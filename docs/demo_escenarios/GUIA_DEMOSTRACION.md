# WORKINT - Escenarios controlados de contratación

Preparación local verificada el 13 de octubre de 2026. Proyecto: `~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software`. La otra copia llamada `WORKIN1` no fue modificada.

## 1. Estado entregado

- Base activa: `backend/workint_escenarios.db`, esquema Alembic `0001`.
- Exactamente **10 vacantes ficticias**: `escenarios-v01` a `escenarios-v10`.
- **0 candidatos, 0 perfiles, 0 postulaciones, 0 recordatorios y 0 eventos de agentes asociados a candidatos**.
- Dos eventos técnicos de ingesta, sin candidato, por las dos ejecuciones de importación. La tabla `alembic_version` contiene la revisión técnica `0001`.
- Cinco CV PDF con texto seleccionable en `docs/demo_escenarios/cvs/`. Son entradas para subir manualmente; no se insertaron sus candidatos.
- Nuevos PDF cargados por la aplicación: `backend/uploads_escenarios/`.
- Flujo manual: `postulado → en_revision → entrevista → contratado`.
- La base y los documentos históricos permanecen intactos. El estado `contratado` es exclusivamente una simulación local, sin comunicación a empresas.

Los cinco candidatos y las cinco contrataciones son el resultado esperado DESPUÉS de la demostración manual, no el contenido precargado.

## 2. Qué es original y qué cambió

### Funcionalidades originales de Entrega 2

Se conservan Next.js/TypeScript, FastAPI/Python, SQLite/SQLAlchemy/Alembic, los grafos LangGraph, la extracción de texto con pypdf y de perfil con Groq previa autorización, la edición y creación manual, el cálculo determinista de afinidad, la confirmación de postulación simulada, el bloqueo de duplicados, las evidencias, los recordatorios locales y la actividad de agentes.

Los estados originales eran `postulado`, `en_revision`, `entrevista` y `descartado`. La documentación original está en `docs/entrega2/`; no se reescribió ni se actualizaron los documentos académicos Word o Excel.

### Mejoras posteriores implementadas en esta preparación

1. Nueva base y almacenamiento PDF aislados, con configuración compartida por API, Alembic e ingesta.
2. Protección contra conexiones accidentales a la base histórica mientras `WORKINT_SCENARIOS=1`.
3. Dataset independiente de 10 vacantes y cinco CV ficticios.
4. Nuevo estado final `contratado`, con cierre del recordatorio, próximo paso e historial persistente.
5. Catálogo visible en el dashboard aun cuando todavía no existen perfiles.
6. Pruebas adicionales y guía reproducible.

### Para una entrega posterior

La experiencia en años y las empresas anteriores no afectan el score. Continúan pendientes las mejoras del backlog anterior. No se implementaron agenda, fechas de entrevista, calendarios, integraciones con empleadores, notificaciones externas, contratos ni tablas de entrevistas. Tampoco se añadió autenticación multiusuario.

## 3. Conservación de los datos anteriores

Respaldo de esta preparación:

`~/Documentos/ChatGPT/BACKUPS/workint_20261013T102425Z/`

Contiene una copia SQLite consistente obtenida con `sqlite3.Connection.backup()`, las carpetas anteriores `backend/uploads/` y `docs/`, el dataset recuperado `vacancies_historicas.json`, las huellas `SHA256_antes.json` y copias de los archivos de código existentes antes del primer cambio en `codigo_antes/`.

La base histórica tenía 12 candidatos, 12 perfiles, 18 vacantes, 10 postulaciones, 10 recordatorios y 139 eventos. Se abrió en modo de solo lectura para respaldarla. `PRAGMA integrity_check` del respaldo devolvió `ok`.

**Hallazgo:** faltaba `backend/app/data/vacancies.json` en el proyecto. Se reconstruyó ese JSON con las 18 vacantes persistidas en la base histórica, sin inventar ni modificar sus datos. Se conservaron tanto esa copia de trabajo como la copia de respaldo. Las pruebas originales pueden volver a usarlo.

