# WORKINT — Profile Manager

**WORKINT** es una aplicación web desarrollada como MVP académico para el reto *Profile Manager* de Magneto, orientada a facilitar la gestión del perfil profesional y la búsqueda de empleo. Permite crear perfiles a partir de hojas de vida, recomendar vacantes mediante un algoritmo de afinidad explicable y simular postulaciones, contrataciones y seguimiento de procesos.

El sistema utiliza flujos **LangGraph**, inteligencia artificial opcional mediante **Groq** y una arquitectura cliente-servidor con persistencia local.

> **Estado del proyecto:** MVP funcional en desarrollo. La aplicación utiliza vacantes ficticias y postulaciones simuladas. No se conecta directamente con Magneto ni envía solicitudes reales a empleadores.

## 1. Características principales

### Gestión de perfiles profesionales
- Carga y validación de hojas de vida en formato PDF.
- Extracción de texto mediante `pypdf`.
- Extracción estructurada de información profesional mediante Groq y LangGraph, previa autorización del usuario.
- Creación, consulta, edición y eliminación de perfiles.
- Identificación de información faltante y preferencias laborales.
- Creación manual de perfiles cuando no se dispone del servicio de IA.

### Recomendación inteligente de vacantes
- Catálogo de vacantes ficticias almacenadas localmente.
- Normalización de habilidades y preferencias.
- Motor de recomendación determinista basado en cinco criterios:

| Criterio | Peso |
|---|---:|
| Habilidades | 45 % |
| Cargo objetivo | 20 % |
| Modalidad de trabajo | 15 % |
| Ubicación | 10 % |
| Aspiración salarial | 10 % |

- Clasificación de vacantes según su puntuación de afinidad.
- Explicación de los criterios utilizados en cada recomendación.

### Postulación y seguimiento
- Simulación de postulaciones con confirmación explícita.
- Prevención de postulaciones duplicadas dentro de una misma simulación.
- Administración de estados: `postulado`, `en_revision`, `entrevista`, `contratado` y `descartado`.
- Generación automática de próximos pasos y recordatorios locales.
- Registro de evidencias, operaciones y actividades.
- Bloqueo de nuevas postulaciones a vacantes ocupadas por una contratación simulada.
- Creación de nuevas simulaciones conservando el historial anterior.

### Flujos de procesamiento

El proyecto implementa cuatro componentes funcionales:

| Componente | Responsabilidad |
|---|---|
| Perfil | Extracción, validación y estructuración de información profesional. |
| Vacantes | Normalización de ofertas y generación de recomendaciones. |
| Postulación | Registro y control de postulaciones simuladas. |
| Seguimiento | Actualización de recordatorios, estados y próximos pasos. |

Estos componentes utilizan grafos LangGraph y reglas de negocio. No constituyen agentes autónomos con capacidad de ejecutar acciones externas sin intervención.

## 2. Requisitos previos y tecnologías

### Requisitos del entorno

| Herramienta | Requisito |
|---|---|
| Python | Python 3.10 o superior |
| Node.js | Node.js 20.9.0 o superior |
| npm | Compatible con la versión instalada de Node.js |
| Git | Recomendado para gestionar contribuciones |
| Groq API Key | Opcional; necesaria para extracción de perfiles mediante IA |

La aplicación utiliza SQLite, por lo que no necesita instalar un servidor de base de datos independiente.

### Stack tecnológico

| Capa | Tecnologías |
|---|---|
| Frontend | Next.js 16.4.0, React 19.3.0, TypeScript, Tailwind CSS 4 |
| Backend | Python, FastAPI, Uvicorn |
| Base de datos | SQLite, SQLAlchemy, Alembic |
| IA | Groq, LangChain Groq, LangGraph |
| Procesamiento PDF | pypdf |
| Validación | Pydantic |
| Pruebas | Pytest, HTTPX, Node.js Test Runner |
| Calidad | ESLint, TypeScript |

Las dependencias se encuentran definidas en:

- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `frontend/package.json`
- `frontend/package-lock.json`

## 3. Instalación y configuración

Los siguientes comandos están orientados a sistemas Linux y deben ejecutarse desde el directorio del proyecto extraído.

### Paso 1. Preparar el backend

Abrir una terminal desde la carpeta principal del proyecto:

```bash
cd Proyecto-ing-Software/backend
```

Crear un entorno virtual de Python:

```bash
python3 -m venv .venv
```

Instalar las dependencias:

```bash
./.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
```

### Paso 2. Configurar las variables de entorno

El repositorio contiene el archivo de ejemplo:

`backend/.env.escenarios.example`

Para trabajar con el conjunto de demostración de diez vacantes, configurar las siguientes variables en `backend/.env`:

```dotenv
WORKINT_SCENARIOS=1
WORKINT_DATABASE_URL=sqlite:///workint_escenarios.db
WORKINT_UPLOAD_DIR=uploads_escenarios
WORKINT_VACANCIES_PATH=app/data/vacancies_escenarios.json
```

Si el archivo `.env` ya existe, conservar sus valores y credenciales al modificarlo.

