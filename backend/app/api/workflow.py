from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.profiles import require_profile
from app.models.contracts import (
    Id,
    VacancyId,
    VacancyData,
    ApplicationRequest,
    ApplicationView,
    StatusRequest,
    LogView,
    ReminderView,
    RecommendationView,
    SimulationRequest,
)
from app.models.entities import Vacancy, Application, AgentLog, Reminder
from app.services.vacancies import recommend
from app.services.simulations import begin_write, current_simulation, simulation_view, start_simulation
from app.services.applications import (
    build_application_graph,
    application_view,
    change_status,
)

router = APIRouter(prefix="/api/v1", tags=["recorrido"])


@router.get("/vacancies", response_model=list[VacancyData])
def vacancies(db: Session = Depends(get_db)):
    return [v.data for v in db.scalars(select(Vacancy).order_by(Vacancy.id))]


@router.get("/vacancies/{vacancy_id}", response_model=VacancyData)
def vacancy(vacancy_id: VacancyId, db: Session = Depends(get_db)):
    row = db.get(Vacancy, vacancy_id)
    if row is None:
        raise HTTPException(404, "Vacante no encontrada")
    return row.data


@router.get(
    "/profiles/{candidate_id}/recommendations", response_model=list[RecommendationView]
)
def recommendations(candidate_id: Id, db: Session = Depends(get_db)):
    results = recommend(db, require_profile(db, candidate_id))
    db.commit()
    return results


@router.post("/applications", response_model=ApplicationView, status_code=201)
def apply(request: ApplicationRequest, db: Session = Depends(get_db)):
    begin_write(db)
    require_profile(db, request.candidate_id)
    vacancy(request.vacancy_id, db)
    try:
        result = build_application_graph(db).invoke(request.model_dump())
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe una postulación para esta vacante")
    return application_view(db, result["application"])


@router.get(
    "/profiles/{candidate_id}/applications", response_model=list[ApplicationView]
)
def applications(candidate_id: Id, db: Session = Depends(get_db)):
    require_profile(db, candidate_id)
    return [
        application_view(db, a)
        for a in db.scalars(
            select(Application)
            .where(Application.candidate_id == candidate_id)
            .order_by(Application.created_at.desc())
        )
    ]


@router.patch("/applications/{application_id}", response_model=ApplicationView)
def update_status(
    application_id: Id, request: StatusRequest, db: Session = Depends(get_db)
):
    begin_write(db)
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(404, "Postulación no encontrada")
    change_status(db, app, request.status)
    db.commit()
    return application_view(db, app)


@router.get("/profiles/{candidate_id}/activity", response_model=list[LogView])
def activity(candidate_id: Id, db: Session = Depends(get_db)):
    require_profile(db, candidate_id)
    return list(
        db.scalars(
            select(AgentLog)
            .where(AgentLog.candidate_id == candidate_id)
            .order_by(AgentLog.created_at, AgentLog.id)
        )
    )


@router.get("/profiles/{candidate_id}/reminders", response_model=list[ReminderView])
def reminders(candidate_id: Id, db: Session = Depends(get_db)):
    require_profile(db, candidate_id)
    return list(
        db.scalars(
            select(Reminder)
            .join(Application)
            .where(Application.candidate_id == candidate_id)
            .where(Application.simulation_id == current_simulation(db).id)
            .order_by(Reminder.due_at)
        )
    )


@router.get("/simulations")
def simulations(db: Session = Depends(get_db)):
    return simulation_view(db)


@router.post("/simulations", status_code=201)
def new_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
    begin_write(db)
    start_simulation(db, request.confirmed, request.expected_current_id)
    db.commit()
    return simulation_view(db)
