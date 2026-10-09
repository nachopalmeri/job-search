# Rezi Map: auditoría para la búsqueda laboral

Fecha: 2026-10-08 (Argentina).

Rezi declara más de 3 millones de avisos en su mapa, búsqueda por ubicación, puesto e industria, sin cuenta. Su documentación describe una reconstrucción periódica del índice, pero no garantiza fecha de publicación original en cada ficha. Referencias: https://www.rezi.ai/posts/rezi-map y https://www.rezi.ai/rezi-docs/job-search.

## Prueba de calidad

- Una ficha de Rezi etiquetada `Argentina` para Stryten Energy describe trabajo presencial en Salina, Kansas: https://map.rezi.ai/jobs/job/32252571/production-operator-at-stryten-energy.
- Buscar `Buenos Aires` por texto recupera avisos de otros países que solo mencionan la ciudad dentro del contenido, por ejemplo https://map.rezi.ai/jobs/job/39203936/senior-backend-engineer-vibesec-at-ox-security.
- Rezi muestra antigüedad relativa y remite al portal de la empresa para postular. Esa antigüedad no debe sustituir la fecha original del ATS o del empleador para la ventana de tres días.

## Decisión

Incorporar Rezi como fuente exploratoria de segunda capa. Para cada candidato exigir enlace del empleador, geografía real, requisitos completos, estado abierto y fecha original comprobable. Los avisos con fecha incierta van a revisión, sin entrar en la lista prioritaria de hasta tres días. No instalar ni consumir su MCP automáticamente.

## Hallazgo relacionado

El aviso IBM Data Intern de LinkedIn aparece reciente, mientras que un agregador conserva un aviso con el mismo texto fechado el 18/09/2026 y cerrado: https://careers.wct-fct.com/companies/ibm-2-ac1a9733-081a-4a8e-80d2-933d126d8ce3/jobs/93568167-data-intern-ibm-technology-expert-labs. Puede tratarse de una nueva vacante o una republicación. Hasta verificar el identificador y la fecha oficial, la prioridad de frescura queda pendiente.
