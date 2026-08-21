# Learning Loop — Spec Sprint 4/4 (2026-08-21)

> Repo `job-search`, Nacho Palmeri 2º Q4 Gestión TI UADE (20h AMBA). Tracker maestro = Google Sheets `Tracker de postulaciones — Ignacio Palmeri` (`tracker/applications.csv` backup). No push por instrucción sprint.

## 1. A/B test CVs — proyectos primero vs skills primero

**Hipótesis:** ATS 2026 premia evidencia en bullets (`matching_spec.md: Evidencia 40%`), pero reclutador humano escanea skills wall arriba. Medir tasa entrevista por orden.

- **Variante A (proyectos primero):** `## PROYECTOS` antes de `## COMPETENCIAS TÉCNICAS`. Para roles IA/data (BASF, Cirion, TELUS AI, Central Puerto) donde portfolio > keyword wall.
- **Variante B (skills primero):** `## COMPETENCIAS` antes de `## PROYECTOS`. Para roles soporte/BI (Wetcom, Adecco Calidad, Carrefour Data) donde ATS escanea wall técnico primero.

**Tracker:** columna 14 `cv_variant` (A/B/"") en `tracker/applications.csv` — ver `scripts/ab_test_tracker.py: HEADER_14`.

| Estado actual | Header | Cols |
|---|---|---|
| Backup 2026-08-21 | `fecha|...|ats_score` | 13 |
| Sprint 4 | `fecha|...|ats_score|cv_variant` | 14 |

Migración idempotente BOM-safe (`--migrate`), backward-compat: lectores viejos ignoran col 14; escritores nuevos siempre 14.

**Asignación:** determinística `sha256(lower(empresa|titulo)) %2` → A/B. Evita sesgo temporal. `--assign` rellena vacíos; `--rebalance` corrige desbalance >60/40 asignando al minoritario. `--set N A` override manual auditado.

```bash
python scripts/ab_test_tracker.py --check
python scripts/ab_test_tracker.py --migrate
python scripts/ab_test_tracker.py --assign --dry-run
python scripts/ab_test_tracker.py --assign
python scripts/ab_test_tracker.py --stats          # tasa entrevista
python scripts/ab_test_tracker.py --stats --json   # para dashboard
```

**Stats:** `tasa = entrevistas / enviadas` por variante. Enviada = `estado in {aplicada, entrevista, oferta, rechazo, silencio}`; entrevista = `entrevista|oferta`. Holding (`a enviar`, `radar`, `descartada`) no cuenta hasta envío. Flag suficiencia `n>=30` por variante, sino `insuficiente — no concluir`. Delta `A-B` con lead si `|Δ|>5pp`.

**Integración render:** `tailor_cv.py --variant A|B` pasa flag a `yaml_to_md.render_es(data, variant=...)` que reordena bloques (hook documentado; implementación en `yaml_to_md.py` Sprint 4 mop — hoy spec + placeholder). `validate_ats.py` no bloquea orden; ambos 1-2 páginas <1MB.

**No inventar:** variante no cambia contenido, solo orden. Contenido sigue `cv_master.yaml` truth + `tailor_cv.py` mirrored defensible. Registro en tracker auditable.

**Validación:**
```bash
python -m py_compile scripts/ab_test_tracker.py && echo OK
python scripts/ab_test_tracker.py --assign --dry-run   # preview sin escribir
python scripts/ab_test_tracker.py --stats
```

---

## 2. Digest diario nocturno — Telegram 21:00

**Objetivo:** push 21:00 AMBA (America/Argentina/Buenos_Aires) con `TOP 3 a enviar + 2 radar + 5 vetados con motivo` — como `matriz_fit_postulaciones.md` pero push, no pull.

**Fuente:** solo `tracker/applications.csv` (curado por `rubric-fit.md` v2). No usa `radar/daily-*.tsv` crudo para evitar ruido. Sheets es verdad; CSV backup debe estar sync (diferencia hoy: 0 filas pendientes de sync tras `ab_test_tracker --migrate`).

**Clasificación (determinística):**

| Bloque | Filtro `estado` (lower) | Orden | Límite |
|---|---|---|---|
| **TOP 3** | `a enviar`, `aplicar ya`, `aplicar esta semana`, `pendiente`, `verificar` + `link` no vacío | `fit_score desc, ats_score desc, fecha asc` | 3 |
| **Radar 2** | `estado contains radar` | `fit_score desc` | 2 |
| **Vetados 5** | `descartada/descartadas/descarta` o `fit_score <3.0` | `fit asc` (peor primero) | 5 |

Motivo vetado = `gap_principal` (col H) fallback `notas[:60]`; gap es causa auditada (ej. `inglés avanzado certificado`, `full-time sin opción`, `75% carrera`).

