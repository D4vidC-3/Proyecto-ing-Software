"""Consultas y escrituras; las transacciones se confirman en el límite HTTP/CLI."""

from sqlalchemy import select
from app.models.entities import Candidate, Profile, AgentLog, uid
from app.models.candidate_profile import CandidateProfile
from app.services.profile_gaps import profile_gaps


def log(
    db,
    agent,
    action,
    reason,
    candidate_id=None,
    application_id=None,
    result_ref=None,
    status="ok",
    execution_context=None,
):
    context = execution_context or {"execution_mode": "rules", "metadata_status": "not_applicable"}
    db.add(
        AgentLog(
            agent=agent,
            action=action,
            reason=reason,
            candidate_id=candidate_id,
            application_id=application_id,
            result_ref=result_ref,
            status=status,
            operation_id=context.get("operation_id") or db.info.setdefault("operation_id", uid()),
            execution_context=dict(context),
        )
    )


def save_profile(db, profile, source, document_id=None):
    existing = (
        db.scalar(select(Profile).where(Profile.document_id == document_id))
        if document_id
        else None
    )
    if existing:
        return existing  # Reintentos no sobrescriben correcciones del candidato.
    candidate = Candidate()
    db.add(candidate)
    db.flush()
    record = Profile(
        candidate_id=candidate.id,
        data=profile.model_dump(),
        source=source,
        document_id=document_id,
    )
    db.add(record)
    db.flush()
    log(
        db,
        "perfil",
        "crear",
        (
            "Extracción con consentimiento"
            if source == "groq"
            else "Entrada manual declarada por el candidato"
        ),
        candidate.id,
        result_ref=record.id,
    )
    return record


def profile_view(record):
    p = CandidateProfile.model_validate(record.data)
    return dict(
        id=record.id,
        candidate_id=record.candidate_id,
        document_id=record.document_id,
        source=record.source,
        updated_at=record.updated_at,
        profile=p,
        gaps=profile_gaps(p),
    )
