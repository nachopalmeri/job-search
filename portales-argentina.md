# Fuentes de búsqueda laboral — estado operativo

El catálogo completo y auditable de fuentes está en [`scripts/search_sources.json`](scripts/search_sources.json). Este archivo explica límites y evidencia; el flujo está en [`AGENTS.md`](AGENTS.md), el scraping en [`scripts/buscar_portales.py`](scripts/buscar_portales.py) y el estado diario en `radar/coverage-AAAA-MM-DD.json`. No mantener otra lista cerrada en prompts.

## Reglas de frescura

- Tope: **4 días de antigüedad** desde la publicación original en cada pasada.
- Orden de evidencia: ATS/página del empleador → anuncio original del portal → post del reclutador. El índice de búsqueda, “republicado” y la fecha de scrapeo no acreditan frescura.
- La ausencia de fecha no es fecha reciente. Marcar “no verificada” y excluir de matches activos.
- Verificar que siga abierta y que acepte candidaturas desde Argentina antes de puntuar.

## Fuentes automáticas (`--scrape all`)

| Fuente | Método | Límite conocido | Acción |
|---|---|---|---|
| LinkedIn Jobs | Página pública/guest; familias de consulta acotadas | Puede responder 429; no hay que insistir ni confiar solo en el filtro temporal | Cortar al primer 429 y contrastar candidatos con fecha original |
| Startups Argentina | Listado SSR | Algunas fichas/listados no informan fecha | Solo promover si la ficha original confirma publicación ≤4 días |
| YC Work at a Startup | Listados por familia/rol | Fecha y elegibilidad geográfica pueden faltar | Confirmar ubicación y ficha de empleo |
| a16z Speedrun | API pública | “Remote” puede limitarse a EE. UU.; revisar país y fecha | Filtrar por ubicación y publicación original |
| Cosign | Búsqueda pública del agregador | Fecha suele faltar; agregador mezcla empresas y mercados | No asumir frescura/Argentina por el título |
| Get on Board | API pública de búsqueda | Verificar país remoto y fecha del aviso | Abrir ficha antes de puntuar |
| Torre | API de oportunidades | Resultado abierto y lugar elegible deben confirmarse | Solo avisos vigentes con empresa identificable |
| Computrabajo | Listado público por término | Fechas relativas/localizadas | Normalizar fecha; abrir el aviso original |
| BecasIT | Listado público | La fecha puede no estar publicada | Confirmar vigencia y fecha; de lo contrario no promover |
| EmpleosIT | RSS público | Algunos ítems no incluyen fecha estructurada | No asignar la fecha del RSS como fecha de publicación |
| Jobicy | [API pública](https://jobicy.com/jobs-rss-feed) | El enlace gratuito lleva a Jobicy y el feed cubre hasta 7 días | Señal en `unverified`; verificar anuncio original, vigencia y Argentina |
| Himalayas | [API pública](https://himalayas.app/docs/remote-jobs-api) con filtro `country=AR` | Feed actualizado cada 24 h; restricciones de país/huso pueden cambiar | Señal en `unverified`; verificar anuncio original y condiciones |
| Remotive | [API pública](https://remotive.com/remote-jobs/api) | Publicación demorada 24 h; región remota puede ser ambigua | Señal en `unverified`; atribuir a Remotive y verificar empleador |
| Arbeitnow | [API pública](https://www.arbeitnow.com/blog/job-board-api) con foco europeo | Pocas oportunidades elegibles desde Argentina | Conservar solo remoto global explícito como señal `unverified` |
| CafeDev | Conector de lectura sobre `/v1/jobs`; documentación oficial no accesible desde la revisión | El contrato visible solo en una referencia secundaria; la lista actual no entrega fecha original ni descripción completa | Descubrimiento automático; mantener `unverified` hasta verificar fecha original, vigencia y elegibilidad desde Argentina |
| Silver.dev | Listado público de empresas y roles | 44 posiciones visibles en la consulta del 18/10; fichas y elegibilidad no revisadas en su totalidad | Exploración manual; registrar cobertura parcial y verificar cada ficha en el empleador/ATS |
| Greenhouse | API oficial por board token (`scripts/ats_boards.json`) | Es un feed por empresa; `updated_at` no equivale a primera publicación | Usar `first_published`, filtrar rol/ubicación y pasar por el filtro común de 4 días |
| Lever | API oficial por board token (`scripts/ats_boards.json`) | Es un feed por empresa; algunas fechas o ubicaciones pueden faltar | Usar `createdAt`, filtrar rol/ubicación y pasar por el filtro común de 4 días |
| Ashby | [Posting API pública](https://developers.ashbyhq.com/docs/public-job-posting-api) por board | No equivale a la API privada de gestión de empleos | Usar `publishedAt`, filtrar rol/ubicación y validar el aviso |

El filtro de frescura común corre antes de `seen_jobs` y antes de escribir el TSV; lo desconocido no se registra como oportunidad fresca.

## Fuentes manuales / autenticadas

| Fuente | Qué revisar | Límite |
|---|---|---|
| Portal de Empleos UADE | Carrera del usuario **y “sin carrera específica”**; número, fecha, requisitos, jornada y ubicación | Sesión de Nacho; solo lectura |
| Startup Jobs Argentina | Revisar ofertas nuevas y confirmar requisitos en la empresa/ATS | Fuente prioritaria de startups argentinas; fecha del agregador no basta |
| LinkedIn Jobs | Consultas separadas por soporte, sistemas, datos, trainee/intern y operaciones/tecnología | Si navegador/API limita, marcar cobertura parcial |
| X | Consultas simples y cortas en “Latest”; solo anuncio concreto con enlace oficial | Mucho ruido; tweets conversacionales no cuentan |
| Bumeran, ZonaJobs, Indeed, Jooble | Buscar en web/navegador cuando el scraper bloquee o falle | Metabuscadores y contenido repetido; validar en el empleador |
| Wellfound, FirstJob, Startup Jobs | Revisión en navegador cuando estén disponibles | Login/SPA o fecha ambigua; validar anuncio original |
| Vibe Coding Jobs, Vibehackers | Exploración de roles y startups | Agregadores/comunidad; no contar hasta confirmar empresa/ATS y Argentina |
| Páginas de carrera | ATS y carreras oficiales de empleadores relevantes | No recorrer catálogos ilimitados; priorizar fecha, Argentina y etapa inicial |

Si una fuente falla, probar una sola vez desde el navegador disponible. Registrar `sin resultados`, `parcial/error` o `no verificada`; no presentar un fallo como búsqueda completa.

Outlier, Alignerr, DataAnnotation y Prolific son plataformas de tareas de IA, no empleos con jornada garantizada. YC Events y Appgentina son networking/eventos. Todos tienen ID propio en el catálogo para que no desaparezcan del recorrido; no se mezclan con las vacantes. La prioridad de búsqueda es: Startups Argentina, luego part-time en Argentina, luego startups globales part-time que acepten Argentina, y finalmente otros matches fuertes. Full-time solo con match claramente alto o sueldo competitivo.

## ATS oficiales habilitados

Los ATS exponen APIs oficiales útiles para una lista curada de empleadores, sin instalar un scraper de terceros:

- **Greenhouse Job Board API:** `GET /v1/boards/{board_token}/jobs?content=true` publica trabajos y descripciones sin auth. [Docs](https://docs.greenhouse.io/job-board.html)
- **Lever Postings API:** devuelve avisos publicados por empresa; no ofrece búsqueda global de texto. [Docs oficiales en GitHub](https://github.com/lever/postings-api)
- **Ashby:** la [Posting API pública](https://developers.ashbyhq.com/docs/public-job-posting-api) expone avisos publicados por board; no usar la API privada `jobPosting.list`.

`--scrape all` consulta los tableros Greenhouse, Lever y Ashby definidos en `scripts/ats_boards.json`. El adaptador mantiene sólo avisos de áreas relacionadas y ubicaciones Argentina/LatAm/remotas; las fechas faltantes quedan fuera de matches frescos. Agregá un empleador al JSON solo después de verificar su board público y elegibilidad geográfica.

Greenhouse expone `first_published`; Lever expone `createdAt`; Ashby Posting API expone `publishedAt`. No usar `updated_at` para rejuvenecer una publicación. [Greenhouse](https://docs.greenhouse.io/job-board.html) · [Lever](https://github.com/lever/postings-api) · [Ashby](https://developers.ashbyhq.com/docs/public-job-posting-api). No se automatizan postulaciones.

## Fuentes apagadas o fuera de la pasada diaria

- Telegram: sin canales activos de calidad; no se consulta hasta verificar uno nuevo.
- Bumeran: manual/condicional a que la sesión o navegador funcione; no anunciar cero resultados por fallo.
- Wellfound: SPA con login; manual.
- Workana y Tecnoempleo no están en el catálogo actual. Las plataformas de tareas de IA sí se revisan en un carril separado por pedido explícito de Nacho.
