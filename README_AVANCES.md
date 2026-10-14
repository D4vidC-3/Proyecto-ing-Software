# Avances para Entrega 2 — 2026-10-13

## Objetivo y límites
Corregir guardado de perfiles, presentación de vacantes, disponibilidad por simulación y trazabilidad. Reutilizar los flujos LangGraph actuales: no son agentes autónomos. Sin nuevos modelos, OCR, integraciones, autenticación, filtros ni vinculación de versiones de CV. Sin llamadas reales a Groq ni recorridos de navegador. Preservar cambios previos, ambas bases, perfiles y documentos; no reseedear ni borrar historial. No modificar Word/Excel.

## Estado inicial
- Revisadas las instrucciones de `frontend/AGENTS.md` y los archivos de estos flujos.
- El backend ya valida mínimo salarial <= máximo y conserva teléfonos como texto. Se reutilizarán esas reglas.
- Hay numerosos cambios previos del usuario: se conservan.
- Bloques pendientes: (1) guardado/vista de lectura, (2) presentación, (3) simulaciones/migración, (4) trazabilidad.
- Verificaciones de esta sesión: lectura de código únicamente; todavía no se ejecutaron pruebas.

## Continuación
Proyecto: `/home/r347/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software`.
Próximo paso: implementar el bloque 1 y sus pruebas enfocadas. Después completar los bloques 2–4, actualizar este archivo en cada cierre y ejecutar una vez los controles finales.

Comandos de controles finales (desde sus carpetas):
```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q app main.py
cd ../frontend
node --experimental-strip-types --test tests/*.test.mjs
npx tsc --noEmit
npm run lint
npm run build
```

Las evidencias históricas de `docs/` no son resultados de esta versión. No se han modificado bases ni aplicado migraciones en esta sesión.

## Bloque 1 — implementado
- Vista de lectura reutilizando los campos actuales; acciones Editar/Cancelar. Guardado separado de la consulta de recomendaciones, estados visibles y borrador conservado ante errores. Bloqueo de doble envío del formulario.
- Validación salarial frontend; se conserva el validador backend existente. Teléfono como texto con `type=tel`, admite prefijo internacional sin verificación externa.
- Archivos: `frontend/src/app/dashboard.tsx`, `profile-validation.ts`, `frontend/tests/profile-validation.test.mjs`, `backend/tests/test_profile_save.py`.
- Prueba frontend enfocada: aprobada (1). Prueba API enfocada: aprobada (1, 0.79 s). El primer proceso de pytest en sandAvances para Entrega 2 — 2026-10-13

## Objetivo y límites
Corregir guardado de perfiles, presentación de vacantes, disponibilidad por simulación y trazabilidad. Reutilizar los flujos LangGraph actuales: no son agentes autónomos. Sin nuevos modelos, OCR, integraciones, autenticación, filtros ni vinculación de versiones de CV. Sin llamadas reales a Groq ni recorridos de navegador. Preservar cambios previos, ambas bases, perfiles y documentos; no reseedear ni borrar historial. No modificar Word/Excel.

## Estado inicial
- Revisadas las instrucciones de `frontend/AGENTS.md` y los archivos de estos flujos.
- El backend ya valida mínimo salarial <= máximo y conserva teléfonos como texto. Se reutilizarán esas reglas.
- Hay numerosos cambios previos del usuario: se conservan.
- Bloques pendientes: (1) guardado/vista de lectura, (2) presentación, (3) simulaciones/migración, (4) trazabilidad.
- Verificaciones de esta sesión: lectura de código únicamente; todavía no se ejecutaron pruebas.

## Continuación
Proyecto: `/home/r347/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software`.
Próximo paso: implementar el bloque 1 y sus pruebas enfocadas. Después completar los bloques 2–4, actualizar este archivo en cada cierre y ejecutar una vez los controles finales.

