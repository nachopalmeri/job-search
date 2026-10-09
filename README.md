# Job search — Argentina

Toolkit personal para buscar pasantías y roles junior de IT/IA/datos, evaluar avisos con evidencia y preparar postulaciones sin enviarlas automáticamente.

## Fuente canónica

[`AGENTS.md`](AGENTS.md) define perfil operativo, criterios, límites y flujos. [`portales-argentina.md`](portales-argentina.md) lista fuentes y límites actuales. [`profile.md`](profile.md) contiene el perfil verificable; [`rubric-fit.md`](rubric-fit.md), el puntaje.

## Pasada diaria

```powershell
D:\Dev\wenv\Scripts\python.exe scripts\buscar_portales.py --scrape all --write
```

El scraper consolida fuentes públicas y tableros Greenhouse y Lever curados en `scripts/ats_boards.json`. `radar/daily-YYYY-MM-DD.tsv` conserva avisos con fecha original verificable dentro de 3 días. `radar/unverified-YYYY-MM-DD.tsv` reúne señales con fecha del portal, ubicación o primera publicación sin confirmar; no equivale a recomendaciones. LinkedIn corta ante 429. UADE puede incorporarse desde el texto de la sesión abierta con `--uade-text <archivo>`; X requiere revisión manual. Cada aviso de UADE conserva su ID real, sin inventar enlaces individuales.

```powershell
D:\Dev\wenv\Scripts\python.exe scripts\buscar_portales.py --scrape all --write --uade-text <archivo-de-texto>
D:\Dev\wenv\Scripts\python.exe scripts\opportunity_rank.py --input <avisos-en-json>
```

`opportunity_rank.py` es un evaluador experimental: separa elegibilidad, compatibilidad y prioridad con razones visibles. Se aplica después de leer la descripción completa y confirmar requisitos obligatorios. Su puntaje no representa probabilidad de contratación. Rezi Map sirve para descubrir fuentes, pero las fechas y la elegibilidad geográfica se verifican en la empresa o ATS.

`--links` genera también búsquedas manuales de LinkedIn Posts y X con términos de reclutadores y equipos. Los filtros de Google/X sirven para descubrir publicaciones: la antigüedad se confirma en el post original antes de registrarla como aviso reciente.

## Seguimiento

- Excel oficial: `C:\Users\Nacho\Documents\Busqueda laboral\Postulaciones_Ignacio_Palmeri.xlsx`.
- CSV espejo versionado: `tracker/postulaciones.csv`.
- `scripts/tracker_add.py` mantiene ambos; no regenerar el Excel oficial desde el CSV.
- Notion es el resumen de lectura. El Excel sigue siendo la fuente de verdad.

## Estructura

- `scripts/buscar_portales.py`: adaptadores públicos y filtros de vigencia/dedupe; `scripts/ats_boards.json`: boards ATS validados.
- `scripts/prompts/agente-libre.md`: prompt breve para cobertura manual y páginas oficiales.
- `scripts/tracker_add.py`: seguimiento de postulaciones.
- `CV_Material_Nacho/`: perfil maestro y CVs a medida.
- `radar/`: resultados diarios, estafas y reportes locales; no se suben los datos diarios.

No postular, enviar mensajes, crear cuentas ni compartir datos personales de Nacho desde los scripts o el navegador.