No se borró ni se modificó `backend/workint.db`. La comparación SHA-256 final confirmó que los 25 archivos históricos inventariados permanecen idénticos. No se ejecutó `git add`, `commit`, `push`, `merge` ni `reset`.

## 4. Configuración y creación de la nueva base

`backend/.env` conserva la clave Groq existente y añade únicamente:

```dotenv
WORKINT_SCENARIOS=1
WORKINT_DATABASE_URL=sqlite:///workint_escenarios.db
WORKINT_UPLOAD_DIR=uploads_escenarios
WORKINT_VACANCIES_PATH=app/data/vacancies_escenarios.json
```

También se entrega `backend/.env.escenarios.example`, sin credenciales. No reemplazar todo `.env` con ese ejemplo si contiene una clave local.

`app/config.py` carga el archivo `.env` sin sobrescribir variables ya exportadas. Las rutas relativas se resuelven respecto a `backend/`, independientemente de la carpeta desde la que se invoque Python. No hay rutas personales absolutas dentro del código fuente. Sin variables de configuración se mantienen los valores históricos por defecto: `workint.db`, `uploads/` y el dataset anterior.

En esta preparación se comprobó la ruta efectiva, se ejecutó `alembic upgrade head` sobre la base nueva y se verificaron todas las tablas vacías **antes** de importar. Evidencia: `evidencias/base_inicial.json`. La migración existente crea el esquema; no se copiaron registros de la base anterior.

No hizo falta una migración adicional: `applications.status` ya es `String(32)` y no tiene restricción ENUM ni CHECK que impida guardar `contratado`.

### Repetir migraciones e ingesta sin mezclar datos

La base ya está preparada; estos comandos son para reproducir o verificar la configuración y se pueden repetir. No borran candidatos que se carguen después.

```bash
cd ~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software/backend
export WORKINT_SCENARIOS=1
export WORKINT_DATABASE_URL=sqlite:///workint_escenarios.db
export WORKINT_UPLOAD_DIR=uploads_escenarios
export WORKINT_VACANCIES_PATH=app/data/vacancies_escenarios.json
./.venv/bin/python -c 'from app.config import DATABASE_URL, check_database; print("Base efectiva:", check_database(DATABASE_URL))'
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python -m app.services.vacancies
./.venv/bin/python -m app.scenarios
```

La ruta impresa debe terminar en `WORKINT/Proyecto-ing-Software/backend/workint_escenarios.db`. Alembic y la ingesta muestran además la ruta inmediatamente antes de operar. Si aparece la base histórica, detenerse: el modo escenarios también bloquea esa conexión mediante código. Las variables exportadas en la terminal tienen prioridad sobre `.env`.

La ingesta valida todo el lote antes de escribir y actualiza por ID. La base con nombre `workint_escenarios.db` rechaza datasets distintos de sus diez IDs y cualquier mezcla previa. Se ejecutó la ingesta dos veces: ambas dejaron exactamente diez vacantes. Cada ejecución agrega una traza técnica de ingesta; eso no es una vacante duplicada.

`python -m app.scenarios` abre SQLite en modo de solo lectura, muestra rutas, conteos e IDs, y comprueba integridad y claves foráneas. Después de la demostración mostrará los candidatos y postulaciones que ustedes hayan creado; no los elimina.

## 5. Comandos exactos de inicio

Backend, en una terminal:

```bash
cd ~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software/backend
./.venv/bin/python -m app.scenarios
./.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend, en otra terminal:

```bash
cd ~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software/frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
```

Abrir <http://127.0.0.1:3000>. API/documentación: <http://127.0.0.1:8000/docs>.

Al finalizar la preparación ya había servidores del proyecto activos en esos puertos. Se verificó que recargaron los cambios: la API respondió con diez vacantes y cero perfiles, y el navegador mostró el catálogo correcto. No iniciar otra instancia sobre un puerto ocupado. Si necesitan cambiar de puertos, usar `8001` para Uvicorn y `NEXT_PUBLIC_API_URL=http://127.0.0.1:8001` con frontend en `3001`; ambas combinaciones están permitidas por CORS. Detener antes la otra instancia de Next.js del mismo proyecto para evitar su bloqueo del directorio de desarrollo.

## 6. Vacantes y hojas de vida

