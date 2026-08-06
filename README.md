# job-search — Búsqueda diaria de pasantías IT (Argentina)

Porting local del framework `MadsLorentzen/ai-job-search` adaptado al stack de Nacho (OpenCode + scripts Python + portales argentinos). El original usa Claude Code + LaTeX + portales daneses; acá: skills OpenCode + scripts + portales AR, manteniendo el núcleo (perfil, rubric de fit, drafter-reviewer, tracker).

## Estructura

```
job-search/
├── profile.md                  # perfil profesional (fuente de verdad)
├── rubric-fit.md               # rúbrica de evaluación (5 dimensiones + deal-breakers)
├── portales-argentina.md       # portales investigados (ago 2026) + notas técnicas
├── scripts/
│   ├── buscar_portales.py      # scraper unificado (5 fuentes scrapeables)
│   └── prompts/
│       └── agente-libre.md     # prompt canónico del agente de búsqueda web libre
├── radar/
│   ├── daily-YYYY-MM-DD.tsv    # output de los scrapers (determinista)
│   └── discoveries-YYYY-MM-DD.md  # reporte del agente libre (web abierta)
└── tracker/
    └── applications.csv        # seguimiento de postulaciones (backup; maestro = Sheets)
```

La skill de OpenCode que orquesta todo: `.opencode/skills/job-search/SKILL.md`.

## Rutina diaria (1 comando + agentes)

1. Scrapers deterministas: `python scripts/buscar_portales.py --scrape all --write` → `radar/daily-*.tsv` (LinkedIn, Startups Argentina, Computrabajo, BecasIT, EmpleosIT).
2. Agente libre (web abierta): Google Empleos + bolsas manuales (Bumerán, ZonaJobs, Jooble, Indeed, Wellfound, FirstJob, Get on Board) + páginas de carrera de empresas + radar de campañas → `radar/discoveries-*.md`.
3. Merge + dedupe + fit (`rubric-fit.md`) → tracker (Sheets maestro + CSV backup) → reporte top 3-5.

## Estado actual (tracker, 5/8/2026)

**Tracker maestro:** el **Google Sheets del usuario** ("Tracker de postulaciones — Ignacio Palmeri"). El `tracker/applications.csv` local es backup/estado del skill, no la fuente de verdad. Al registrar una postulación: primero al Sheets, después (opcional) al CSV.

- **Wetcom Jóvenes Talentos IT 17ª** — fit 4.2 — Fátima contactó por WhatsApp; llamada pendiente.
- **BecasIT Pasante Analista IA / Python** — fit 4.5/4.2 — falta monto para enviar email.
- **IBM Req 127046** — fit 3.5 — verificar requisito "últimos años".
- **TELUS AI Intern / SWE Intern** — vigencia confirmada 5/8 vía LinkedIn guest.
- **Danone Programa de Pasantías** — publicado 4/8, incluye Sistemas; aplicar YA.

## Fuentes scrapeables (verificadas 5/8/2026)

LinkedIn (guest semana/internship), Startups Argentina (SSR), Computrabajo (SSR), BecasIT (Google Sites SSR), EmpleosIT (RSS). Detalle técnico en `portales-argentina.md`.

## Diferencias con el original (decisiones tomadas)

| Original (ai-job-search) | Acá |
|---|---|
| Claude Code + comandos `.claude/commands/` | OpenCode + skill `.opencode/skills/job-search/` |
| LaTeX (lualatex/xelatex) | CVs existentes DOCX/PDF reportlab (ya ATS-validados) |
| Portales daneses (Jobindex, Jobnet...) | Portales argentinos (BecasIT, Computrabajo, Bumeran, EmpleosIT...) |
| Scrapers CLI en Bun | Script Python unificado (--scrape all) para portales scrapeables + agente libre para la web abierta |
| Enfoque volumen (69 aplicaciones) | Enfoque curado: pocas postulaciones de calidad + contacto humano |