Comandos de controles finales (desde sus carpetas):
￼￼
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q app main.py
cd ../frontend
node --experimental-strip-types --test tests/*.test.mjs
npx tsc --noEmit
npm run lint
npm run build
￼￼

Las evidencias históricas de `docs/` no son resultados de esta versión. No se han modificado bases ni aplicado migraciones en esta sesión.

## Bloque 1 — implementado
- Vista de lectura reutilizando los campos actuales; acciones Editar/Cancelar. Guardado separado de la consulta de recomendaciones, estados visibles y borrador conservado ante errores. Bloqueo de doble envío del formulario.
- Validación salarial frontend; se conserva el validador backend existente. Teléfono como texto con `type=tel`, admite prefijo internacional sin verificación externa.
- Archivos: `frontend/src/app/dashboard.tsx`, `profile-validation.ts`, `frontend/tests/profile-validation.test.mjs`, `backend/tests/test_profile_sAvances para Entrega 2 — 2026-10-13

## Objetivo y límites
Corregir guardado de perfiles, presentación de vacantes, disponibilidad por simulación y trazabilidad. Reutilizar los flujos LangGraph actuales: no son agentes autónomos. Sin nuevos modelos, OCR, integraciones, autenticación, filtros ni vinculación de versiones de CV. Sin llamadas reales a Groq ni recorridos de navegador. Preservar cambios previos, ambas bases, perfiles y documentos; no reseedear ni borrar historial. No modificar Word/Excel.

## Estado inicial
- Revisadas las instrucciones de `frontend/AGENTS.md` y los archivos de estos flujos.
- El backend ya valida mínimo salarial <= máximo y conserva teléfonos como texto. Se reutilizarán esas reglas.
- Hay numerosos cambios previos del usuario: se conservan.
- Bloques pendientes: (1) guardado/vista de lectura, (2) presentación, (3) simulaciones/migración, (4) trazabilidad.
- Verificaciones de esta sesión: lectura de código únicamente; todavía no se ejecutaron pruebas.

## Continuación
Proyecto: `/home/r347/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software`.
Próximo paso: implementar el bloque 1 y sus pruebas enfocadas. Después completar los bloques 2–4, actualizar este archivo en cada cierre y ejecutar una vez los controles finales.

Comandos de controles finales (desde sus carpetas):
￼￼
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q app main.py
cd ../frontend
node --experimental-strip-types --test tests/*.test.mjs
npx tsc --noEmit
npm run lint
npm run build
￼￼

Las evidencias históricas de `docs/` no son resultados de esta versión. No se han modificado bases ni aplicado migraciones en esta sesión.

## Bloque 1 — implementado
- Vista de lectura reutilizando los campos actuales; acciones Editar/Cancelar. Guardado separado de la consulta de recomendaciones, estados visibles y borrador conservado ante errores. Bloqueo de doble envío del formulario.
- Validación salarial frontend; se conserva el validador backend existente. Teléfono como texto con `type=tel`, admite prefijo internacional sin verificación externa.
- Archivos: `frontend/src/app/dashboard.tsx`, `profile-validation.ts`, `frontend/tests/profile-validation.test.mjs`, `backend/tests/test_profile_sbox quedó sin respuesta y se interrumpió; la ejecución autorizada fuera del sandbox finalizó correctamente. Sin revisión visual.

## Bloque 2 — implementado
- Aviso general de demostración; se eliminan repeticiones solo al presentar empresa/descripción/publicación. Catálogos, IDs y datos del scoring intactos.
- Archivos: `frontend/src/app/vacancy-presentation.ts`, `dashboard.tsx`.
- Verificación de código: transformación exclusiva de presentación. Controles TypeScript/lint/build pendientes al cierre.
- Próximo paso: migración compatible y disponibilidad por simulación (bloque 3), sin borrar historial ni deducir contrataciones históricas.

## Bloque 3 — implementado, pendiente aplicar a las bases locales
- Tabla `simulations`, relación en postulaciones y fecha de contratación nullable. Unicidad candidato/vacante por simulación. Migración `0002_simulations.py`: conserva las filas anteriores en simulación inicial; no inventa fechas ni contrataciones. Alembic comprueba claves foráneas y migra transaccionalmente sin cascadas al recrear la tabla SQLite.
- Contratar, postular y nueva simulación se serializan mediante `BEGIN IMMEDIATE`. Una vacante ocupada responde 409; una nueva simulación exige confirmación y versión actual. El historial anterior queda en lectura, sus recordatorios se preservan pero no aparecen como pendientes actuales.
- UI: disponibles/ocupadas, bloqueo de postulación, sección contratados y simulaciones, nueva simulación confirmada. Sin cambios al scoring/transiciones.
- Archivos: `backend/app/models/{entities,contracts}.py`, `app/services/{applications,simulations}.py`, `app/api/workflow.py`, `alembic/env.py`, `alembic/versions/0002_simulations.py`, `tests/{test_simulations,test_persistence}.py`, `frontend/src/app/dashboard.tsx`.
- Pruebas enfocadas: **3 aprobadas en 1.01 s**. Cubren contratación, bloqueo, persistencia/reconexión, nueva simulación, confirmación obsoleta, contrataciones simultáneas y conservación exacta de filas históricas relacionadas al migrar 0001→head.
- Bases reales todavía sin migrar; no se inició una simulación nueva en ellas. Próximo paso: trazabilidad de ejecución (bloque 4), controles finales y aplicación conservadora de migraciones.

## Bloque 4 — implementado
- Migración `0003_execution_trace.py` añade `operation_id` y contexto JSON nullable a la bitácora existente. Los registros históricos permanecen sin atribución de proveedor/modelo.
- Nuevas operaciones identifican componente (campo legado `agent`), acción, motivo, estado/resultado, referencia y operación relacionada. Extracción distingue `real`, `simulated`, `unknown` y `reused`; los otros componentes usan `rules`.
- Contexto por operación con proveedor, modelo configurado separado del efectivo, ID de solicitud y de respuesta cuando existen. Se toma el modelo efectivo de la respuesta ORIGINAL de Groq; el adaptador LangChain instalado usa el configurado en `model_name`, por lo que ese campo no sirve de prueba.
- Adaptador mínimo sobre el mismo ChatGroq/modelo, sin dependencias nuevas. No se almacenan prompts, texto CV, respuesta completa, claves ni mensajes originales de excepción. Los fallos de extracción también se registran.
- Archivos: `backend/app/services/{execution_trace,profile_extractor}.py`, `main.py`, `app/repository.py`, `app/models/{entities,contracts}.py`, `alembic/versions/0003_execution_trace.py`, `tests/{conftest,test_execution_trace,test_document_identity}.py`, `frontend/src/app/dashboard.tsx`.
- Pruebas enfocadas: **4 aprobadas en 0.82 s**, todas sintéticas. Contexto simulado, metadatos originales vs configuración, reutilización sin llamada y fallo sanitizado. Ninguna llamada real a Groq.
- Próximo paso: ejecutar una vez los controles finales; aplicar migraciones a ambas bases con copias de seguridad y comparación de datos previos. Servidores habituales identificados en 3000 (Next dev) y 8000 (Uvicorn con recarga); no se levantaron servidores temporales.

## Controles finales — 2026-10-13
- Suite backend: **130 aprobadas y 1 fallo en 20.76 s**. El fallo era una expectativa antigua de una sola traza tras cuatro solicitudes: ahora se registran creación, extracción y tres reutilizaciones. Se actualizó la prueba para comprobar esas cinco acciones y mantener la verificación de candidato único/una sola llamada simulada. Reejecución **solo de ese caso: 1 aprobada en 0.80 s**. Los 131 casos quedaron verificados entre la suite y esa corrección puntual; no se repitió la suite completa.
- Frontend: **22 pruebas aprobadas** (21 flujo CV + 1 rango salarial), `npx tsc --noEmit`, `npm run lint` y `npm run build` aprobados en una sola ronda. Node emite aviso no bloqueante `MODULE_TYPELESS_PACKAGE_JSON`; no se cambió la configuración de módulos fuera de alcance.
- `compileall` backend aprobado. No hubo navegador ni llamada real a Groq. Los resultados históricos no se modificaron.

## Cierre y estado actual
- **Los cuatro bloques están implementados.** Pendiente únicamente la comprobación visual/manual del equipo; no hay bloqueos funcionales conocidos a partir de estas verificaciones.
- Migraciones **0002 y 0003 aplicadas** a `backend/workint.db` y `backend/workint_escenarios.db`. Comparación de cada fila y cada columna preexistente: idénticas antes/después en ambas bases. `foreign_key_check` sin incidencias e `integrity_check=ok`. No se borró, fusionó, reseedeó ni reinició ninguna base; documentos/perfiles y cambios previos conservados.
- Copias previas (locales, no versionadas): `backend/backups/entrega2-20261013T183434Z/workint.db` y `backend/backups/entrega2-20261013T183434Z/workint_escenarios.db`. No restaurarlas sobre una base que haya recibido cambios nuevos.
- Se añadió una simulación inicial por base para contener los registros existentes. No se ejecutó la acción de nueva simulación ni se inventaron contrataciones en las bases reales. `hired_at` histórico sigue desconocido; las trazas antiguas no tienen contexto/modelo atribuido retrospectivamente.
- `README.md` actualizado en instrucciones de uso, diferenciando web actual y PoC separada. No se editaron informes históricos ni plantillas Word/Excel.
- `git diff --check`: aprobado. Estado del repositorio conserva los cambios previos, incluidos archivos todavía no versionados; no hubo commit ni limpieza.
- Comprobación HTTP puntual: `http://127.0.0.1:8000/health`, `/api/v1/simulations` y `http://127.0.0.1:3000` devolvieron 200. El HTML de 3000 contiene la sección nueva de contratados. Esto **no constituye revisión visual de navegador**.
- Servidores habituales conservados: Next dev en 3000 y Uvicorn con recarga en 8000, ambos desde este proyecto. No se levantaron servidores temporales.

## Próximo paso concreto para el equipo / Antigravity
Abrir `http://127.0.0.1:3000` y comprobar manualmente:
1. Editar un perfil: prefijo telefónico internacional, rango salarial inválido sin pérdida del borrador, corrección y guardado con retorno a lectura.
2. Contratar una postulación pasando por los estados actuales; comprobar sección de contratados y bloqueo de otra postulación a la vacante ocupada.
3. Recargar: perfil, ocupación y fecha de contratación permanecen. Confirmar nueva simulación: vacantes disponibles otra vez e historial anterior visible en lectura.
4. Revisar la bitácora: componente, acción, motivo, resultado y operación; trazas históricas sin atribución inventada. No es necesario llamar a Groq para esta revisión.

Comandos de continuación, solo si se modifica código: usar los controles al inicio de este archivo; para pruebas enfocadas backend, `.venv/bin/python -m pytest -q tests/test_profile_save.py tests/test_simulations.py tests/test_execution_trace.py`. La aplicación actual ya tiene las migraciones; no repetir ingestas. Si se instala en otra copia, usar las instrucciones de migración del README principal.

Limitaciones relevantes: simulación local sobre SQLite (bloqueos `BEGIN IMMEDIATE`); sin OCR ni servicios externos nuevos. Contrataciones anteriores sin fecha verificable la muestran como no registrada. No se ha verificado una llamada real a Groq en esta sesión: la captura de metadatos se probó con respuestas sintéticas y con el transporte bloqueado. El adaptador de metadatos depende de la versión fijada de `langchain-groq`; al actualizarla se debe conservar esa prueba. La revisión visual queda a cargo del equipo.