Todas las empresas, personas y ofertas son ficticias. Los correos usan `example.com`. Las ofertas incluyen fuente `demo`, descripción, ciudad, modalidad, contrato, salarios y habilidades requeridas/deseables compatibles con `VacancyData`.

| CV | Persona ficticia | Objetivo | Ciudad / modalidad | Aspiración mensual COP |
|---|---|---|---|---|
| [CV_A_python.pdf](cvs/CV_A_python.pdf) | Valeria Ríos Luna | V01 - Backend Python | Medellín / híbrido | 5.000.000 - 6.000.000 |
| [CV_B_java.pdf](cvs/CV_B_java.pdf) | Mateo Salazar Vega | V03 - Backend Java | Bogotá / remoto | 4.500.000 - 5.500.000 |
| [CV_C_embebidos.pdf](cvs/CV_C_embebidos.pdf) | Camila Torres Prado | V05 - Sistemas Embebidos | Cali / presencial | 4.000.000 - 5.000.000 |
| [CV_D_datos.pdf](cvs/CV_D_datos.pdf) | Nicolás Pardo Sol | V07 - Analista de Datos | Medellín / remoto | 3.500.000 - 4.500.000 |
| [CV_E_react.pdf](cvs/CV_E_react.pdf) | Daniela Mora Céspedes | V09 - Frontend React | Bogotá / híbrido | 4.000.000 - 5.000.000 |

V01 corresponde a `escenarios-v01`, y así sucesivamente. Las alternativas son V02 Backend Node.js, V04 Ingeniero Java Senior, V06 Firmware Senior, V08 Ingeniero de Datos y V10 Frontend Angular. Se diferencian por tecnologías, modalidad, ubicación o rango salarial. La antigüedad senior es informativa y por sí misma no penaliza al candidato.

Los cinco CV tienen educación 2018-2022 y experiencia laboral ficticia de julio de 2023 a junio de 2026 (tres años), con disponibilidad inmediata. Son PDF de una página, con fuentes incrustadas y texto seleccionable; se revisaron visualmente y se verificó la extracción de sus nombres, correos, cargos y habilidades con pypdf.

`perfiles_ficticios.json` es referencia legible para corrección manual y fixture de pruebas. No es una instrucción de importación de candidatos. `backend/scripts/generate_scenario_cvs.py` regenera únicamente los PDF mediante ReportLab, sin abrir SQLite:

```bash
cd ~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software/backend
./.venv/bin/python scripts/generate_scenario_cvs.py
```

## 7. Resultado del matching sin alterar el motor

Se conserva exactamente `matching.py` y sus pesos: habilidades 45, cargo 20, modalidad 15, ubicación 10 y salario 10. Los datos desconocidos aportan cero sin redistribución. Una vacante remota cumple el componente de ubicación cuando hay datos geográficos. Las habilidades deseables, el contrato y la experiencia siguen siendo informativos.

Con los perfiles de referencia completos se obtuvo:

| Perfil | Primera recomendación | Puntos | Segunda recomendación | Puntos |
|---|---|---:|---|---:|
| A | V01 | 100 | V03 | 51,33 |
| B | V03 | 100 | V02 | 54 |
| C | V05 | 100 | V06 | 30 |
| D | V07 | 100 | V01 | 47 |
| E | V09 | 100 | V10 | 45,83 |

Estos 100 puntos resultan de las habilidades requeridas, el cargo y las preferencias presentes en los datos. No hay reglas por nombre, emparejamientos precargados en el algoritmo ni puntajes forzados. Una prueba cambia el nombre y elimina la experiencia y comprueba que el score no varía. Evidencia completa: `evidencias/matching_referencia.json`.

**Límite de esta comprobación:** son perfiles de referencia, no resultados obtenidos en una llamada real a Groq. La extracción puede omitir habilidades, cargo o preferencias, y entonces el puntaje disminuirá. Revisar los datos y el desglose del score; completar únicamente información que conste en el PDF. No modificar el algoritmo para recuperar 100 puntos.

## 8. Recorrido manual para cada candidato

