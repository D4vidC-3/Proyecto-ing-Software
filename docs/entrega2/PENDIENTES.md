# Pendientes y aportes del equipo

## Funcionalidad fuera del cierre de esta entrega

| Historia | Pendiente concreto |
|---|---|
| HU07 | Informe explícito de datos faltantes por vacante durante importación; hoy se conservan null y se muestran desconocidos en detalle/scoring |
| HU08 | Filtros que excluyan vacantes incompatibles y manejo explícito de preferencias no negociables; el ranking actual no excluye |
| HU-NF01 | Autenticación, autorización, aislamiento, retención de PDF y controles de despliegue; el MVP solo utiliza datos ficticios en localhost |
| HU-NF02 | Logging centralizado y sanitizado de errores, fallos de almacenamiento y errores inesperados; hoy se controlan casos conocidos y se trazan operaciones exitosas |

No es necesario ampliar estas historias para sostener el avance técnico propuesto de esta entrega. No se añadieron Magneto, scraping, postulaciones reales, mensajería, calendarios, cloud ni otros módulos avanzados.

## Limitaciones conocidas

- Un reintento de extracción devuelve el perfil existente; no hay acción separada para forzar reprocesamiento. Concurrencia extrema en extracción del mismo documento no está ensayada.
- Perfiles y vacantes contienen agregados JSON validados en la aplicación; no se implementa consulta SQL de cada habilidad o empleo individual.
- Las reglas de ciudad y cargo son simples; deben explicarse como tales. No hay embeddings ni equivalencias completas de habilidades.
- Un recordatorio por postulación se recalcula al cambiar estado. No tiene botón de completar, calendario ni entrega externa.
- Eliminación de perfil borra sus datos relacionales y trazas; conserva PDF local. Falta flujo de retención/borrado integral.
- No existe aislamiento de acceso. CORS no sustituye autenticación.
- Las pruebas del proveedor real y del navegador son comprobaciones manuales de esta sesión, no CI ni garantía de disponibilidad futura.
- Concurrencia, rollback de fallos de disco, accesibilidad y soporte móvil exhaustivo quedan sin validar.

## Evidencias académicas que solo puede aportar el equipo

Las plantillas Word/Excel se inspeccionaron sin modificarlas. No se inventaron personas, ceremonias, decisiones del PO, puntos ni capturas.

1. Acordar y registrar estimaciones propias y alcance con PO. La ponderación uniforme de MATRIZ_AVANCE es una propuesta técnica, no Planning Poker.
2. Completar Features con las 22 historias originales y su estado revisado. No usar los ejemplos genéricos de la plantilla como backlog de WORKINT.
3. Completar incertidumbre de negocio/técnica, tallas, velocidad real y cono de incertidumbre con datos del equipo; hoy no hay base suficiente para estimarlo.
4. Adoptar una Definition of Done y documentar revisión de código y aceptación. No afirmar porcentajes de cobertura, Sonar u OpenShift por aparecer en la plantilla.
5. Aportar retrospectiva del sprint anterior: técnica utilizada, participantes reales y acciones acordadas.
6. Aportar planificación del sprint, evidencia de reuniones, estimaciones y vínculo real de backlog/sprint de Azure DevOps si la materia lo requiere.
7. Completar Team Shape con integrantes y responsabilidades reales.
8. Incorporar los diagramas de ARQUITECTURA y las capturas reales de evidencias. Generar capturas adicionales durante la sustentación cuando corresponda.
9. Aportar conclusiones y lecciones del equipo, revisión del monitor y aceptación del PO.

## Git

Conservar rama `desarrollo/entrega-2`. Revisar primero los cambios que ya existían y los nuevos con `git diff` y `git status`. No se creó commit ni se publicó nada. Commits sugeridos para revisión: persistencia/perfiles; vacantes/matching; simulación/seguimiento; UI integrada; pruebas/documentación. No agregar `.env`, BD, uploads, entornos virtuales o node_modules.
