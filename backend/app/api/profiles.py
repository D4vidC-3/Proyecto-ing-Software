from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.contracts import Id, ProfileView
from app.models.entities import Profile, Candidate
from app.repository import save_profile, profile_view, log

router = APIRouter(prefix="/api/v1/profiles", tags=["perfiles"])


def require_profile(db, candidate_id):
    record = db.scalar(select(Profile).where(Profile.candidate_id == candidate_id))
    if record is None:
        raise HTTPException(404, "Perfil no encontrado")
    return record


@router.post("", response_model=ProfileView, status_code=201)
def create(profile: CandidateProfile, db: Session = Depends(get_db)):
    record = save_profile(db, profile, "manual")
    db.commit()
    return profile_view(record)


@router.get("", response_model=list[ProfileView])
def list_profiles(db: Session = Depends(get_db)):
    return [
        profile_view(p)
        for p in db.scalars(select(Profile).order_by(Profile.updated_at.desc()))
    ]


@router.get("/{candidate_id}", response_model=ProfileView)
def read(candidate_id: Id, db: Session = Depends(get_db)):
    return profile_view(require_profile(db, candidate_id))


@router.put("/{candidate_id}", response_model=ProfileView)
def update(candidate_id: Id, profile: CandidateProfile, db: Session = Depends(get_db)):
    record = require_profile(db, candidate_id)
    record.data = profile.model_dump()
    record.source = "groq_editado" if record.source.startswith("groq") else "manual"
    log(
        db,
        "perfil",
        "editar",
        "Corrección manual guardada; faltantes recalculados",
        candidate_id,
        result_ref=record.id,
    )
    db.commit()
    return profile_view(record)


@router.delete("/{candidate_id}", status_code=204)
def delete(candidate_id: Id, db: Session = Depends(get_db)):
    require_profile(db, candidate_id)
    db.delete(db.get(Candidate, candidate_id))
    db.commit()
    return Response(status_code=204)
