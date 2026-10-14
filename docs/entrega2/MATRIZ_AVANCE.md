# Matriz de avance verificable

## Método y resultado

Base: las **22 historias originales** de GitHub, preservadas con sus criterios en `evidencias/backlog_github.json`. No hay puntos del equipo verificables. Se propone **peso uniforme 1 por historia**, incluyendo las no funcionales. Esta medida es cobertura de historias, no esfuerzo; no sustituye estimación ni aprobación del equipo. El denominador no se recortó al MVP.

Solo DONE técnica aporta 1. PARTIAL y TODO aportan 0, sin conceder porcentajes subjetivos a trabajo parcial. DONE significa que los criterios se implementaron, integraron, probaron y demostraron; **la aceptación formal del PO y del equipo sigue pendiente y no se inventa**.

**18 DONE técnicas / 22 × 100 = 81,82 % de cobertura funcional/técnica propuesta.** Cuatro PARTIAL, cero TODO entre las 22 historias: el backlog ya propone un MVP y permite datasets y simulación. No representa el 81,82 % de un producto comercial ni una aceptación académica certificada. Tampoco se afirma que el reto esté al 100 %. Si se consideran solo las 20 funcionales, el cálculo auxiliar es 18/20 = 90 %, pero se adopta el total conservador de 22.

La meta de 60 % se supera bajo esta ponderación transparente. El equipo debe aprobar o sustituir los pesos y ratificar las historias; hasta entonces el porcentaje académico aceptado no es verificable. No se desarrolló trabajo adicional fuera del recorrido para elevar el número.

