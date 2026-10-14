import re
from app.services.pdf_extractor import extract_pdf_text, PDFValidationError
from fastapi.middleware.cors import CORSMiddleware
from tempfile import TemporaryFile
from shutil import copyfileobj
from starlette.concurrency import run_in_threadpool

from pydantic import BaseModel, ValidationError, StrictBool
from groq import GroqError
from langchain_core.exceptions import OutputParserException

from app.models.candidate_profile import CandidateProfile
from app.services.profile_extractor import extract_candidate_profile
from app.services.execution_trace import extraction_context, capture_execution

from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.database import get_db
from app.models.entities import Profile, now
from app.repository import save_profile, log
from app.services.documents import (
    directory_lock, document_lock, fingerprint, matching_document, store_document,
)
from app.api.profiles import router as profiles_router

app = FastAPI(
    title="WORKINT API",
    description="Backend del proyecto Profile Manager",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


from app.config import UPLOAD_DIR, MAX_PDF_SIZE
MAX_FILE_SIZE = MAX_PDF_SIZE


@app.get("/health")
def health():
    return {"status": "ok", "service": "WORKINT"}


@app.get("/api/v1/cv/limits")
def cv_limits():
    return {"max_size_bytes": MAX_FILE_SIZE}


@app.post("/api/v1/cv/upload", status_code=201)
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or ""
    try:
        if not filename.lower().endswith(".pdf") or file.content_type != "application/pdf":
            raise HTTPException(415, "Formato no permitido. Solo se aceptan archivos PDF (application/pdf).")
        # El temporal se cierra incluso ante errores/cancelación; aún no existe ID público.
        with TemporaryFile(mode="w+b") as temporary:
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(413, f"El PDF supera el límite configurado de {MAX_FILE_SIZE} bytes.")
                temporary.write(chunk)
            try:
                text = await run_in_threadpool(
                    extract_pdf_text, temporary, max_size_bytes=MAX_FILE_SIZE
                )
            except PDFValidationError as error:
                raise HTTPException(error.status_code, str(error)) from error

            document_id, digest, reused_document = await run_in_threadpool(
                store_document, db, UPLOAD_DIR, temporary, copyfileobj
            )
        existing = db.scalar(select(Profile).where(Profile.document_id == document_id))
        saved_profile = extraction_response(existing, document_id, "reused") if existing else None
        return {
            "message": "PDF validado; disponible para extracción con consentimiento",
            "document_id": document_id,
            "filename": filename,
            "size_bytes": size,
            "status": "ready",
            "processable": True,
            "characters": len(text),
            "sha256": digest,
            "reused_document": reused_document,
            "saved_profile": saved_profile,
        }
    finally:
        await file.close()


@app.post("/api/v1/cv/{document_id}/extract")
def extract_cv(document_id: str):

    if not re.fullmatch(r"[0-9a-f]{32}", document_id):
        raise HTTPException(
            status_code=422,
            detail="Identificador de documento invalido.",
        )

    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"

    try:
        text = extract_pdf_text(pdf_path, max_size_bytes=MAX_FILE_SIZE)

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No se encontro el documento.",
        )

    except PDFValidationError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error),
        )

    return {
        "document_id": document_id,
        "text": text,
        "characters": len(text),
        "status": "extracted",
    }


class ProfileExtractionRequest(BaseModel):
    consent_external_processing: StrictBool = False
    regenerate: StrictBool = False
    expected_updated_at: str | None = None


class ProfileExtractionResponse(BaseModel):
    document_id: str
    profile: CandidateProfile
    status: str = "structured"
    candidate_id: str
    source: str
    updated_at: str


def extraction_response(record, document_id, status):
    return ProfileExtractionResponse(
        document_id=document_id,
        profile=CandidateProfile.model_validate(record.data),
        candidate_id=record.candidate_id,
        source=record.source,
        updated_at=record.updated_at.isoformat(),
        status=status,
    )


