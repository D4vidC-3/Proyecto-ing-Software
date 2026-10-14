# Alcance del MVP local

WORKINT conserva el extractor existente e integra un recorrido local de CV a seguimiento. Incluye PDF, consentimiento explícito para Groq, perfil persistido y editable, ruta manual identificada, 18 vacantes ficticias, recomendaciones explicables, confirmación de postulación simulada, evidencia, estados, próximos pasos y actividad de agentes.

La entrada manual no se presenta como extracción de IA. Los perfiles incompletos pueden guardarse: vacío es desconocido; se muestran campos recomendados y opcionales, sin inventar información. Cero años de experiencia es un dato válido.

La API permite crear, leer, actualizar y eliminar perfiles y sus registros dependientes. La interfaz realiza esas operaciones. El PDF original permanece en `backend/uploads/`; la eliminación del perfil no es una eliminación integral del CV. La interfaz lo advierte antes de borrar. No hay política automática de retención.

## Fronteras deliberadas

- Dataset local curado, no scraping ni acceso a Magneto.
- Todas las postulaciones son simuladas. No se envían correos ni formularios externos.
- Seguimiento por reglas y recordatorios visibles dentro de la app. No hay scheduler, calendario ni notificaciones externas.
- El scoring ordena todas las vacantes; no implementa exclusión estricta por preferencias (HU08 parcial).
- Vacantes con datos desconocidos conservan null; falta un informe completo de faltantes de la fuente (HU07 parcial).
- Sin cuentas, autenticación, permisos ni separación multiusuario. Solo localhost y datos ficticios.
- Sin producción, cloud, microservicios, embeddings, proveedores alternativos o analítica avanzada.

## Criterio de cierre técnico

Historia DONE técnica: todos sus criterios de GitHub están cubiertos en la implementación local, integrada y demostrable, con pruebas apropiadas y evidencia. PARTIAL: algún criterio no está cubierto; no suma al numerador. TODO: sin implementación útil. La aceptación del PO y del equipo no se presume.

Se conserva el denominador completo de 22 historias. Ver `MATRIZ_AVANCE.md`. No se utiliza número de archivos, clases o líneas como medida de avance.