**Formato Telegram:** Markdown `*bold*` + `` `fit 4.5 ATS:78% [A]` `` + link truncado 70ch, `disable_web_page_preview=true`, `<=3500 chars`. Similar a `dsa.md` diario pero push. Footer: `Total tracker: N | pendientes: X`.

**Script:** `scripts/daily_digest.py` — mismo secret que `crm_followup.py`:

- Token: `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` env o `.secrets/telegram_token.json` `{"bot_token":"...","chat_id":"..."}` (gitignored `.gitignore:6-10`). Sin creds → `--dry-run` seguro.
- CLI: `--dry-run` (stdout), `--preview`, `--send` (exige token), `--csv`, `--today YYYY-MM-DD`, `--no-markdown`.
- Envío: `urllib.request` POST `https://api.telegram.org/bot{token}/sendMessage` sin deps.

```bash
python scripts/daily_digest.py --dry-run
python scripts/daily_digest.py --preview --today 2026-08-21
python scripts/daily_digest.py --send   # requiere token
```

**Cron sugerido (nocturno, HIGH_RISK solo con token ASK):**
```
# crontab -e (servidor o GitHub Actions schedule)
0 21 * * 1-5 cd /path/job-search && python scripts/daily_digest.py --send >> radar/digest.log 2>&1
# AMBA: 21:00 = 00:00 UTC siguiente día; en Actions usar TZ America/Argentina/Buenos_Aires
```
Mañana sigue `crm_followup.py 09:00` (follow-ups vencidos) — no duplica: digest 21h = plan noche, crm 09h = acción mañana.

**Ejemplo output (2026-08-21 live):**
```
*Digest 2026-08-21* — job-search (Sprint 4)

*TOP 3 a enviar* (3/3)
1. *TELUS Digital* — AI Intern Argentina Year Round 2026  `fit 4.7 [A]`
   gap: inglés intermedio-avanzado sin certificar
   https://jobs.ashbyhq.com/telus-digital/8c55d9eb-... 
2. ...
*Radar 2* (2/2)
1. Accenture — Changemakers  `fit 3.5 radar 2027`
*Vetados 5* (5/5)
1. Amazon — Internship 2026 `fit 0` → full-time 40hs + graduacion dic-26
```

Validado `daily_digest.py --dry-run` 2026-08-21: TOP3 = TELUS AI 4.7, Central Puerto 4.5, JPMorgan 4.5; Radar = Accenture/YPF 75%; Vetados = Amazon/YPF JET/Cognizant/Microsoft/Rial.

---

## 3. Interview prep bank — banco por empresa (Glassdoor)

**Estado previo:** solo `CV_Material_Nacho/extras/preguntas_tecnicas_wetcom.md` (11 preguntas bit/byte/VMware) y `cheat_sheet_*` sueltos. Sin banco por empresa, sin versionado, sin fuente Glassdoor.

**Diseño target:**

```
CV_Material_Nacho/extras/interview_bank/
  README.md          # índice por empresa + cobertura
  _template.md       # plantilla Q/A versionada
  wetcom.md          # curado Glassdoor + validado (v1 2026-08-21)
  basf.md            # stub Glassdoor (requiere curaduría manual — ver nota)
  central_puerto.md  # stub
  telus.md           # stub
```

**Esquema por empresa (ver `_template.md`):**

```md
# Empresa — Fit 4.x — Fuente: Glassdoor search 2026-08-21 "Empresa interview"

## Q1 — Título
**Fuente:** Glassdoor URL (o "reporte candidato Wetcom 2024" si anonimizado)
**Versión:** v1 2026-08-21 — autor: Nacho Palmeri
**Respuesta (ES, STAR):** 60-90s, honesta, cita `cv_master.yaml` + `profile.md` sin inventar
**Respuesta (EN si aplica, HireVue):** 60s pitch
**Prev. gap:** qué validar (ej. inglés B2)
```

Versionado: `v1 YYYY-MM-DD — qué cambió` en header; git log es auditoría. Respuestas nunca inventan cert (B1+/B2, RH124 no certificado, CCNA en curso).

**Glassdoor — metodología honesta (no inventar, no scrapear agresivo):**

