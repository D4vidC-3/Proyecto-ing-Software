"""Contexto por operación; nunca guarda prompts, CV, respuestas completas ni secretos."""
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

execution = ContextVar("workint_execution", default=None)


def extraction_context():
    # Dependencia explícita: las pruebas que sustituyen el extractor declaran
    # su contexto simulado. Un extractor sustituido sin contexto queda desconocido.
    return {"execution_mode": "unknown", "provider": None, "configured_model": None,
            "effective_model": None, "provider_request_id": None, "completion_id": None,
            "metadata_status": "unavailable", "operation_id": uuid4().hex}


@contextmanager
def capture_execution(context):
    token = execution.set(context)
    try:
        yield context
    finally:
        execution.reset(token)


def provider_metadata(response):
    context = execution.get()
    if context is None or context["execution_mode"] != "real":
        return
    data = response if isinstance(response, dict) else response.model_dump()
    # Solo campos de la respuesta original. No usar model_name de LangChain:
    # la versión instalada lo sustituye por el modelo configurado.
    context["effective_model"] = data.get("model")
    context["provider_request_id"] = getattr(response, "_request_id", None) or (data.get("x_groq") or {}).get("id")
    context["completion_id"] = data.get("id")
    context["metadata_status"] = "provider_response" if context["effective_model"] else "model_unavailable"