1. Abrir WORKINT. Antes de crear perfiles deben verse las diez vacantes ficticias.
2. En **Cargar hoja de vida**, seleccionar el PDF correspondiente de `docs/demo_escenarios/cvs/` y pulsar **Cargar documento**.
3. Marcar el consentimiento que autoriza enviar el contenido a Groq y generar el perfil. No confundir la extracción local de texto PDF con la extracción estructurada de IA.
4. Revisar nombre, correo, ubicación, resumen, habilidades, experiencia, educación y cargo objetivo.
5. Corregir manualmente lo que Groq haya omitido. Revisar especialmente ciudad preferida, modalidad y salario según la tabla anterior.
6. Pulsar **Guardar perfil**. Consultar **recomendaciones y seguimiento** y comprobar que aparecen las diez vacantes y que el objetivo tiene afinidad coherente.
7. Abrir **Detalle y explicación**: revisar requisitos, deseables, rango salarial, fuente ficticia y componentes del score.
8. Pulsar **Preparar postulación simulada**, marcar la confirmación y confirmar. Debe quedar en `postulado`. Sin confirmación explícita no se registra nada.
9. En **Postulaciones y seguimiento**, cambiar manualmente a `en_revision`, después a `entrevista` y finalmente a `contratado`.
10. Comprobar la etiqueta **Finalizada**, el mensaje de proceso simulado terminado con contratación y el selector deshabilitado. No debe haber un recordatorio pendiente para esa postulación.
11. Abrir **Evidencia de la simulación** y **Historial del proceso**. Mostrar también **Actividad de los agentes**.
12. Recargar la página; seleccionar de nuevo el candidato en **Perfiles guardados**. El estado `contratado`, la evidencia y el historial se recuperan de SQLite.
13. Si se reinicia el backend con la misma configuración, seleccionar de nuevo el perfil y repetir la comprobación. No volver a crear el perfil ni la postulación para comprobar persistencia.
14. Repetir con los otros cuatro PDF. El resultado esperado será cinco candidatos, diez vacantes y cinco postulaciones en `contratado`.

La interfaz no elige automáticamente una persona ni contrata por puntuación alta. Si se intenta postular dos veces a la misma vacante, la API responde `409` y no duplica el registro.

### Estados y recordatorios

| Estado | Transiciones permitidas | Seguimiento pendiente |
|---|---|---|
| `postulado` | `en_revision`, `descartado` | Sí |
| `en_revision` | `entrevista`, `descartado` | Sí |
| `entrevista` | `contratado`, `descartado` | Sí |
| `contratado` | Ninguna | No |
| `descartado` | Ninguna | No |

Un salto como `postulado → contratado`, una repetición del mismo estado o un intento de reabrir un estado final recibe `409`. La evidencia original permanece inalterada y los cambios manuales se guardan en `agent_logs` dentro de la misma transacción que el estado y el recordatorio.

### Si Groq falla

No se comprobó la disponibilidad real del proveedor durante la preparación ni se consumieron llamadas reales. Si al generar un perfil aparece un error, anotar el mensaje y la hora. La API maneja los errores conocidos y el dashboard conserva **Crear perfil manual**: completar los datos desde el PDF y guardar. El origen debe figurar como `manual`; no presentar esa operación como extracción real de IA. Un perfil extraído y luego corregido figura como `groq_editado`.

La creación manual utiliza la funcionalidad existente y no asocia automáticamente el PDF ya cargado con ese perfil. Los documentos permanecen en el almacenamiento local aislado.

## 9. Consultar evidencias

En la interfaz: **Evidencia de la simulación** muestra ID de operación, candidato, vacante, fecha, confirmación y tipo `simulada`. **Historial del proceso** filtra los eventos de esa postulación. **Actividad de los agentes** presenta los eventos cronológicos de perfil, vacantes, postulación y seguimiento.

En la API, usando el `candidate_id` del perfil:

- `GET /api/v1/profiles/{candidate_id}/applications`: estado, evidencia, próximo paso y transiciones disponibles.
- `GET /api/v1/profiles/{candidate_id}/activity`: historial persistente.
- `GET /api/v1/profiles/{candidate_id}/reminders`: recordatorios, incluidos los cerrados (`pending=false`).

