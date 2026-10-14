# Ejecución y guion de sustentación

Todos los cambios han sido verificados y consolidados en la ruta principal `/home/r347/Documentos/ChatGPT/WORKINT/Proyecto-ing-Software`. Ejecuta todos los procesos desde esta carpeta principal sin mezclar bases de datos ni procesos de copias auxiliares.

## Instalación y migración

Desde la raíz del repositorio:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.services.vacancies
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

En otra terminal, desde la raíz:

```bash
cd frontend
npm ci
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Abrir http://127.0.0.1:3000. API documentada: http://127.0.0.1:8000/docs. Requiere una versión de Node compatible con el Next.js instalado (en esta verificación: Node 22.23.1 y npm 10.9.8). Backend verificado con Python 3.14.7. `requirements.txt` fija las versiones encontradas/utilizadas; una instalación limpia debe comprobar disponibilidad de esas versiones en el registro.

La BD por defecto tiene ruta absoluta `backend/workint.db`, independiente del directorio desde el que se inicia Uvicorn. Puede cambiarse con `WORKINT_DATABASE_URL=sqlite:////ruta/absoluta/demo.db` en el entorno tanto para migraciones, ingesta como para API. No se crean tablas implícitamente al importar la aplicación: ejecutar Alembic es obligatorio.

La carga de vacantes es idempotente por ID. Ejecutarla dos veces mantiene 18 filas de vacantes; sí registra cada importación como un evento de ingesta.

## Configuración del proveedor

Para usar IA, configurar `backend/.env` local, excluido de Git:

```dotenv
GROQ_API_KEY=TU_CLAVE_LOCAL
GROQ_MODEL=openai/gpt-oss-20b
```

No pegar la clave en pantallas de sustentación, commits o logs. La casilla de consentimiento de la UI es obligatoria; no basta con subir el PDF. Si Groq está indisponible, utilizar Crear perfil manual. Se muestra `manual`, nunca IA simulada como si fuera real.

## Puertos alternativos usados en la verificación

Para conservar el servicio que ya ocupaba 8000:

```bash
# Terminal backend
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8001
# Terminal frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001 npm run dev -- --hostname 127.0.0.1 --port 3001
```

Para producción local (`npm run build` y `npm start`), `NEXT_PUBLIC_API_URL` debe estar definido al compilar. CORS acepta exclusivamente localhost y 127.0.0.1 en 3000/3001. No exponer la API en 0.0.0.0: no tiene autenticación.

## Recorrido demostrable

1. Seleccionar `CV_Prueba_Profile_Manager.pdf` de Descargas (documento ficticio). Cargar. Mostrar nombre y confirmación.
2. Antes de marcar consentimiento, señalar que Generar está deshabilitado. Marcar consentimiento y generar; mostrar origen groq y bloques estructurados. No ocultar errores de cuota/configuración; si ocurre uno, mostrar ruta manual.
3. Revisar faltantes. Para evidenciarlos, crear un perfil manual con solo nombre o quitar un campo y guardar. Los faltantes opcionales no impiden guardar. Un perfil con 0 años de experiencia no se considera desconocido.
4. Corregir un dato y preferencias; guardar. Mostrar origen groq_editado si procede y selector de perfiles persistidos.
5. Consultar recomendaciones. Mostrar listado real desde BD, fuente demo, requisitos y razón de cada componente. Señalar que desconocido aporta cero y que afinidad no es probabilidad de contratación.
6. Preparar postulación. Vista previa muestra candidato, empresa ficticia y efecto local. Cancelar primero y comprobar que no aparece una aplicación nueva.
7. Volver a preparar, marcar confirmación y ejecutar. Mostrar postulado, fecha, operation_id y tipo simulada. La misma vacante ya no permite otra postulación para ese candidato.
8. Cambiar a en_revision y después entrevista desde la UI de demo. Mostrar cambios cronológicos, próximo paso y recordatorio. Descartado cierra el proceso y el recordatorio; no admite regresar a un estado activo.
9. Mostrar panel con los cuatro agentes: perfil, vacantes, postulacion y seguimiento. Las razones provienen de eventos persistidos.
10. Detener solo el backend de la demo con Ctrl+C y volver a iniciarlo. Recargar la página y seleccionar el perfil guardado. Verificar mismo estado, evidencia y datos.
11. Crear un perfil manual desechable y eliminarlo con confirmación. Mostrar que desaparece del listado. No borrar el candidato principal si se necesitan sus evidencias para la sustentación.

No se envía una postulación real ni una notificación externa en ningún paso.

## Datos para la ruta manual

Nombre: Sofía Demo. Correo: sofia.demo@example.com. Ciudad: Medellín. Cargo: Desarrolladora Backend Python. Experiencia: 3 años. Habilidades: Python, FastAPI, PostgreSQL. Modalidad: remoto e híbrido. Salario: 4.500.000 a 5.500.000 COP. Otros campos pueden dejarse vacíos para mostrar detección de desconocidos. Son datos ficticios y su ingreso manual no acredita extracción de IA.
