# Job search — Argentina

Toolkit personal para buscar pasantías y roles junior de IT/IA/datos, evaluar avisos con evidencia y preparar postulaciones sin enviarlas automáticamente.

## Fuente canónica

[`AGENTS.md`](AGENTS.md) define perfil operativo, criterios, límites y flujos. [`scripts/search_sources.json`](scripts/search_sources.json) es el catálogo completo de fuentes; [`portales-argentina.md`](portales-argentina.md) explica sus límites. [`profile.md`](profile.md) contiene el perfil verificable; [`rubric-fit.md`](rubric-fit.md), el puntaje.

## Pasada diaria

```powershell
python scripts\source_coverage.py --init
python scripts\buscar_portales.py --scrape all --write
python scripts\opportunity_pipeline.py
python scripts\cafedev_audit.py --enrich-live --detail-limit 30 --low-sample 10
```

El scraper consolida fuentes públicas y tableros Greenhouse, Lever y Ashby curados en `scripts/ats_boards.json`. Incluye CafeDev mediante consultas de texto amplias y paginadas con un límite local conservador; `first_seen_at` es indexación, no fecha de publicación. El listado se enriquece bajo demanda con `GET /v1/jobs/{id}` para hasta 30 candidatos, 10 de baja afinidad y las fichas históricas con resumen largo. Este detalle devuelve descripciones y requisitos, pero no siempre `published_at`, estado abierto/cerrado ni URL fuente directa; su `apply_url` puede seguir siendo un proxy de CafeDev. `radar/daily-YYYY-MM-DD.tsv` conserva avisos con fecha original verificable dentro de 4 días; `unverified-YYYY-MM-DD.tsv` reúne señales potenciales con fecha, empresa o elegibilidad pendientes. `opportunity_pipeline.py` genera `potential-review-YYYY-MM-DD.json` y `recommendations-YYYY-MM-DD.json` para separar investigación de avisos frescos. LinkedIn corta ante 429. UADE puede incorporarse desde el texto de la sesión abierta con `--uade-text <archivo>`; X requiere revisión manual. Cada aviso de UADE conserva su ID real, sin inventar enlaces individuales.

```powershell
python scripts\buscar_portales.py --scrape all --write --uade-text <archivo-de-texto>
python scripts\opportunity_rank.py --input <avisos-en-json>
```

`opportunity_rank.py` es un evaluador experimental: separa elegibilidad, compatibilidad y prioridad con razones visibles. Se aplica después de leer la descripción completa y confirmar requisitos obligatorios. Su puntaje no representa probabilidad de contratación. Rezi Map sirve para descubrir fuentes, pero las fechas y la elegibilidad geográfica se verifican en la empresa o ATS.

`--links` genera también búsquedas manuales de LinkedIn Posts y X con términos de reclutadores y equipos. Los filtros de Google/X sirven para descubrir publicaciones: la antigüedad se confirma en el post original antes de registrarla como aviso reciente.

El catálogo actual tiene 38 fuentes, incluida Silver.dev. `source_coverage.py --init` genera `radar/source-inventory.md` y `.json` con tipo, perfil, método, frecuencia, autenticación y la última cobertura conocida. UADE sin carrera específica, LinkedIn y X conservan su revisión diaria; comunidades, eventos y gigs con baja sensibilidad temporal se marcan `not_due` y se revisan semanalmente (lunes). `source_coverage.py --check` falla solo por fuentes debidas que quedaron pendientes, parciales o bloqueadas. Las tareas de IA y eventos siguen separadas de vacantes.

Para clasificar señales de startups, networking o ideas de contenido con evidencia explícita, usar `python scripts\strategic_intelligence.py --input <signals.json>`. El clasificador nunca convierte una ronda en contratación, ni envía mensajes o publica. Ver [flujo V2](docs/job-search-v2-workflow.md).

La automatización diaria autorizada usa este repositorio y cierra actualizando Notion con oportunidades verificadas, ordenadas por match, y la fecha original y la fecha de alta. Si no hubo hallazgos, registra la cobertura; si Notion no está accesible, informa el bloqueo. El Excel local sigue siendo el registro oficial de postulaciones.

## Seguimiento

- Excel oficial: `C:\Users\Nacho\Documents\Busqueda laboral\Postulaciones_Ignacio_Palmeri.xlsx`.
- CSV espejo versionado: `tracker/postulaciones.csv`.
- `scripts/tracker_add.py` mantiene ambos; no regenerar el Excel oficial desde el CSV.
- Notion es el resumen de lectura. El Excel sigue siendo la fuente de verdad.

## Estructura

- `scripts/buscar_portales.py`: adaptadores públicos y filtros de vigencia/dedupe; `scripts/ats_boards.json`: boards ATS validados.
- `scripts/search_sources.json` y `scripts/source_coverage.py`: catálogo y checklist diario de cobertura.
- `scripts/prompts/agente-libre.md`: prompt breve para cobertura manual y páginas oficiales.
- `scripts/tracker_add.py`: seguimiento de postulaciones.
- `CV_Material_Nacho/`: perfil maestro y CVs a medida.
- `radar/`: resultados diarios, estafas y reportes locales; no se suben los datos diarios.

No postular, enviar mensajes, crear cuentas ni compartir datos personales de Nacho desde los scripts o el navegador.
