# Interview Prep Bank — índice (Sprint 4, 2026-08-21)

> Banco por empresa, Q/A versionadas, fuente Glassdoor atribuida. Honestidad: B1+/B2 sin certificar, RH124/CCNA no certificados, sin DApp/Web3 (ver `profile.md:41-44`). Git log = auditoría de versiones.

## Cómo usar

1. Antes de `tailor_cv.py --empresa X`, leer `interview_bank/<empresa>.md` para espejar evidencia real en bullets (no inventar).
2. En `tracker/applications.csv` col `notas` anotar `prep: interview_bank/<empresa>.md v1`.
3. Responder en voz alta 60-90s (HireVue: cámara, luz, STAR). Ver `cheat_sheet_*` en `extras/`.

## Cobertura 2026-08-21

| Empresa | Fit | Fuente Glassdoor 2026-08-21 | Estado | Version |
|---|---|---|---|---|
| **Wetcom** | 4.2 | Reporte candidatos Wetcom Jóvenes Talentos IT 2023-24 (Glassdoor requiere login 2026-08-21, verificado 403); validado contra `preguntas_tecnicas_wetcom.md:1` | curado | v1 2026-08-21 |
| **BASF** | 4.2 | `https://www.glassdoor.com.ar/Entrevista/BASF-Entrevista-E427.htm` — búsqueda pendiente manual (stub) | stub TODO | v0.1 |
| **TELUS Digital** | 4.7/4.3 | `https://www.glassdoor.com.ar/Entrevista/TELUS-Digital-Entrevista-E...` — AI Intern 2026 (stub) | stub TODO | v0.1 |
| **Central Puerto** | 4.5 | `https://www.glassdoor.com.ar/Entrevista/Central-Puerto-Entrevista-...` — Pasante Datos (stub) | stub TODO | v0.1 |
| **SAP iXp** | 4.5 | SAP Labs BA Order-to-Invoice (stub) | stub TODO | v0.1 |

Stubs: no se fabrican Q/A sin fuente. Completar con búsqueda logueada `site:glassdoor.com.ar "Empresa" Entrevista` y pegar URL fuente. Marcar `v1` solo con fuente verificada.

## Metodología Glassdoor honesta

- Glassdoor bloquea scrape anónimo (Cloudflare 403 sin login, verificado `curl glassdoor.com/Interview` 2026-08-21). No se burla `cf_clearance`, no se hardcodea session (HIGH_RISK).
- Flujo aprobado: login manual → copiar 3-5 Q públicas con atribución → pegar en `interview_bank/<empresa>.md` con URL + fecha.
- Futuro ASK: `.secrets/glassdoor.json` + Playwright `storage_state` como `uade_scraper_spec.md` (rate 1/10s). Hoy no implementado.

## Template

Ver `_template.md` para Q/A versionadas (STAR ES + EN).

## Próximos stubs priorizados (por fit)

Raizen 4.0, Adecco 4.4, Lotba 4.2, Kavak 3.5, JPMorgan 4.5 (HireVue ya en `cheat_sheet_hirevue_jpmorgan.md`).