Evidencias de esta preparación en `docs/demo_escenarios/evidencias/`: base vacía inicial, base antes de la demostración, matching de referencia, salida Pytest, TypeScript, lint, build y verificación final de datos históricos. No confundirlas con las evidencias que se generarán al ejecutar la demostración manual.

## 10. Pruebas ejecutadas

**86 pruebas aprobadas en 11,05 segundos**: 47 existentes y 39 nuevas. Las nuevas cubren migración vacía, diez vacantes, idempotencia, separación del dataset, cinco rankings, lectura de cinco PDF, consentimiento, confirmación, duplicados, las 25 combinaciones de estados, cierre de recordatorios, historial y persistencia en un nuevo intérprete que vuelve a cargar FastAPI y SQLite.

Los cinco recorridos de integración suben los PDF a almacenamiento temporal y simulan la extracción del proveedor. Ninguna prueba escribe candidatos en la base de demostración. La fixture crea una base temporal por prueba, aisla los PDF, elimina la clave Groq del entorno del test y bloquea el transporte del SDK.

Comandos ejecutados:

```bash
cd ~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software/backend
./.venv/bin/python -m pytest -q -o faulthandler_timeout=45

cd ~/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software/frontend
npx tsc --noEmit --incremental false
npm run lint
npm run build
```

TypeScript: aprobado. Lint: aprobado. Build de producción Next.js 16.4.0: aprobado. Las comprobaciones del frontend se repitieron después del último ajuste del catálogo. `git diff --check` no reportó problemas.

Comprobación del navegador real: <http://127.0.0.1:3000/> cargó las diez ofertas y mostró el selector sin candidatos, sin postulaciones y sin recordatorios pendientes. No se ejecutó una contratación manual real en esa base: se reservó para la presentación solicitada.

El primer intento de Pytest dentro del sandbox se quedó detenido en TestClient y se canceló. La ejecución local posterior completó las 86 pruebas; su salida se conserva en `evidencias/pytest.txt`.

## 11. Archivos de esta preparación

| Archivo o grupo | Cambio |
|---|---|
| `backend/app/config.py` | Carga compartida del entorno, resolución de rutas y protección histórica |
| `backend/app/database.py` | Usa la configuración compartida y valida la base antes de crear el motor |
| `backend/alembic/env.py` | Resuelve y muestra la ruta efectiva antes de migrar |
| `backend/main.py` | Directorio de documentos configurable, conservando `uploads/` como predeterminado |
| `backend/app/models/contracts.py` | Admite IDs nuevos sin colisión y el estado `contratado` |
| `backend/app/services/applications.py` | Transición final, próximo paso, recordatorio cerrado y traza de seguimiento |
| `backend/app/services/vacancies.py` | Ruta visible, selección del dataset por entorno y rechazo de mezclas en escenarios |
| `backend/app/scenarios.py` | Comprobación de solo lectura de rutas, conteos e integridad |
| `backend/app/data/vacancies.json` | Recuperación del dataset histórico desde SQLite |
| `backend/app/data/vacancies_escenarios.json` | Diez nuevas vacantes ficticias |
| `backend/.env` y `.env.escenarios.example` | Configuración local activa y ejemplo sin secretos |
| `backend/workint_escenarios.db`, `backend/uploads_escenarios/` | Base nueva migrada y almacenamiento aislado |
| `backend/scripts/generate_scenario_cvs.py` | Generador reproducible de cinco CV; no inserta candidatos |
| `backend/tests/conftest.py`, `test_scenarios.py` | Aislamiento del proveedor/almacenamiento y pruebas específicas |
| `frontend/src/app/dashboard.tsx` | Tipos de estados, contratado final y catálogo sin perfil |
| `.gitignore` | Ignora los PDF cargados en el nuevo almacenamiento |
| `README.md` | Enlace a esta guía; conserva la descripción de Entrega 2 |
| `docs/demo_escenarios/` | CV, referencias, guía y evidencias |

`matching.py`, la migración `0001_mvp.py`, el esquema ORM y los archivos académicos oficiales no se modificaron. Los cambios anteriores del usuario presentes en el repositorio se conservaron.