| HU / fuente | Funcionalidad | Criterios originales | Estado | Pruebas/evidencia | Peso | Aporte al total |
|---|---|---|---|---|---:|---:|
| [HU01](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/1) | Cargar hoja de vida | El usuario puede seleccionar un archivo PDF.; El sistema valida que el archivo tenga un formato permitido.; El sistema informa si la carga fue exitosa o falló. | DONE técnica | test_upload; UI PDF | 1 | 4,54545 % |
| [HU02](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/2) | Estructurar información del CV | El sistema procesa el CV cargado.; Extrae información como educación, experiencia y habilidades.; La información obtenida se muestra de forma estructurada.; Si no puede procesar el CV, informa al usuario. | DONE técnica | test_profile_extractor, test_integrated_pdf_graph_to_followup; Groq real UI | 1 | 4,54545 % |
| [HU03](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/3) | Detectar información faltante | Identifica campos faltantes.; Indica cuáles deben completarse.; Permite agregar la información faltante. | DONE técnica | test_unknown_and_optional_gaps; perfil mínimo UI | 1 | 4,54545 % |
| [HU04](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/4) | Editar información del perfil | Permite modificar los datos extraídos.; Guarda los cambios realizados.; Muestra la información actualizada. | DONE técnica | test_profile_crud_and_new_connection; corrección UI | 1 | 4,54545 % |
| [HU05](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/5) | Registrar preferencias laborales | Permite registrar modalidad de trabajo.; Permite registrar ubicación y aspiración salarial.; Guarda las preferencias. | DONE técnica | test_profile_invalid_salary_and_ids; formulario UI | 1 | 4,54545 % |
| [HU06](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/6) | Obtener vacantes | Consume una fuente de vacantes de prueba.; Registra las vacantes obtenidas.; Maneja errores de la fuente. | DONE técnica | test_ingestion_idempotent_and_source_atomic | 1 | 4,54545 % |
| [HU07](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/7) | Normalizar vacantes | Estandariza los campos de las vacantes.; Conserva información relevante.; Identifica datos faltantes. | PARTIAL | test_normalization_and_missing_vacancy_data; pendiente: No hay informe específico de faltantes de la fuente | 1 | 0 % |
| [HU08](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/8) | Filtrar vacantes por preferencias | Utiliza las preferencias del candidato.; Excluye vacantes incompatibles.; Muestra los resultados filtrados. | PARTIAL | test_scoring_incompatible_and_unknown_salary; pendiente: Ordena por preferencias; no excluye incompatibles | 1 | 0 % |
| [HU09](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/9) | Recomendar vacantes | Compara perfil y vacantes.; Genera un nivel de afinidad.; Ordena las recomendaciones. | DONE técnica | test_ranking_and_persisted_trace | 1 | 4,54545 % |
| [HU10](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/10) | Explicar una recomendación | Muestra habilidades coincidentes.; Muestra criterios utilizados.; Presenta una explicación comprensible. | DONE técnica | test_scoring_exact_and_unknown; detalle UI | 1 | 4,54545 % |
| [HU11](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/11) | Consultar detalle de una vacante | Muestra descripción y requisitos.; Muestra empresa y modalidad cuando estén disponibles.; Permite iniciar la postulación. | DONE técnica | test_normalization_and_missing_vacancy_data; detalle UI | 1 | 4,54545 % |
| [HU12](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/12) | Confirmar postulación | Muestra la vacante seleccionada.; Solicita confirmación.; No ejecuta la acción si se cancela. | DONE técnica | test_requires_strict_confirmation; cancelar/confirmar UI | 1 | 4,54545 % |
| [HU13](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/13) | Simular postulación | Ejecuta una postulación simulada.; Registra fecha y vacante.; Informa el resultado al usuario. | DONE técnica | test_application_lifecycle_evidence_and_cascade; UI | 1 | 4,54545 % |
| [HU14](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/14) | Guardar evidencia de postulación | Guarda evidencia de cada acción.; Relaciona evidencia con una vacante.; Permite consultarla posteriormente. | DONE técnica | test_application_lifecycle_evidence_and_cascade; evidencia UI | 1 | 4,54545 % |
| [HU15](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/15) | Consultar estado de postulaciones | Muestra todas las postulaciones.; Indica el estado de cada una.; Permite distinguir procesos activos y finalizados. | DONE técnica | test_application_lifecycle_evidence_and_cascade; tablero UI | 1 | 4,54545 % |
| [HU16](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/16) | Generar próximos pasos | Analiza el estado de la postulación.; Genera una acción sugerida.; Muestra el próximo paso al usuario. | DONE técnica | test_reminder_and_errors; UI seguimiento | 1 | 4,54545 % |
| [HU17](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/17) | Generar recordatorios | Permite generar un recordatorio.; El recordatorio está relacionado con una postulación.; Muestra recordatorios pendientes. | DONE técnica | test_reminder_and_errors; recordatorios UI | 1 | 4,54545 % |
| [HU18](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/18) | Consultar historial de procesos | Registra cambios de estado.; Conserva fecha de cada cambio.; Muestra el historial cronológicamente. | DONE técnica | test_application_lifecycle_evidence_and_cascade; historial UI | 1 | 4,54545 % |
| [HU19](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/19) | Consultar acciones realizadas por los agentes | Registra las acciones de los agentes.; Identifica qué agente ejecutó cada acción.; Muestra fecha y resultado. | DONE técnica | test_integrated_pdf_graph_to_followup; panel UI | 1 | 4,54545 % |
| [HU20](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/20) | Consultar razón de una acción | Cada acción puede incluir una justificación.; La explicación es visible desde el panel.; La explicación identifica el agente responsable. | DONE técnica | test_ranking_and_persisted_trace; razones UI | 1 | 4,54545 % |
| [HU-NF01](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/21) | Protección de información del candidato | El sistema valida los datos recibidos.; La información sensible no se expone públicamente.; Los secretos y credenciales no se almacenan en el repositorio. | PARTIAL | test_cors_for_update_delete; consentimiento; .gitignore; pendiente: Sin autenticación/aislamiento; solo demo local | 1 | 0 % |
| [HU-NF02](https://github.com/D4vidC-3/Proyecto-ing-Software/issues/22) | Manejo de errores | Los errores son controlados.; El usuario recibe mensajes comprensibles.; Los errores técnicos relevantes quedan registrados. | PARTIAL | test_invalid_provider_output_is_controlled; test_failed_provider_manual_fallback; pendiente: Errores conocidos controlados; falta logging completo de fallos | 1 | 0 % |

Los aportes individuales se muestran redondeados; el total se calcula con 18/22, no sumando los textos redondeados.

## Cómo auditar

1. Comparar cada fila con el cuerpo original de la issue, sin cambiar sus criterios.
2. Ejecutar Pytest y los checks frontend de PRUEBAS.md.
3. Seguir DEMO.md y contrastar registros persistidos, no pantallas estáticas.
4. Revisar capturas reales, reinicio.json y el código referenciado en ARQUITECTURA.md.
5. Registrar aceptación real del PO; actualizar peso/estado y recalcular si el equipo obtiene estimaciones oficiales.
