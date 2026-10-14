from datetime import timedelta
from typing import TypedDict
from fastapi import HTTPException
from langgraph.graph import StateGraph, START, END
from sqlalchemy import select
from app.models.entities import Application, Vacancy, Reminder, uid, now
from app.repository import log
from app.services.simulations import current_simulation, require_available

TRANSITIONS = {
    "postulado": ["en_revision", "descartado"],
    "en_revision": ["entrevista", "descartado"],
    "entrevista": ["contratado", "descartado"],
    "contratado": [],
    "descartado": [],
}
STEPS = {
    "postulado": ("Revisar el proceso simulado en 3 días", 3),
    "en_revision": ("Preparar ejemplos de experiencia para una posible entrevista", 2),
    "entrevista": ("Preparar entrevista; la fecha real no está programada", 1),
    "descartado": ("Proceso finalizado; revisar otras vacantes", 0),
    "contratado": ("Proceso simulado terminado con contratación; no requiere seguimiento", 0),
}


class ApplicationState(TypedDict, total=False):
    candidate_id: str
    vacancy_id: str
    confirmed: bool
    simulation_id: str | None
    application: Application


def follow_up(db, application):
    message, days = STEPS[application.status]
    reminder = db.scalar(
        select(Reminder).where(Reminder.application_id == application.id)
    )
    if reminder is None:
        reminder = Reminder(application_id=application.id)
        db.add(reminder)
    reminder.message = message
    reminder.due_at = now() + timedelta(days=days)
    reminder.pending = application.status not in {"descartado", "contratado"}
    log(
        db,
        "seguimiento",
        "proximo_paso",
        (f"Regla de estado {application.status}: revisión en {days} días"
         if reminder.pending else f"Proceso simulado finalizado: {application.status}; recordatorio cerrado"),
        application.candidate_id,
        application.id,
        application.id,
    )
    return {}


def build_application_graph(db):
    def consent(state):
        if state.get("confirmed") is not True:
            raise HTTPException(403, "Confirma explícitamente la postulación simulada")
        return {}

    def apply(state):
        simulation = current_simulation(db)
        if state.get("simulation_id") and state["simulation_id"] != simulation.id:
            raise HTTPException(409, "La simulación cambió. Actualiza antes de postular")
        require_available(db, state["vacancy_id"], simulation.id)
        duplicate = db.scalar(
            select(Application).where(
                Application.candidate_id == state["candidate_id"],
                Application.vacancy_id == state["vacancy_id"],
                Application.simulation_id == simulation.id,
            )
        )
        if duplicate:
            raise HTTPException(409, "Ya existe una postulación para esta vacante")
        operation, date = uid(), now()
        app = Application(
            id=operation,
            candidate_id=state["candidate_id"],
            vacancy_id=state["vacancy_id"],
            created_at=date,
            status="postulado",
            simulation_id=simulation.id,
            evidence=dict(
                operation_id=operation,
                candidate_id=state["candidate_id"],
                vacancy_id=state["vacancy_id"],
                date=date.isoformat(),
                type="simulada",
                result="registrada_localmente",
                confirmed=True,
                simulation_id=simulation.id,
            ),
        )
        db.add(app)
        db.flush()
        log(
            db,
            "postulacion",
            "postulado",
            "Confirmación explícita; simulación local sin envío externo",
            app.candidate_id,
            app.id,
            app.id,
        )
        return {"application": app}

    graph = StateGraph(ApplicationState)
    graph.add_node("consentimiento", consent)
    graph.add_node("simular", apply)
    graph.add_node("seguimiento", lambda state: follow_up(db, state["application"]))
    graph.add_edge(START, "consentimiento")
    graph.add_edge("consentimiento", "simular")
    graph.add_edge("simular", "seguimiento")
    graph.add_edge("seguimiento", END)
    return graph.compile()


def application_view(db, app):
    is_current = app.simulation_id == current_simulation(db).id
    return dict(
        id=app.id,
        candidate_id=app.candidate_id,
        vacancy_id=app.vacancy_id,
        status=app.status,
        simulation_id=app.simulation_id,
        is_current=is_current,
        hired_at=app.hired_at,
        created_at=app.created_at,
        evidence=app.evidence,
        vacancy=db.get(Vacancy, app.vacancy_id).data,
        next_step=STEPS[app.status][0],
        allowed_transitions=TRANSITIONS[app.status] if is_current else [],
    )


def change_status(db, app, status):
    if app.simulation_id != current_simulation(db).id:
        raise HTTPException(409, "La postulación pertenece a una simulación anterior; su historial se conserva")
    if status not in TRANSITIONS[app.status]:
        raise HTTPException(409, "Transición de estado no permitida")
    previous = app.status
    if status == "contratado":
        require_available(db, app.vacancy_id, app.simulation_id)
        app.hired_at = now()
    app.status = status
    log(
        db,
        "postulacion",
        "cambio_estado",
        f"Cambio manual de demostración: {previous} → {status}",
        app.candidate_id,
        app.id,
        app.id,
    )
    # El flujo de seguimiento ejecuta la misma regla en creación y actualización.
    graph = StateGraph(ApplicationState)
    graph.add_node("seguimiento", lambda state: follow_up(db, state["application"]))
    graph.add_edge(START, "seguimiento")
    graph.add_edge("seguimiento", END)
    graph.compile().invoke({"application": app})
