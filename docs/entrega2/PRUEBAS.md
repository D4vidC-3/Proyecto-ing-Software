# Pruebas y evidencias

Fecha: 12 de octubre de 2026. Línea base: **26 aprobadas**. Suite final: **47 ejecutadas, 47 aprobadas, 0 fallidas**, incluidas las 26 originales. Resultado exacto en `evidencias/pytest.txt`.

## Automatización

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q app main.py tests
cd ../frontend
npx tsc --noEmit
npm run lint
npm run build
```

| Cobertura | Evidencia |
|---|---|
| PDF, extracción local, consentimiento, errores de proveedor, Pydantic | Las 26 pruebas originales, sin eliminarlas ni cambiar sus asserts |
| Migración y CRUD de perfil, conexión nueva, faltantes opcionales/desconocidos | test_persistence.py (4 pruebas) |
| Importación idempotente, fuente ausente/corrupta/inválida | test_ingestion_idempotent_and_source_atomic |
| Normalización y salario desconocido | test_normalization_and_missing_vacancy_data |
| Desglose de scoring exacto, parcial, incompatible y desconocido | test_scoring_exact_and_unknown, test_scoring_incompatible_and_unknown_salary |
| Orden del ranking y trazas reales | test_ranking_and_persisted_trace |
| Confirmación estricta | test_requires_strict_confirmation (4 casos) |
| Duplicados, transiciones, evidencia estable, cierre y cascadas | test_application_lifecycle_evidence_and_cascade |
| Recordatorio, errores de ID/estado | test_reminder_and_errors |
| CORS de PUT/PATCH/DELETE y origen rechazado | test_cors_for_update_delete |
| Alembic upgrade/downgrade/upgrade | test_migration_down_up |
| Reintento del CV preserva edición | test_extraction_retry_preserves_edits |
| Proveedor indisponible y entrada manual | test_failed_provider_manual_fallback |
| Flujo PDF → grafo real con LLM falso → BD → ranking → simulación → seguimiento | test_integrated_pdf_graph_to_followup |
| Respuesta estructurada inválida | test_invalid_provider_output_is_controlled |

Cada test usa SQLite temporal **en disco creada con Alembic**. Se elimina la clave Groq del entorno de las pruebas y se inyectan modelos/mocks. Ninguna prueba automatizada consume llamadas reales. No se afirma cobertura porcentual ni se equipara el mock con verificación del proveedor.

## Comprobación manual con navegador

1. Crear `Sofía Demo UI` desde formulario; guardar. Aparecen educación y disponibilidad como faltantes opcionales.
2. Consultar 18 ofertas; la primera muestra 100 puntos con desglose 45/20/15/10/10 para el perfil creado.
3. Abrir vista previa; Confirmar está deshabilitado hasta marcar la casilla. Cancelar no crea postulación. Confirmar sí crea estado postulado, evidencia y recordatorio.
4. Cambiar a en_revision. El historial muestra transición manual y regla de seguimiento. La evidencia inicial permanece.
5. Seleccionar el PDF ficticio facilitado y cargarlo desde Next.js. Se muestra el nombre y tamaño (71.464 bytes).
6. Marcar consentimiento de procesamiento externo y generar perfil. **Llamada real a Groq exitosa**, separada de Pytest. Origen inicial groq; experiencia, educación, habilidades y preferencias visibles. Esta observación no garantiza disponibilidad futura del proveedor.
7. Guardar corrección de disponibilidad: `Disponible en 20 días (corrección de prueba)`. Se verifica persistencia y origen groq_editado. Completar postulación del perfil extraído hasta evidencia y seguimiento.
8. Crear un perfil mínimo desechable. La interfaz indica nueve campos desconocidos. Eliminarlo mediante confirmación: desaparece del selector, y los otros perfiles permanecen.
9. Reiniciar el proceso Uvicorn de prueba. Lectura por HTTP confirma perfiles, vacantes, estado y evidencia. Ver `evidencias/reinicio.json`.

Capturas reales, sin recreación: `seguimiento.png`, `confirmacion.png`, `recorrido_groq.png`. Contienen solo datos ficticios. Los IDs son los producidos por esta ejecución y no se usan como fixtures del código.

## Incidencias y correcciones

- TestClient no avanzaba dentro del aislamiento de herramientas. Al ejecutarse con permiso fuera de él, la línea base pasó.
- Las primeras pruebas nuevas usaban la misma carpeta temporal para DB y archivos, rompiendo tres asserts originales de carpeta vacía. Se separó la preparación; las pruebas anteriores se conservaron.
- El build inicial requería descargar fuentes de Google. Se eliminó esa dependencia visual.
- Turbopack requiere puertos temporales: un intento aislado falló y dejó caché. Tras limpiar `.next` y compilar fuera del aislamiento, pasó.
- La prueba UI encontró una carrera al leer trazas en paralelo con el cálculo del ranking. Se lee la actividad después de completar el cálculo.
- Un intento de edición UI fue rechazado temporalmente por el revisor automático con HTTP 429. Se verificó el contexto local y ficticio; el reintento de la misma acción autorizada funcionó posteriormente.
- En la consolidación final hacia `WORKINT`, se ajustó `websockets==16.1.1` en `backend/requirements.txt` (en lugar de `17.2`) para alinear la versión instalada en `.venv` con la restricción de `langgraph-sdk` y evitar backtracking (`resolution-too-deep`) al ejecutar `pip install -r requirements.txt -r requirements-dev.txt`.

## Límites de verificación

No se midió cobertura porcentual, carga concurrente, accesibilidad exhaustiva, compatibilidad móvil completa, producción ni PostgreSQL. No hay E2E de navegador incorporado a CI; los pasos manuales son reproducibles en DEMO.md. La aceptación académica, revisión de otro integrante y evidencias Scrum siguen pendientes del equipo.
