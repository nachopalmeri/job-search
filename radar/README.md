# radar/

Carpeta de reportes diarios generada por la pasada de búsqueda (`--scrape all --write`).

## Archivos

- `daily-YYYY-MM-DD.tsv` — output unificado de los scrapers deterministas (LinkedIn, Startups Argentina, Computrabajo, BecasIT, EmpleosIT). Una línea por aviso, pipe-separated:
  `portal|fecha|titulo|empresa|ubicacion|modalidad|jornada|estado|url`
- `discoveries-YYYY-MM-DD.md` — reporte de descubrimientos del agente libre (web abierta: Google Empleos, bolsas con login/Cloudflare, páginas de carrera, radar de campañas).

## Reglas

- Cada pasada con `--write` **resetea** el TSV del día (sin duplicados entre corridas).
- El agente libre dedupea contra `tracker/applications.csv` y los `discoveries-*` previos.
- Google Empleos entra siempre en la pasada libre.