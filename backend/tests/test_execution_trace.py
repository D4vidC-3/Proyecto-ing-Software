from io import BytesIO
from unittest.mock import Mock
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session
import main
from app.models.candidate_profile import CandidateProfile
from app.models.entities import AgentLog
from app.services.execution_trace import extraction_context, capture_execution, provider_metadata
from app.services.profile_extractor import extract_candidate_profile, TracedChatGroq
from test_profile_extractor import FakeModel

client = TestClient(main.app)


def upload():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(40, 700, "Contenido privado de prueba que nunca se registra")
    pdf.save()
    return client.post("/api/v1/cv/upload", files={"file": ("cv.pdf", buffer.getvalue(), "application/pdf")}).json()["document_id"]


def test_injected_model_explicitly_simulated():
    context = extraction_context()
    with capture_execution(context):
        extract_candidate_profile("Texto privado", llm=FakeModel({"skills": ["Python"]}))
    assert context["execution_mode"] == "simulated"
    assert context["effective_model"] is None
    assert context["provider_request_id"] is None
    assert "Texto privado" not in str(context)


def test_original_response_metadata_without_configured_model_fallback():
    context = {**extraction_context(), "execution_mode": "real", "configured_model": "configured"}
    with capture_execution(context):
        provider_metadata({"model": "actual", "id": "completion-1", "x_groq": {"id": "request-1"}, "choices": [{"message": "private"}]})
    assert context["effective_model"] == "actual"
    assert context["provider_request_id"] == "request-1"
    assert "private" not in str(context)
    with capture_execution(context):
        provider_metadata({"id": "completion-2"})
    assert context["effective_model"] is None
    assert context["provider_request_id"] is None
    # Adaptador probado sin construir cliente ni invocar transporte.
    model = TracedChatGroq.model_construct(model_name="configured", service_tier=None, reasoning_effort=None)
    with capture_execution(context):
        model._create_chat_result(
            {"model": "actual", "id": "completion-3", "choices": [{"message": {"role": "assistant", "content": "{}"}, "finish_reason": "stop"}]}, {},
        )
    assert context["effective_model"] == "actual"
    assert context["completion_id"] == "completion-3"


def test_mocked_api_trace_and_reuse(database, monkeypatch):
    fake = Mock(return_value=CandidateProfile(skills=["Python"]))
    monkeypatch.setattr(main, "extract_candidate_profile", fake)
    doc = upload()
    path = f"/api/v1/cv/{doc}/profile"
    response = client.post(path, json={"consent_external_processing": True})
    assert response.status_code == 200
    cid = response.json()["candidate_id"]
    logs = client.get(f"/api/v1/profiles/{cid}/activity").json()
    trace = next(l for l in logs if l["action"] == "extraer_cv")
    assert trace["execution_context"]["execution_mode"] == "simulated"
    assert trace["execution_context"]["effective_model"] is None
    assert trace["operation_id"]
    assert len({l["operation_id"] for l in logs}) == 1
    assert "Contenido privado" not in str(logs)
    assert client.post(path, json={"consent_external_processing": True}).status_code == 200
    assert fake.call_count == 1
    logs = client.get(f"/api/v1/profiles/{cid}/activity").json()
    assert next(l for l in logs if l["action"] == "reutilizar")["execution_context"]["execution_mode"] == "reused"


def test_provider_error_recorded_without_payload(database, monkeypatch):
    monkeypatch.setattr(main, "extract_candidate_profile", Mock(side_effect=RuntimeError("Secret text should never be logged")))
    doc = upload()
    assert client.post(f"/api/v1/cv/{doc}/profile", json={"consent_external_processing": True}).status_code == 503
    with Session(database) as db:
        trace = db.scalar(select(AgentLog).where(AgentLog.action == "extraer_cv"))
        assert trace.status == "error" and trace.execution_context["execution_mode"] == "simulated"
        assert "Secret" not in trace.reason
