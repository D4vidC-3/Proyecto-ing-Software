# Estado inicial verificado

Auditoría del 12 de octubre de 2026. Fuente principal: repositorio local, rama `desarrollo/entrega-2`, HEAD `80b347b` (HU01 FastAPI Next.js). Commits anteriores: `808eb47`, `a1a895b`, `726b71e`.

Se compararon `~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software` (que conservaba el avance parcial inicial con 26 pruebas) y `~/Documentos/ChatGPT/WORKIN1/Proyecto-ing-Software` (donde se completó el MVP con 47 pruebas, persistencia y documentación). Tras respaldar y comparar archivo por archivo, todos los cambios validados se sincronizaron selectivamente hacia la ruta principal `~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software`. No se ejecutaron reset, rebase, merge ni push.

## Trabajo previo conservado

Modificados inicialmente: `backend/main.py`, `backend/requirements.txt`, `backend/requirements-dev.txt`, `frontend/src/app/page.tsx`. Sin seguimiento: `backend/app/` y las pruebas `test_candidate_profile.py`, `test_extract_api.py`, `test_pdf_extractor.py`, `test_profile_api.py`, `test_profile_extractor.py`. El archivo preexistente `app/services/__init__.pyC` se conservó sin cambiarlo.

| Funcionalidad | Historia | Estado inicial | Evidencia inicial | Trabajo pendiente inicial |
|---|---|---|---|---|
| Carga PDF hasta 5 MB | HU01 | Implementada | API, Next.js, test_upload | Integrar recorrido |
| Extraer texto | HU02 | Implementada | pypdf, máximo 10 páginas/20.000 caracteres, tests | Guardar perfil |
| Perfil estructurado | HU02 | Implementada con proveedor | Grafo extract → validate, ChatGroq, json_schema, UI, mocks | Persistencia y comprobación real de esta entrega |
| Faltantes, edición, preferencias | HU03–05 | Parcial | Pydantic y visualización de datos | CRUD, formulario, detección |
| Vacantes y matching | HU06–11 | TODO | Sin código | Dataset y servicios |
| Postulación e historial | HU12–15, HU18 | TODO | Sin código | Grafo y persistencia |
| Seguimiento y trazabilidad | HU16–17, HU19–20 | TODO | Sin código | Reglas y panel |
| Protección | HU-NF01 | Parcial | Consentimiento, .gitignore, validación PDF, CORS | Sin autenticación ni aislamiento |
| Errores | HU-NF02 | Parcial | Errores HTTP de carga/proveedor | Cobertura ampliada y logging |

Endpoints originales preservados: `GET /health`, `POST /api/v1/cv/upload`, `POST /api/v1/cv/{document_id}/extract`, `POST /api/v1/cv/{document_id}/profile`. La respuesta del último se amplió con `candidate_id` y `source`.

## Línea base ejecutada antes de las nuevas funcionalidades

- Pytest: **26 aprobadas**. El aislamiento de herramientas bloqueaba TestClient; fuera de ese aislamiento pasaron sin cambiar las pruebas.
- TypeScript: aprobado.
- ESLint: aprobado.
- Build inicial: falló por descarga de Geist/Geist Mono desde Google. Se sustituyeron por tipografía del sistema.
- SQLAlchemy y Alembic no estaban instalados. LangGraph y langchain-groq estaban instalados pero faltaban en requirements; ahora se declaran.
- Sin base relacional ni migraciones previas.

## Backlog y plantillas

Se consultaron las 22 issues de GitHub (20 funcionales, 2 no funcionales). Sus cuerpos y URLs quedan en `evidencias/backlog_github.json`. No se encontraron puntos del equipo en ellas. Las casillas de tareas del repositorio remoto no se modificaron y no constituyen evidencia de terminación técnica.

Se leyeron las plantillas originales de Descargas. El Excel contiene Features, Analysis, Cone of Uncertainty, Assumtions, Definition of Done y Team Shape, entre otras hojas auxiliares. Los ejemplos de login, citas y calificación corresponden a una plantilla genérica, no a estimaciones de WORKINT. No se reutilizaron sus puntos ni su velocidad.

La plantilla Word solicita retrospectiva, planificación, arquitectura, diagramas, demo, capturas y conclusiones. Se prepara contenido técnico verificable en esta carpeta; el equipo debe completar las evidencias de ceremonias y aceptación. Los archivos originales no se modificaron.
