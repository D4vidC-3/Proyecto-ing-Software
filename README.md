# WORKINT — Ejecutar y probar el proyecto del ZIP

## 1. Instalar los requisitos

- **Python 3.14**, para acercarse al entorno usado por el equipo (la documentación registra 3.14.7). Descarga: [Python oficial](https://www.python.org/downloads/). En Windows, habilita la opción para añadir Python al PATH si el instalador la ofrece.
- **Node.js 22.x actualizado**, con npm. El entorno documentado usó Node 22.23.1 y npm 10.9.8. Descarga: [Node.js oficial](https://nodejs.org/en/download). El Next.js incluido declara Node >=20.9.0; esta guía usa la rama 22 para reproducir el entorno y sus pruebas.
- Navegador e internet para instalar dependencias. La extracción con IA también necesita conexión y una clave de Groq propia; las funciones manuales se pueden probar sin esa clave.

Abre una terminal nueva después de instalar. En Windows utiliza **PowerShell**:

```powershell
py -3.14 --version
node --version
npm.cmd --version
```

En Linux o macOS:

```bash
python3.14 --version
node --version
npm --version
```

Si un comando no existe, resuelve primero la instalación o el PATH. Si `python3 --version` ya muestra 3.14, puedes usar `python3` en lugar de `python3.14` para crear el entorno.

## 2. Descomprimir y ubicar el proyecto

1. Extrae completamente el ZIP en una carpeta local; no ejecutes archivos desde el visor del ZIP.
2. Entra a la carpeta que contiene **backend** y **frontend**, normalmente `WORKINT/Proyecto-ing-Software` o directamente `Proyecto-ing-Software`.
3. Abre dos terminales en esa carpeta. En VS Code puedes abrir esa carpeta y usar **Terminal → Nueva terminal** dos veces; VS Code es opcional.

Estructura útil:

```text
Proyecto-ing-Software/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env
│   ├── alembic/
│   └── workint_escenarios.db
├── frontend/
│   ├── package.json
│   └── package-lock.json
└── docs/demo_escenarios/cvs/
    ├── CV_A_python.pdf
    ├── CV_B_java.pdf
    ├── CV_C_embebidos.pdf
    ├── CV_D_datos.pdf
    └── CV_E_react.pdf
```

El ZIP incluye `.venv`, `node_modules` y `.next` de la computadora de origen. Se creará un entorno Python nuevo llamado **`.venv-local`**, npm reinstalará sus dependencias y se eliminará únicamente la caché `.next`. No uses el Python de `.venv` que viene comprimido.

El `main.py` de la raíz corresponde a un prototipo anterior. Para abrir la aplicación web utiliza los comandos de esta guía desde `backend/` y `frontend/`.

## 3. Revisar la configuración del backend

Abre `backend/.env` con un editor de texto. Para usar los mismos escenarios que el equipo, verifica estas líneas, sin duplicarlas:

```dotenv
WORKINT_SCENARIOS=1
WORKINT_DATABASE_URL=sqlite:///workint_escenarios.db
WORKINT_UPLOAD_DIR=uploads_escenarios
WORKINT_VACANCIES_PATH=app/data/vacancies_escenarios.json
GROQ_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=
```

Para probar IA, escribe tu clave después de `GROQ_API_KEY=`. Para probar el flujo manual, deja el valor vacío. Guarda el archivo como `.env`, no como `.env.txt`. El nombre del modelo es el configurado en el proyecto; su disponibilidad depende del proveedor.

**Sobre el ZIP compartido:** contiene un `.env` con una clave Groq no vacía. El propietario debe revocarla o rotarla si se compartió por accidente y excluirla de los próximos ZIP. Cada integrante debe configurar su propia clave; no copies claves en chats, capturas ni documentación.

Las rutas anteriores son relativas a `backend/`: no necesitan la ruta personal de quien creó el ZIP. Las variables que ya estén definidas en una terminal tienen prioridad sobre `.env`; usa terminales nuevas si tenías otra configuración.

## 4. Preparar el backend — terminal 1

Ejecuta los comandos **uno por uno**. Si aparece un error, resuélvelo antes de continuar. Elige solo el bloque de tu sistema operativo. Ambos empiezan desde la carpeta `Proyecto-ing-Software`.

### Windows (PowerShell)

```powershell
cd backend
py -3.14 -m venv .venv-local
.\.venv-local\Scripts\python.exe -m pip install --upgrade pip
Get-Content requirements.txt | Where-Object { $_ -notmatch '^\s*uvloop\b' } | Set-Content -Encoding ascii requirements.windows.txt
.\.venv-local\Scripts\python.exe -m pip install -r requirements.windows.txt -r requirements-dev.txt
.\.venv-local\Scripts\python.exe -m pip check
.\.venv-local\Scripts\python.exe -m alembic upgrade head
.\.venv-local\Scripts\python.exe -m app.scenarios
```

El archivo derivado `requirements.windows.txt` conserva las versiones y omite únicamente `uvloop`, que [no admite Windows](https://github.com/MagicStack/uvloop/blob/master/setup.py). Uvicorn puede usar `asyncio`. No hace falta activar el entorno ni cambiar la política de ejecución de PowerShell.

### Linux o macOS

```bash
cd backend
python3.14 -m venv .venv-local
./.venv-local/bin/python -m pip install --upgrade pip
./.venv-local/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
./.venv-local/bin/python -m pip check
./.venv-local/bin/python -m alembic upgrade head
./.venv-local/bin/python -m app.scenarios
```

### Qué debes comprobar

- `pip check` debe terminar sin dependencias incompatibles.
- Alembic debe terminar sin errores. Aplica las migraciones pendientes sobre la base incluida; la versión revisada contiene las revisiones hasta `0003`.
- `app.scenarios` debe mostrar una ruta que termine en **backend/workint_escenarios.db**, **10 vacantes** y los IDs `escenarios-v01` a `escenarios-v10`.

**El ZIP revisado ya contiene un perfil y una postulación.** Es normal que aparezcan datos anteriores: no esperes una base vacía. Las guías históricas de `docs/` describen etapas anteriores.

No repitas la importación de vacantes para esta base incluida. Solo si recibiste una copia sin base, o el reporte muestra cero vacantes después de migrar, carga el dataset una vez y repite el reporte:

Windows:

```powershell
.\.venv-local\Scripts\python.exe -m app.services.vacancies
.\.venv-local\Scripts\python.exe -m app.scenarios
```

Linux/macOS:

```bash
./.venv-local/bin/python -m app.services.vacancies
./.venv-local/bin/python -m app.scenarios
```

## 5. Encender el backend — terminal 1

Desde `backend/`, en Windows:

```powershell
.\.venv-local\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --loop asyncio
```

En Linux/macOS:

```bash
./.venv-local/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Deja esta terminal abierta. Comprueba en el navegador:

- [Estado de la API](http://127.0.0.1:8000/health): debe responder `{"status":"ok","service":"WORKINT"}`.
- [Documentación interactiva](http://127.0.0.1:8000/docs): debe mostrar los endpoints de WORKINT.

`/health` comprueba que el servidor responde; el reporte anterior comprueba la base. Continúa cuando ambos funcionen.

## 6. Preparar y encender el frontend — terminal 2

Esta segunda terminal comienza en `Proyecto-ing-Software`, no en `backend`.

### Windows (PowerShell)

```powershell
cd frontend
if (Test-Path .next) { Remove-Item -Recurse -Force .next }
npm.cmd ci
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
```

### Linux o macOS

```bash
cd frontend
rm -rf .next
npm ci
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
```

La eliminación afecta solamente la caché generada de Next.js dentro de `frontend/`. `npm ci` reinstala `node_modules` usando el archivo de versiones incluido. Espera a que termine correctamente antes de ejecutar el último comando.

Deja también esta terminal abierta. Cuando indique que está listo, abre:

**[WORKINT — http://127.0.0.1:3000](http://127.0.0.1:3000)**

La primera carga puede tardar mientras Next.js compila. Cada compañero abre esta dirección en su propia computadora.

## 7. Probar el programa paso a paso

### Prueba inicial sin IA

1. Verifica que aparezca el catálogo de las diez vacantes.
2. Pulsa **Crear perfil manual**.
3. Ingresa datos ficticios. Por ejemplo: nombre `Prueba Equipo`, correo `prueba.equipo@example.com`, ciudad `Medellín`, cargo `Desarrollador Backend Python`, habilidades `Python`, `FastAPI` y `PostgreSQL`, modalidad `híbrido` y aspiración de `5000000` a `6000000` COP. Completa los campos que solicite el formulario.
4. Pulsa **Guardar perfil** y espera la confirmación. Usa **Editar** para cambiar un dato y vuelve a guardar.
5. Pulsa **Consultar recomendaciones y seguimiento** y revisa el detalle del puntaje de una vacante.
6. Prepara una postulación simulada. Primero cancela y verifica que no se registre; luego repite, marca la confirmación y confirma.
7. En seguimiento, avanza en orden: `postulado → en_revision → entrevista → contratado`. Son cambios manuales de demostración.
8. Revisa la evidencia, el historial y **Actividad de componentes y flujos**. Al terminar en `contratado`, el recordatorio deja de estar pendiente y la vacante queda ocupada en esa simulación.
9. Recarga la página y selecciona el perfil guardado: sus datos y el proceso deben continuar disponibles.

Si una vacante ya está ocupada o el perfil ya tiene esa postulación, utiliza otra vacante o sigue la sección de nueva simulación. No se permite repetir una postulación a la misma vacante con el mismo candidato dentro de la misma simulación.

### Prueba con un PDF e IA

1. Configura tu clave Groq en `backend/.env` y reinicia el backend si lo tenías abierto.
2. En **Cargar y validar hoja de vida**, selecciona un PDF de `docs/demo_escenarios/cvs/`.
3. Pulsa **Cargar documento** y espera la validación.
4. Marca el consentimiento para enviar el contenido al proveedor y pulsa **Generar perfil con IA**.
5. Revisa y corrige los datos extraídos antes de guardar. La IA puede omitir información; el puntaje depende de lo que quedó registrado.
6. Continúa con recomendaciones, postulación y seguimiento como en la prueba manual.

| PDF incluido | Perfil ficticio | Vacante de referencia |
|---|---|---|
| `CV_A_python.pdf` | Valeria Ríos Luna | V01 — Backend Python |
| `CV_B_java.pdf` | Mateo Salazar Vega | V03 — Backend Java |
| `CV_C_embebidos.pdf` | Camila Torres Prado | V05 — Sistemas Embebidos |
| `CV_D_datos.pdf` | Nicolás Pardo Sol | V07 — Analista de Datos |
| `CV_E_react.pdf` | Daniela Mora Céspedes | V09 — Frontend React |

Usa PDF con texto seleccionable, de hasta 5 MB, 10 páginas y 20.000 caracteres extraídos. Los escaneos sin texto no tienen OCR en esta versión. Un documento ya procesado puede recuperar su perfil existente; eso no implica una nueva llamada a IA.

Si Groq no está configurado, no responde o agota su cuota, continúa con **Crear perfil manual**. Las postulaciones y contrataciones son simulaciones locales; no se envían a empresas.

### Comenzar otra simulación

En **Contratados y simulaciones**, marca la confirmación y pulsa **Iniciar nueva simulación**. Las vacantes vuelven a estar disponibles; los perfiles se conservan y los procesos anteriores quedan en el historial de solo lectura. No necesitas borrar bases ni volver a importar vacantes.

## 8. Cerrar y volver a ejecutar otro día

Para detener el programa, pulsa **Ctrl+C** en cada terminal. Los perfiles y las postulaciones quedan en SQLite.

Para abrirlo de nuevo, repite únicamente:

1. El comando de Uvicorn del paso 5 desde `backend/`.
2. La variable `NEXT_PUBLIC_API_URL` y el comando `npm run dev` del paso 6 desde `frontend/` (en PowerShell, usa `npm.cmd`).
3. Abre `http://127.0.0.1:3000` y selecciona el perfil guardado.

No repitas la creación del entorno, instalación, limpieza de caché ni ingesta en cada inicio. Si recibes una nueva versión con migraciones, ejecuta `alembic upgrade head` antes de encender el backend.

## 9. Pruebas automatizadas opcionales

Puedes ejecutarlas en una tercera terminal. Desde `backend/`:

Windows:

```powershell
.\.venv-local\Scripts\python.exe -m pytest -q
```

Linux/macOS:

```bash
./.venv-local/bin/python -m pytest -q
```

La suite configura bases y documentos temporales y bloquea las llamadas reales a Groq. Un resultado correcto termina sin pruebas fallidas. Los conteos publicados en documentos antiguos corresponden a versiones anteriores.

Desde `frontend/`, en Windows:

```powershell
npm.cmd run test:cv
npx.cmd tsc --noEmit
npm.cmd run lint
```

Linux/macOS:

```bash
npm run test:cv
npx tsc --noEmit
npm run lint
```

`test:cv` ejecuta las pruebas del flujo del CV. Para incluir todos los archivos de pruebas frontend, en Node 22 actualizado:

```text
node --experimental-strip-types --test "tests/*.test.mjs"
```

Para comprobar además la compilación, detén el frontend de desarrollo y ejecuta `npm run build` (Windows: `npm.cmd run build`). No necesitas compilar para usar el modo de desarrollo de esta guía.

## 10. Soluciones a problemas frecuentes

| Problema | Solución |
|---|---|
| `python`, `py`, `node` o `npm` no se reconoce | Revisa la instalación y el PATH; cierra y abre la terminal. En Windows usa `py -3.14` y `npm.cmd` como arriba. |
| Windows bloquea `Activate.ps1` o `npm.ps1` | No actives el entorno: usa directamente `.venv-local\Scripts\python.exe`. Usa `npm.cmd`/`npx.cmd`. |
| Error de `uvloop` en Windows | Genera e instala `requirements.windows.txt` siguiendo el paso 4. |
| `No matching distribution found` o fallo al compilar una dependencia | Comprueba Python 3.14, sistema de 64 bits, pip actualizado y el nombre/versión exactos que fallan. La disponibilidad de los paquetes fijados depende del registro y de tu plataforma; comparte ese error con el equipo antes de cambiar versiones. |
| Conflicto con `websockets==17.2` | El ZIP WORKINT revisado fija `16.1.1`. Comprueba que estás usando el ZIP correcto y no la copia anterior WORKIN1. |
| `Could not import module main`, falta `app` o `alembic.ini` | Ejecuta los comandos del backend dentro de `Proyecto-ing-Software/backend`, con el Python de `.venv-local`. |
| `no such table` o falta una columna | Detén el backend, ejecuta `alembic upgrade head` y comprueba la base con `app.scenarios`. |
| Base histórica protegida o aparecen 18 vacantes | Revisa las cuatro variables `WORKINT_*` del paso 3 y las variables exportadas en tu terminal. Debes usar `workint_escenarios.db`. |
| `Failed to fetch` o la web no carga datos | Comprueba `/health`, ambas terminales y que `NEXT_PUBLIC_API_URL` coincida con el puerto real del backend. Reinicia el frontend tras cambiar esa variable. |
| El servicio de IA no está configurado o falla | Revisa tu clave, conexión y disponibilidad del modelo/proveedor; reinicia backend tras cambiar `.env`. Usa el perfil manual para continuar. |
| Error con el PDF | Prueba primero un PDF incluido. Debe tener texto seleccionable y cumplir los límites del paso 7. |
| Next.js informa un bloqueo en `.next/dev/lock` | Detén otra instancia de Next.js que esté usando esa misma carpeta. Con todas detenidas, elimina solo `frontend/.next` y vuelve a iniciar. |
| El puntaje no es 100 | Revisa habilidades, cargo y preferencias guardadas, y el desglose. Los datos desconocidos aportan cero; la afinidad no garantiza una contratación. |
| Vacante ocupada o postulación duplicada | Usa otra vacante o inicia una nueva simulación con confirmación. |

### Si los puertos 8000 o 3000 están ocupados

Puedes usar backend **8001** y frontend **3001**, que están permitidos en la configuración CORS. Detén primero tus instancias de WORKINT con Ctrl+C si siguen abiertas.

Windows, terminal backend:

```powershell
.\.venv-local\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --loop asyncio
```

Windows, terminal frontend:

```powershell
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8001"
npm.cmd run dev -- --hostname 127.0.0.1 --port 3001
```

Linux/macOS, terminal backend:

```bash
./.venv-local/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Linux/macOS, terminal frontend:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001 npm run dev -- --hostname 127.0.0.1 --port 3001
```

Abre `http://127.0.0.1:3001`; la documentación estará en `http://127.0.0.1:8001/docs`. Mantén el uso en localhost: el proyecto no incorpora autenticación.