Para habilitar la extracción de perfiles con inteligencia artificial, agregar:

```dotenv
GROQ_API_KEY=TU_CLAVE_DE_GROQ
GROQ_MODEL=openai/gpt-oss-20b
```

La integración con Groq es opcional. Sin una clave válida, se puede utilizar la creación manual de perfiles.

**Importante:** no publicar el archivo `.env` ni las credenciales de acceso en repositorios.

### Paso 3. Preparar la base de datos

Desde `backend/`, ejecutar las migraciones:

```bash
./.venv/bin/python -m alembic upgrade head
```

Si se utiliza una base nueva y todavía no contiene las vacantes de demostración, importarlas mediante:

```bash
./.venv/bin/python -m app.services.vacancies
```

Para verificar la base de escenarios:

```bash
./.venv/bin/python -m app.scenarios
```

El proyecto dispone de dos configuraciones de datos:

| Base de datos | Contenido |
|---|---|
| `workint.db` | Datos históricos del MVP y catálogo de 18 vacantes ficticias. |
| `workint_escenarios.db` | Entorno independiente de demostración con 10 vacantes ficticias. |

La configuración de escenarios impide utilizar accidentalmente la base histórica como base activa.

### Paso 4. Ejecutar el backend

```bash
./.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Una vez iniciado, estarán disponibles:

- API: http://127.0.0.1:8000
- Documentación interactiva Swagger: http://127.0.0.1:8000/docs
- Comprobación del servidor: http://127.0.0.1:8000/health

### Paso 5. Preparar el frontend

Abrir una segunda terminal y acceder a:

```bash
cd Proyecto-ing-Software/frontend
```

Instalar las dependencias utilizando el archivo de bloqueo:

```bash
npm ci
```

### Paso 6. Ejecutar el frontend

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
```

Abrir la aplicación:

http://127.0.0.1:3000

El frontend se comunica con el backend mediante solicitudes HTTP a la API REST.

**Nota:** la API está preparada para demostración local. No incorpora autenticación multiusuario y no debe exponerse públicamente sin incorporar controles de seguridad adicionales.

## 4. Guía de uso rápido

### Verificar el funcionamiento

Con el backend ejecutándose, consultar su estado:

```bash
curl http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "WORKINT"
}
```

Consultar el catálogo de vacantes disponibles:

```bash
curl http://127.0.0.1:8000/api/v1/vacancies
```

### Crear un perfil desde la API

El siguiente ejemplo registra un perfil de prueba sin utilizar Groq:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Candidato Demo",
    "email": "demo@example.com",
    "location": "Medellín",
    "target_role": "Backend Python",
    "skills": ["Python", "FastAPI", "SQL"],
    "preferences": {
      "desired_roles": ["Backend Python"],
      "preferred_locations": ["Medellín"],
      "work_modes": ["remoto"]
    }
  }'
```

El servicio guarda el perfil en SQLite y devuelve su información, incluyendo el identificador del candidato.

### Recorrido desde la interfaz web

1. Acceder a `http://127.0.0.1:3000`.
2. Cargar una hoja de vida PDF o crear un perfil manual.
3. Si se utiliza IA, autorizar explícitamente el procesamiento del documento mediante Groq.
4. Revisar y guardar los datos profesionales y las preferencias laborales.
5. Consultar el catálogo y las recomendaciones.
6. Seleccionar una vacante y revisar la explicación de afinidad.
7. Confirmar una postulación simulada.
8. Consultar el estado, las evidencias, los recordatorios y la actividad registrada.
9. Actualizar el estado del proceso hasta `contratado` o `descartado`, según las transiciones permitidas.

Para ejecutar casos controlados, el repositorio incluye cinco hojas de vida ficticias en:

```text
docs/demo_escenarios/cvs/
```

La documentación completa de este recorrido se encuentra en [Guía de demostración](docs/demo_escenarios/GUIA_DEMOSTRACION.md).

### Endpoints principales

| Método | Endpoint | Función |
|---|---|---|
| GET | `/health` | Consultar el estado del backend. |
| POST | `/api/v1/cv/upload` | Cargar y validar un PDF. |
| POST | `/api/v1/cv/{document_id}/profile` | Generar un perfil estructurado con IA. |
| GET | `/api/v1/profiles` | Listar perfiles. |
| POST | `/api/v1/profiles` | Crear un perfil manual. |
| PUT | `/api/v1/profiles/{candidate_id}` | Actualizar un perfil. |
| DELETE | `/api/v1/profiles/{candidate_id}` | Eliminar un perfil. |
| GET | `/api/v1/vacancies` | Consultar vacantes. |
| GET | `/api/v1/profiles/{candidate_id}/recommendations` | Obtener recomendaciones. |
| POST | `/api/v1/applications` | Crear una postulación simulada. |
| PATCH | `/api/v1/applications/{application_id}` | Actualizar el estado de una postulación. |
| GET | `/api/v1/profiles/{candidate_id}/activity` | Consultar la actividad registrada. |
| GET | `/api/v1/profiles/{candidate_id}/reminders` | Consultar recordatorios. |
| GET | `/api/v1/simulations` | Consultar simulaciones. |
| POST | `/api/v1/simulations` | Iniciar una nueva simulación. |

