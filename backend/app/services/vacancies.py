import json
from pathlib import Path
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from sqlalchemy import select
from pydantic import TypeAdapter
from app.models.contracts import VacancyData
from app.models.entities import Vacancy
from app.models.candidate_profile import CandidateProfile
from app.repository import log
from app.services.matching import score

DATASET = Path(__file__).resolve().parents[1] / "data" / "vacancies.json"


class VacancyState(TypedDict, total=False):
    records: list[dict]
    normalized: list[dict]
    profile: CandidateProfile
    recommendations: list[dict]


def normalize_records(state):
    validated = TypeAdapter(list[VacancyData]).validate_python(state["records"])
    if len({v.id for v in validated}) != len(validated):
        raise ValueError("IDs duplicados en el dataset")
    return {"normalized": [v.model_dump() for v in validated]}


def rank(state):
    return {
        "recommendations": sorted(
            [score(state["profile"], v) for v in state["normalized"]],
            key=lambda r: (-r["score"], r["vacancy"]["id"]),
        )
    }


def build_vacancy_graph():
    graph = StateGraph(VacancyState)
    graph.add_node("normalizar", normalize_records)
    graph.add_node("matching", rank)
    graph.add_edge(START, "normalizar")
    graph.add_edge("normalizar", "matching")
    graph.add_edge("matching", END)
    return graph.compile()


vacancy_graph = build_vacancy_graph()


def ingest(db, path=DATASET):
    from app.config import check_database

    print(f"Ingesta - base efectiva: {check_database(db.get_bind().url.render_as_string(hide_password=False))}", flush=True)
    # Validar todo antes de escribir: una fuente corrupta no deja media importación.
    records = normalize_records({"records": json.loads(Path(path).read_text())})[
        "normalized"
    ]
    if Path(db.get_bind().url.database or "").name == "workint_escenarios.db":
        expected = {f"escenarios-v{i:02d}" for i in range(1, 11)}
        existing = set(db.scalars(select(Vacancy.id)))
        if {r["id"] for r in records} != expected or not existing <= expected:
            raise ValueError("La base de escenarios admite exclusivamente sus 10 vacantes; no se mezclan datasets")
    for record in records:
        row = db.get(Vacancy, record["id"])
        if row is None:
            db.add(Vacancy(id=record["id"], data=record))
        else:
            row.data = record
    log(
        db,
        "vacantes",
        "ingesta",
        "Dataset ficticio validado; actualización idempotente por ID",
        result_ref=f"demo:{len(records)}",
    )
    db.flush()
    return len(records)


def recommend(db, profile_record):
    result = vacancy_graph.invoke(
        {
            "records": [v.data for v in db.scalars(select(Vacancy))],
            "profile": CandidateProfile.model_validate(profile_record.data),
        }
    )
    log(
        db,
        "vacantes",
        "recomendar",
        "Pesos fijos 45/20/15/10/10; desconocidos aportan cero",
        profile_record.candidate_id,
        result_ref=f'ranking:{len(result["recommendations"])}',
    )
    return result["recommendations"]


if __name__ == "__main__":
    from sqlalchemy.orm import Session
    from app.database import engine
    from app.config import VACANCIES_PATH

    with Session(engine) as db:
        count = ingest(db, VACANCIES_PATH)
        db.commit()
        print(f"{count} vacantes demo importadas")
