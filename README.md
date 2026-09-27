# job-search — Búsqueda diaria de pasantías IT (Argentina)

Porting local del framework `MadsLorentzen/ai-job-search` adaptado al stack de Nacho (OpenCode + scripts Python + portales argentinos). El original usa Claude Code + LaTeX + portales daneses; acá: skills OpenCode + scripts + portales AR, manteniendo el núcleo (perfil, rubric de fit, drafter-reviewer, tracker).

## Estructura

```
job-search/
├── AGENTS.md                   # FLUJO CANÓNICO para agentes (OpenCode, Claude Code, etc.)
├── profile.md                  # perfil profesional (fuente de verdad)
├── rubric-fit.md               # rúbrica de evaluación (5 dimensiones + deal-breakers)
├── portales-argentina.md       # portales investigados (ago 2026) + notas técnicas
├── scripts/
│   ├── buscar_portales.py      # scraper unificado (11 fuentes: LinkedIn, Cosign, Startups AR, YC, Speedrun, Get on Board, Torre, Computrabajo, BecasIT, EmpleosIT, Bumeran)
│   ├── tracker_xlsx.py         # genera el Excel de seguimiento desde tracker/*.csv
│   ├── tracker_add.py          # agrega/actualiza postulaciones en el Excel de Nacho (+ espejo CSV, backup, follow-ups)
│   └── prompts/
│       └── agente-libre.md     # prompt canónico del agente de búsqueda web libre
├── radar/
│   ├── daily-YYYY-MM-DD.tsv    # output de los scrapers (determinista)
│   └── discoveries-YYYY-MM-DD.md  # reporte del agente libre (web abierta)
└── tracker/
    ├── postulaciones.csv       # espejo de la Google Sheet (una fila por postulación)
    ├── contactos.csv           # recruiters, referidos y networking
    └── applications.csv        # legacy: radar + postulaciones hasta 26/09/2026
```

**Fuente canónica del flujo: [`AGENTS.md`](AGENTS.md)** (reglas, mapa de rutas, MCPs y los 5 flujos). En OpenCode se usa con `/busqueda`, `/cv`, `/postule` y `/seguimiento` (comandos en `~/.config/opencode/command/`) y la skill global `job-search` (`~/.agents/skills/job-search/SKILL.md`); ambos solo apuntan a `AGENTS.md`. Claude Code y cualquier otro agente leen el mismo archivo.

## Rutina diaria (1 comando + agentes)

1. Scrapers deterministas: `python scripts/buscar_portales.py --scrape all --write` → `radar/daily-*.tsv` (LinkedIn, Cosign, Startups Argentina, YC, Speedrun, Get on Board, Torre, Computrabajo, BecasIT, EmpleosIT; Bumeran/UADE dan WARN sin sesión). Telegram está apagado: sin canales vivos (26/09/2026).
2. Pasada con el navegador de Nacho (Claude in Chrome, solo lectura): portal UADE por carrera y búsqueda "Más reciente" en X. Ver `scripts/prompts/agente-libre.md`.
3. Agente libre (web abierta): Google Empleos + bolsas manuales (ZonaJobs, Jooble, Indeed, Wellfound, FirstJob) + páginas de carrera + radar de campañas + outbound → `radar/discoveries-*.md`.
4. Merge + dedupe + fit (`rubric-fit.md`) → CV personalizado (inglés siempre B1) → Nacho postula → fila nueva en la Google Sheet (y en `tracker/postulaciones.csv`).

## Estado actual (tracker, 5/8/2026)

**Tracker maestro (desde 26/09/2026):** la Google Sheet `Postulaciones_Ignacio_Palmeri` (Drive, carpeta Búsqueda Laboral), con panel, seguimiento automático a 3/14 días, contactos y CVs. Es un archivo de Nacho: no depende de Claude. `tracker/postulaciones.csv` es su espejo y `python scripts/tracker_xlsx.py` regenera el Excel. La planilla vieja ("Tracker de postulaciones — Ignacio Palmeri") queda como respaldo.

- **Wetcom Jóvenes Talentos IT 17ª** — fit 4.2 — Fátima contactó por WhatsApp; llamada pendiente.
- **BecasIT Pasante Analista IA / Python** — fit 4.5/4.2 — falta monto para enviar email.
- **IBM Req 127046** — fit 3.5 — verificar requisito "últimos años".
- **TELUS AI Intern / SWE Intern** — vigencia confirmada 5/8 vía LinkedIn guest.
- **Danone Programa de Pasantías** — publicado 4/8, incluye Sistemas; aplicar YA.

## Fuentes scrapeables (verificadas 26/09/2026)

LinkedIn (guest), Cosign (API Convex), Startups Argentina (SSR), YC Work at a Startup (SSR), a16z Speedrun (API), Get on Board (API v0), Torre (API POST), Computrabajo (SSR), BecasIT (Google Sites SSR), EmpleosIT (RSS). Pasada del 26/09: LinkedIn 326, Cosign 40, Startups AR 82, YC 3, Speedrun 15, Get on Board 74, Torre 30. Detalle técnico en `portales-argentina.md`.

## Diferencias con el original (decisiones tomadas)

| Original (ai-job-search) | Acá |
|---|---|
| Claude Code + comandos `.claude/commands/` | OpenCode + skill `.opencode/skills/job-search/` |
| LaTeX (lualatex/xelatex) | CVs existentes DOCX/PDF reportlab (ya ATS-validados) |
| Portales daneses (Jobindex, Jobnet...) | Portales argentinos (BecasIT, Computrabajo, Bumeran, EmpleosIT...) |
| Scrapers CLI en Bun | Script Python unificado (--scrape all) para portales scrapeables + agente libre para la web abierta |
| Enfoque volumen (69 aplicaciones) | Enfoque curado: pocas postulaciones de calidad + contacto humano |
