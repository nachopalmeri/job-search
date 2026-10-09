# Fuentes de búsqueda laboral — estado operativo

Este archivo mantiene el inventario de fuentes. El flujo y las reglas están en [`AGENTS.md`](AGENTS.md); consultas y parsing, en [`scripts/buscar_portales.py`](scripts/buscar_portales.py). No mantener la misma lista detallada en varios prompts.

## Reglas de frescura

- Tope: **3 días de antigüedad** desde la publicación original en cada pasada.
- Orden de evidencia: ATS/página del empleador → anuncio original del portal → post del reclutador. El índice de búsqueda, “republicado” y la fecha de scrapeo no acreditan frescura.
- La ausencia de fecha no es fecha reciente. Marcar “no verificada” y excluir de matches activos.
- Verificar que siga abierta y que acepte candidaturas desde Argentina antes de puntuar.

## Fuentes automáticas (`--scrape all`)

| Fuente | Método | Límite conocido | Acción |
|---|---|---|---|
| LinkedIn Jobs | Página pública/guest; familias de consulta acotadas | Puede responder 429; no hay que insistir ni confiar solo en el filtro temporal | Cortar al primer 429 y contrastar candidatos con fecha original |
| Startups Argentina | Listado SSR | Algunas fichas/listados no informan fecha | Solo promover si la ficha original confirma publicación ≤3 días |
| YC Work at a Startup | Listados por familia/rol | Fecha y elegibilidad geográfica pueden faltar | Confirmar ubicación y ficha de empleo |
| a16z Speedrun | API pública | “Remote” puede limitarse a EE. UU.; revisar país y fecha | Filtrar por ubicación y publicación original |
| Cosign | Búsqueda pública del agregador | Fecha suele faltar; agregador mezcla empresas y mercados | No asumir frescura/Argentina por el título |
| Get on Board | API pública de búsqueda | Verificar país remoto y fecha del aviso | Abrir ficha antes de puntuar |
| Torre | API de oportunidades | Resultado abierto y lugar elegible deben confirmarse | Solo avisos vigentes con empresa identificable |
| Computrabajo | Listado público por término | Fechas relativas/localizadas | Normalizar fecha; abrir el aviso original |
| BecasIT | Listado público | La fecha puede no estar publicada | Confirmar vigencia y fecha; de lo contrario no promover |
| EmpleosIT | RSS público | Algunos ítems no incluyen fecha estructurada | No asignar la fecha del RSS como fecha de publicación |
| Greenhouse | API oficial por board token (`scripts/ats_boards.json`) | Es un feed por empresa; `updated_at` no equivale a primera publicación | Usar `first_published`, filtrar rol/ubicación y pasar por el filtro común de 3 días |
| Lever | API oficial por board token (`scripts/ats_boards.json`) | Es un feed por empresa; algunas fechas o ubicaciones pueden faltar | Usar `createdAt`, filtrar rol/ubicación y pasar por el filtro común de 3 días |

El filtro de frescura común corre antes de `seen_jobs` y antes de escribir el TSV; lo desconocido no se registra como oportunidad fresca.

## Fuentes manuales / autenticadas

| Fuente | Qué revisar | Límite |
|---|---|---|
| Portal de Empleos UADE | Carrera del usuario **y “sin carrera específica”**; número, fecha, requisitos, jornada y ubicación | Sesión de Nacho; solo lectura |
| LinkedIn Jobs | Consultas separadas por soporte, sistemas, datos, trainee/intern y operaciones/tecnología | Si navegador/API limita, marcar cobertura parcial |
| X | Consultas simples y cortas en “Latest”; solo anuncio concreto con enlace oficial | Mucho ruido; tweets conversacionales no cuentan |
| Bumeran, ZonaJobs, Indeed, Jooble | Buscar en web/navegador cuando el scraper bloquee o falle | Metabuscadores y contenido repetido; validar en el empleador |
| Wellfound, FirstJob | Revisión en navegador cuando estén disponibles | Login/SPA; no automatizar autenticación |
| Páginas de carrera | ATS y carreras oficiales de empleadores relevantes | No recorrer catálogos ilimitados; priorizar fecha, Argentina y etapa inicial |

Si una fuente falla, probar una sola vez desde el navegador disponible. Registrar `sin resultados`, `parcial/error` o `no verificada`; no presentar un fallo como búsqueda completa.

## ATS oficiales habilitados

Los ATS exponen APIs oficiales útiles para una lista curada de empleadores, sin instalar un scraper de terceros:

- **Greenhouse Job Board API:** `GET /v1/boards/{board_token}/jobs?content=true` publica trabajos y descripciones sin auth. [Docs](https://docs.greenhouse.io/job-board.html)
- **Lever Postings API:** devuelve avisos publicados por empresa; no ofrece búsqueda global de texto. [Docs oficiales en GitHub](https://github.com/lever/postings-api)
- **Ashby:** su API `jobPosting.list` requiere permiso `jobsRead`; para exponer avisos hay que limitarse a los publicados/listados. [Docs](https://developers.ashbyhq.com/reference/jobpostinglist)

`--scrape all` consulta el tablero Greenhouse de Sezzle y los tableros Lever de RYZ Labs, Emi Labs, Sauce, Aleph y Flex, definidos en `scripts/ats_boards.json`. Se verificó que cada identificador responde a su API pública. El adaptador mantiene sólo avisos de áreas relacionadas y ubicaciones Argentina/LatAm/remotas; las fechas faltantes quedan fuera de matches frescos. Agregá un empleador al JSON solo después de verificar su board público y elegibilidad geográfica.

Greenhouse expone `first_published` en su API; Lever expone `createdAt`. No usar `updated_at` para rejuvenecer una publicación. [Documentación Greenhouse](https://docs.greenhouse.io/job-board.html) · [Documentación Lever](https://github.com/lever/postings-api). Ashby queda diferido: su endpoint documentado requiere `jobsRead`, y no se encontró un endpoint público sin credenciales adecuado. No se scrapean endpoints privados ni se automatizan postulaciones.

## Fuentes apagadas o fuera de la pasada diaria

- Telegram: sin canales activos de calidad; no se consulta hasta verificar uno nuevo.
- Bumeran: manual/condicional a que la sesión o navegador funcione; no anunciar cero resultados por fallo.
- Wellfound: SPA con login; manual.
- Workana, Tecnoempleo y microtareas de anotación: no forman parte del objetivo de pasantía/junior IT en Argentina; incluir solo si Nacho amplía el alcance.