@app.post(
    "/api/v1/cv/{document_id}/profile",
    response_model=ProfileExtractionResponse,
)
def generate_candidate_profile(
    document_id: str,
    request: ProfileExtractionRequest,
    db: Session = Depends(get_db),
    execution_context: dict = Depends(extraction_context),
):
    if not re.fullmatch(r"[0-9a-f]{32}", document_id):
        raise HTTPException(
            status_code=422,
            detail="Identificador de documento invalido.",
        )

    if not request.consent_external_processing:
        raise HTTPException(
            status_code=403,
            detail=(
                "Se requiere consentimiento para enviar "
                "el contenido del CV al proveedor de IA."
            ),
        )

    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"

    try:
        text = extract_pdf_text(pdf_path, max_size_bytes=MAX_FILE_SIZE)

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No se encontro el documento.",
        )

    except PDFValidationError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error),
        )

    with pdf_path.open("rb") as stream:
        digest = fingerprint(stream)
    with directory_lock(UPLOAD_DIR):
        canonical_id = matching_document(db, UPLOAD_DIR, digest, preferred_id=document_id)
    # No conservar una lectura antigua ni una transacción mientras esperamos al otro proceso.
    db.rollback()
    with document_lock(UPLOAD_DIR / f"{canonical_id}.pdf"):
        existing = db.scalar(select(Profile).where(Profile.document_id == canonical_id))
        if existing and not request.regenerate:
            log(db, "perfil", "reutilizar", "Perfil guardado mostrado sin nueva llamada al proveedor",
                existing.candidate_id, result_ref=existing.id,
                execution_context={**execution_context, "execution_mode": "reused", "document_id": canonical_id})
            db.commit()
            return extraction_response(existing, document_id, "reused")
        if request.regenerate and (
            existing is None or request.expected_updated_at != existing.updated_at.isoformat()
        ):
            raise HTTPException(409, "El perfil cambió o falta su versión. Muestra el perfil guardado antes de confirmar la regeneración.")
        previous = (existing.id, existing.updated_at) if existing else None
        previous_candidate_id = existing.candidate_id if existing else None
        db.rollback()  # La llamada externa no mantiene una transacción SQLite abierta.
        db.info["operation_id"] = execution_context["operation_id"]
        execution_context["document_id"] = canonical_id
        def extraction_log(status, reason, candidate_id=None, result_ref=None):
            log(db, "perfil", "extraer_cv", reason, candidate_id or previous_candidate_id,
                result_ref=result_ref or canonical_id, status=status,
                execution_context=execution_context)
        try:
            with capture_execution(execution_context):
                profile = extract_candidate_profile(text)
        except RuntimeError:
            extraction_log("error", "Servicio de IA no disponible o sin configurar")
            db.commit()
            raise HTTPException(
                status_code=503,
                detail="El servicio de IA no está disponible o no está configurado. No se generó un nuevo perfil. Puedes reintentar o crear el perfil manualmente.",
            )
        except (GroqError, ValidationError, OutputParserException):
            extraction_log("error", "Fallo del proveedor o respuesta estructurada inválida")
            db.commit()
            raise HTTPException(
                status_code=502,
                detail="El proveedor de IA falló o devolvió un perfil inválido. No se generó un nuevo perfil. Puedes reintentar o crear el perfil manualmente.",
            )
        if previous:
            record_id, version = previous
            result = db.execute(
                update(Profile).where(Profile.id == record_id, Profile.updated_at == version)
                .values(data=profile.model_dump(), source="groq", updated_at=now())
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != 1:
                db.rollback()
                extraction_log("conflict", "Extracción descartada porque el perfil fue editado durante la operación")
                db.commit()
                raise HTTPException(409, "El perfil fue editado durante la regeneración. Se conservaron los cambios guardados; vuelve a consultarlo.")
            db.expire_all()
            record = db.get(Profile, record_id)
            log(db, "perfil", "regenerar", "Regeneración explícita con consentimiento; candidato y relaciones conservados", record.candidate_id, result_ref=record.id)
            status = "regenerated"
        else:
            record = save_profile(db, profile, "groq", canonical_id)
            status = "structured"
        extraction_log("ok", "Perfil validado y guardado" if not previous else "Regeneración explícita validada y guardada", record.candidate_id, record.id)
        db.commit()
        # Responder con los datos persistidos, también si save_profile encontró un vínculo.
        return extraction_response(record, document_id, status)


app.include_router(profiles_router)
from app.api.workflow import router as workflow_router

app.include_router(workflow_router)