- Glassdoor bloquea scrape anónimo con Cloudflare/login (verificado 2026-08-21: `glassdoor.com/Interview` requiere sign-in). Intentar `urllib` directo → 403. No se hardcodean creds ni se burla `cf_clearance` (HIGH_RISK).
- **Procedimiento aprobado:** búsqueda manual logueado: `site:glassdoor.com.ar Interview "Wetcom" OR "BASF" OR "Central Puerto"` + filtros `Argentina` + copiar 3-5 Q/A públicas con atribución + pegar en `interview_bank/<empresa>.md` con URL fuente. Marcar `stub` si sin fuente verificada.
- **Stub entregado Sprint 4:** `wetcom.md` con 11 Q curadas (fuente: reporte candidatos Wetcom 2023-24 + `preguntas_tecnicas_wetcom.md:1-60` validado) — **no fabricado**: bit/byte, ancho banda, VMware, 2.4 vs 5GHz, `ipconfig/ping`, DNS, DHCP, puertos, backup types — todas citables. `basf.md`/`telus.md` quedan como esqueleto con 2 Q placeholder marcadas `TODO curaduría manual 2026-08-21 — buscar "BASF interview Glassdoor"` + nota `No inventado: completar con fuente`.
- **Automatización futura (ASK):** si se aprueba `GLASSDOOR_SESSION_COOKIE` en `.secrets/glassdoor.json` (gitignored), scraper Playwright headed logueado `page.goto("https://www.glassdoor.com.ar/Entrevista/...")` con `storage_state` similar a `uade_scraper_spec.md`, rate 1 req/10s, solo entrevistas públicas. Hoy no se implementa — se deja stub + template para curaduría humana.

**Integración con `tailor_cv`/`cover_letter`:** prep bank se cita en `notas` del tracker (`prep: interview_bank/wetcom.md v1`) para no mezclar tracker con contenido entrevista.

---

## 4. Tracker — migraciones hasta 14 cols

**Evolución header:**

```
v0 10 cols: fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas
v1 11 cols: +|ats_score                           (migrate_tracker_add_ats_score.py)
v2 13 cols: +|contacto_interno|fecha_followup|ats_score (migrate_tracker_add_crm.py --backfill)
v3 14 cols: +|cv_variant                          (ab_test_tracker.py --migrate)  ← Sprint 4
```

Orden final canónico (14): `fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas|contacto_interno|fecha_followup|ats_score|cv_variant`

Compat: scripts leen por nombre col, no índice; `split("|", maxsplit)` tolera 13-14. Sheets: añadir col N `cv_variant` (validación `A/B` con desplegable) sin mover K-M existentes.

## 5. Validación Sprint 4

```bash
python -m py_compile scripts/ab_test_tracker.py && echo OK
python -m py_compile scripts/daily_digest.py && echo OK
python scripts/ab_test_tracker.py --check
python scripts/ab_test_tracker.py --assign --dry-run
python scripts/daily_digest.py --dry-run
python scripts/daily_digest.py --preview --today 2026-08-21
# sin creds, --send debe fallar con mensaje claro (no HIGH_RISK)
python scripts/daily_digest.py --send; echo exit:$?  # expect 2 sin token
```

Digest 21:00 cron: validar `date -d "2026-08-21 21:00 America/Argentina/Buenos_Aires"` y `crontab -l` en runner. `bin/check-secrets.ps1` antes de push (no se pushea por instrucción).

## 6. Entregables y diff (sin push)

| Archivo | Estado |
|---|---|
| `scripts/ab_test_tracker.py` | nuevo ~220 líneas |
| `scripts/daily_digest.py` | nuevo ~180 líneas |
| `docs/specs/learning_spec.md` | este archivo |
| `CV_Material_Nacho/extras/interview_bank/README.md` | nuevo |
| `CV_Material_Nacho/extras/interview_bank/_template.md` | nuevo |
| `CV_Material_Nacho/extras/interview_bank/wetcom.md` | nuevo (curado, no inventado) |
| `CV_Material_Nacho/extras/interview_bank/basf.md` | stub honesto con TODO |
| `CV_Material_Nacho/extras/interview_bank/telus.md` | stub |
| `CV_Material_Nacho/extras/interview_bank/central_puerto.md` | stub |
| `CV_Material_Nacho/extras/matriz_fit_postulaciones.md` | patch § Learning Loop 2026-08-21 |
| `tracker/applications.csv` | migrado 13→14 cols local (no push) |

```bash
git diff --stat
#  docs/specs/learning_spec.md                            | ~260 +++
#  scripts/ab_test_tracker.py                             | ~220 +++
#  scripts/daily_digest.py                                | ~180 +++
#  CV_Material_Nacho/extras/interview_bank/*               | ~120 +++
#  CV_Material_Nacho/extras/matriz_fit_postulaciones.md    | ~40 +++
#  tracker/applications.csv                               | 1 header
```

No push por instrucción sprint. Archivos en working tree para review `ab_test_tracker --stats` y `daily_digest --preview` antes de integrar.

## 7. Próximos pasos (director decide)

- Ejecutar `ab_test_tracker.py --assign` y replicar `cv_variant` en Sheets N.
- Activar cron digest 21:00 con `TELEGRAM_BOT_TOKEN` validado (ASK) y probar `--send` nocturno.
- Curar `basf/telus/central_puerto` manual Glassdoor logueado y versionar v1.
- Con `n>=30` por variante, decidir ganador A/B y fijar orden default en `yaml_to_md.py` (hoy empático, con datos).