## 5. Estructura del proyecto

El repositorio está organizado mediante una arquitectura cliente-servidor con separación entre interfaz, API, modelos, servicios y persistencia.

```text
Proyecto-ing-Software/
├── README.md
├── README_AVANCES.md
├── main.py
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   ├── .env.escenarios.example
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── profiles.py
│   │   │   └── workflow.py
│   │   │
│   │   ├── models/
│   │   │   ├── candidate_profile.py
│   │   │   ├── contracts.py
│   │   │   └── entities.py
│   │   │
│   │   ├── services/
│   │   │   ├── applications.py
│   │   │   ├── documents.py
│   │   │   ├── execution_trace.py
│   │   │   ├── matching.py
│   │   │   ├── pdf_extractor.py
│   │   │   ├── profile_extractor.py
│   │   │   ├── profile_gaps.py
│   │   │   ├── simulations.py
│   │   │   └── vacancies.py
│   │   │
│   │   ├── data/
│   │   │   ├── vacancies.json
│   │   │   └── vacancies_escenarios.json
│   │   │
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── repository.py
│   │   └── scenarios.py
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── scripts/
│   │   └── generate_scenario_cvs.py
│   │
│   └── tests/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx
│   │       ├── dashboard.tsx
│   │       ├── cv-workflow.ts
│   │       ├── profile-types.ts
│   │       ├── profile-validation.ts
│   │       ├── vacancy-presentation.ts
│   │       ├── layout.tsx
│   │       └── globals.css
│   │
│   ├── tests/
│   ├── package.json
│   ├── package-lock.json
│   └── next.config.ts
│
└── docs/
    ├── entrega2/
    │   ├── ALCANCE_MVP.md
    │   ├── ARQUITECTURA.md
    │   ├── DEMO.md
    │   ├── MATRIZ_AVANCE.md
    │   ├── PENDIENTES.md
    │   └── PRUEBAS.md
    │
    └── demo_escenarios/
        ├── cvs/
        ├── evidencias/
        ├── perfiles_ficticios.json
        └── GUIA_DEMOSTRACION.md
```

### Organización de la arquitectura

**Frontend:** construido con Next.js y React. Gestiona la interacción del candidato, formularios, visualización de vacantes y panel de seguimiento.

**Backend:** expone una API REST mediante FastAPI y coordina la lógica de negocio.

**Servicios:** implementan los flujos LangGraph, el procesamiento de documentos, el matching y las reglas de seguimiento.

**Persistencia:** utiliza SQLite con SQLAlchemy como ORM y Alembic para controlar las migraciones.

**Documentación:** almacena las decisiones arquitectónicas, el alcance académico, las pruebas y los escenarios de demostración.

El archivo `main.py` de la raíz corresponde a una prueba de concepto inicial y no es el punto de entrada de la aplicación web.

## 6. Contribución

Las contribuciones pueden enfocarse en correcciones, pruebas, mejoras de interfaz, seguridad, documentación y nuevas funcionalidades del MVP.

### Flujo recomendado

1. Revisar `README.md`, `README_AVANCES.md` y la documentación de arquitectura.
2. Crear una rama de trabajo para el cambio.
3. Implementar la funcionalidad respetando la separación de responsabilidades.
4. Incorporar o actualizar las pruebas correspondientes.
5. Ejecutar las verificaciones locales.
6. Documentar los cambios y su impacto.
7. Proponer los cambios mediante un Pull Request para revisión.

### Ejecutar las pruebas del backend

Desde `backend/`:

```bash
./.venv/bin/python -m pytest -q
```

Verificar la compilación de los módulos Python:

```bash
./.venv/bin/python -m compileall -q app main.py
```

### Ejecutar las verificaciones del frontend

Desde `frontend/`:

```bash
node --experimental-strip-types --test tests/*.test.mjs
```

Validar los tipos de TypeScript:

```bash
npx tsc --noEmit
```

Ejecutar el análisis estático:

```bash
npm run lint
```

Comprobar la compilación:

```bash
npm run build
```

### Criterios para aceptar cambios

- Mantener la compatibilidad con los contratos existentes de la API.
- Evitar la pérdida de perfiles, postulaciones y registros históricos.
- Incluir migraciones Alembic cuando se modifique el esquema de persistencia.
- Mantener separadas las bases históricas y de escenarios.
- No incluir claves API, datos personales reales ni archivos locales sensibles.
- Conservar las validaciones de consentimiento y confirmación de acciones.
- Actualizar las pruebas y la documentación cuando corresponda.

Para comprender las decisiones de implementación, consultar [Arquitectura del proyecto](docs/entrega2/ARQUITECTURA.md) y [Avances recientes](README_AVANCES.md).

---

**WORKINT — Profile Manager**

*Proyecto académico de Ingeniería de Software | Universidad EAFIT | 2026*
