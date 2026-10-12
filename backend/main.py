from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

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
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@app.get("/health")
def health():
    return {"status": "ok", "service": "WORKINT"}


@app.post("/api/v1/cv/upload", status_code=201)
async def upload_cv(file: UploadFile = File(...)):
    filename = file.filename or ""

    try:
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=415,
                detail="Solo se permiten archivos PDF",
            )

        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=415,
                detail="Tipo de contenido no permitido",
            )

        header = await file.read(5)

        if header != b"%PDF-":
            raise HTTPException(
                status_code=422,
                detail="El archivo no tiene una cabecera PDF valida",
            )

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

        document_id = uuid4().hex
        destination = UPLOAD_DIR / f"{document_id}.pdf"

        try:
            size = len(header)

            with destination.open("xb") as output:
                output.write(header)

                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)

                    if size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="El PDF supera el limite de 5 MB",
                        )

                    output.write(chunk)

        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return {
            "message": "PDF recibido y almacenado",
            "document_id": document_id,
            "filename": filename,
            "size_bytes": size,
        }

    finally:
        await file.close()

