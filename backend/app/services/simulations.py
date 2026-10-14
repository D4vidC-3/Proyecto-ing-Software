"""Simulaciones locales: decisiones de disponibilidad bajo transacción SQLite."""
from fastapi import HTTPException
from sqlalchemy import select, text
from app.models.entities import Application, Profile, Simulation, Vacancy
from app.repository import log


def begin_write(db):
    # Serializa contratar, postular e iniciar simulación incluso entre procesos.
    # Debe llamarse antes de leer/modificar objetos en estos endpoints.
    db.execute(text("BEGIN IMMEDIATE"))


def current_simulation(db):
    return db.scalar(select(Simulation).where(Simulation.active.is_(True)))


def require_available(db, vacancy_id, simulation_id):
    occupied = db.scalar(select(Application.id).where(
        Application.simulation_id == simulation_id,
        Application.vacancy_id == vacancy_id,
        Application.status == "contratado",
    ))
    if occupied:
        raise HTTPException(409, "La vacante está ocupada en esta simulación")


def simulation_view(db):
    current = current_simulation(db)
    hires = []
    occupied = set()
    for app, profile, vacancy in db.execute(
        select(Application, Profile, Vacancy)
        .join(Profile, Profile.candidate_id == Application.candidate_id)
        .join(Vacancy, Vacancy.id == Application.vacancy_id)
        .where(Application.status == "contratado")
        .order_by(Application.created_at, Application.id)
    ):
        if app.simulation_id == current.id:
            occupied.add(app.vacancy_id)
        hires.append(dict(application_id=app.id, candidate_id=app.candidate_id,
                          candidate_name=profile.data.get("name"), vacancy_id=app.vacancy_id,
                          vacancy_title=vacancy.data["title"], hired_at=app.hired_at,
                          simulation_id=app.simulation_id))
    return dict(current_id=current.id, occupied_vacancy_ids=sorted(occupied), hires=hires,
                simulations=[dict(id=s.id, created_at=s.created_at, active=s.active)
                             for s in db.scalars(select(Simulation).order_by(Simulation.created_at))])


def start_simulation(db, confirmed, expected_current_id):
    if confirmed is not True:
        raise HTTPException(403, "Confirma explícitamente el inicio de una nueva simulación")
    previous = current_simulation(db)
    if previous.id != expected_current_id:
        raise HTTPException(409, "La simulación cambió. Actualiza antes de confirmar otra")
    previous.active = False
    db.flush()
    simulation = Simulation()
    db.add(simulation)
    db.flush()
    log(db, "simulacion", "iniciar", "Nueva simulación confirmada; historial anterior conservado", result_ref=simulation.id)
    return simulation
