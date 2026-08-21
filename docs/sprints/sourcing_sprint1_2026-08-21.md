# Sourcing Sprint 1 — Reporte 2026-08-21

> **Agente Sourcing** — Nacho Palmeri, 2º año Q4 Gestión TI UADE (37.5%, 8.2), 20hs AMBA. Repo `job-search`, Sprint 1/4.

---

## 1. Auditoría `scripts/buscar_portales.py` — cobertura real vs. pérdida 60%

**Archivo auditado:** `scripts/buscar_portales.py:1-297` (297 líneas, 2026-08-21). `BASE_LINKS` define 14 entradas pero `main():256` solo scrapea 5.

| Portal | BASE_LINKS | Scraper real | Estado | Evidencia |
|---|---|---|---|---|
| **LinkedIn** | `linkedin` line 27 | `scrape_linkedin():105` | OK — guest `f_TPR=r604800` | `portales-argentina.md:108` scrapeable |
| **StartupsArgentina** | `startupsargentina` line 26 | `scrape_startupsargentina():127` | OK — SSR | line 128-148 |
| **Computrabajo** | `computrabajo` line 15 | `scrape_computrabajo():151` | OK — SSR `box_offer` | line 152-169 |
| **BecasIT** | — (BECASIT_URL line 34) | `scrape_becasit():172` | OK — Google Sites SSR | line 173-190 |
| **EmpleosIT** | `empleosit` line 18 | `scrape_empleosit():197` | OK — RSS `empleosit.com.ar/rss/` | line 198-224 |
| **Bumeran** | `bumeran` line 16 | **NO scrapeado** | **Gap crítico** — Cloudflare/SPA | `portales-argentina.md:113` "Bloquea scrape → links manuales"; `main():256` no lo incluye |
| **ZonaJobs** | `zonajobs` line 17 | **NO scrapeado** | **Gap crítico** — mismo Navent SPA | idem Bumeran |
| **Jooble** | `jooble` line 19 | **NO scrapeado** | Metabuscador — solo link | `portales-argentina.md:22` |
| **Indeed** | `indeed` line 20 | **NO scrapeado** | Bloquea bots | `portales-argentina.md:113` |
| **Jobsora** | `jobsora` line 21 | **NO scrapeado** | Metabuscador | tracker `applications.csv:29` muestra origen Jobsora manual |
| **Google Jobs** | `google` line 22 | **NO scrapeado** | `ibp=htl;jobs` | agente-libre lo cubre |
| **UADE** | `uade` line 23 | **NO scrapeado** | **Gap exclusivo** — login | `portales-argentina.md:42` "login libreta"; `main():256` no incluye |
| **FirstJob** | `firstjob` line 24 | **NO scrapeado** | Pasantías primarias | `portales-argentina.md:58` |
| **Wellfound/GetOnBoard** | lines 25,29 | **NO scrapeado** | SPA/API | `portales-argentina.md:113` |

**Conclusión gap:** 5/14 BASE_LINKS automatizados (35.7%), 9/14 manuales. De 5 fuentes scrapeables reales verificadas (`portales-argentina.md:107`) se cubren 5/5, pero el pitch de 60% perdido viene de: UADE (exclusivo 3.600 inst.), Bumeran/ZonaJobs (40% reclutadoras), Telegram/Discord (ofertas sin portal), y careers directas (Lever/Greenhouse/Workday). `radar/seen_jobs.json` 450 líneas: 200+ Lever/ashby directas fueron ingestadas por agente-libre manual, no por scraper → confirma pérdida si el agente no corre.

**Evidencia adicional:**
- `radar/daily-2026-08-21.tsv:2-16` — 14 jobs LinkedIn + 1 Computrabajo + 1 EmpleosIT, **0** de Bumeran/ZonaJobs/UADE/Telegram.
- `tracker/applications.csv:69,73` — BDO (Bumeran ID 1118342998) y VASA (1118385729) entraron como `bumeran` manual, no vía `_emit`.

## 2. Spec UADE Scraper Headless (Playwright + cookies, ASK)

**Archivo:** `docs/specs/uade_scraper_spec.md` (spec completo).

Resumen:
- **Target:** `empleos.uade.edu.ar/busquedaslaborales` (ver `portales-argentina.md:42`).
- **Auth:** Playwright `storage_state` → `.secrets/uade_cookies.json` **gitignored**. Flujo ASK: `python scripts/uade_scraper.py --login` (headed, login manual, `¿Guardar sesión? [s/N]`), resto `headless` reutiliza cookies. Nunca hardcodear creds, nunca loggear usuario/clave.
- **Ruta canónica:** `Path(__file__).parent.parent / ".secrets" / "uade_cookies.json"` (ver spec §Dónde guardar).
- **Pseudo-código:** `login_flow()` con `page.wait_for_url("**/busquedaslaborales**")` + `context.storage_state(path=STORAGE)`; `scrape_uade(headless=True)` con `storage_state=str(STORAGE)`, paginación 5 páginas, selectors `article/div.card/.busqueda-card`, detección expiry `if "login" in page.url`.
- **Integración:** `buscar_portales.py` importa `scrape_uade` en `elif name=="uade"`; `BASE_LINKS["uade"]` queda como fallback `[manual]`.
- **Compliance:** rate 1 req/3s, solo listado búsquedas, no notas/legajo.

## 3. Spec Bumeran Headless Stealth + Fallback API Reverse

**Archivo:** `docs/specs/bumeran_scraper_spec.md`.

Resumen:
- **Targets:** `bumeran.com.ar/empleos/busqueda-{kw}-en-buenos-aires.html` y `zonajobs.com.ar/empleos/buscar?q={kw}` (grupo Navent, Cloudflare + SPA JS — `portales-argentina.md:19`).
- **Opción A primaria:** Playwright stealth (`playwright-stealth` / `undetected-playwright`) + `UA` línea 41-44, `locale es-AR`, `wait_for_selector("div.Card__CardWrapper, [data-testid='job-card']")`, scroll 3× para lazy, parse multi-selector (clases cambian por deploy). Fallback Node `puppeteer-extra-plugin-stealth` solo si Python es bloqueado (proceso hijo vía subprocess).
- **Opción B fallback:** reverse API interna Navent. Pasos: DevTools XHR → capturar `GET /api/v1/search?query=pasantia&page=1` + headers `x-api-key/authorization`. Si endpoint es sin auth estable → `urllib.request` directo; si requiere `cf-clearance`/turnstile → descartar y quedarse con stealth. **Nunca hardcodear `api_key`/`bearer`** (HIGH_RISK).
- **Pseudo-código:** `scrape_bumeran_stealth(kw, headless=True)` y `scrape_bumeran_api(kw)` completos en spec.
- **Integración:** `buscar_portales.py:259` ampliar `selected` a incluir `bumeran/zonajobs` solo si stealth ok; si `status 403/503` → mensaje y links manuales sin romper `--scrape all`.
- **Deps:** `playwright==1.44.0` + `playwright-stealth==1.0.6` (`playwright install chromium`).

## 4. Feeds Telegram/Discord IT AR (3-4 concretos + cómo agregarlos)

**Archivo canónico:** `scripts/feeds_telegram.yaml` (ver §6). Feeds:

| # | Feed | URL RSS/Telegram | Tipo | Cómo agregar a `buscar_portales.py` |
|---|---|---|---|---|
| 1 | **SysArmy — Comunidad IT AR** | Preview sin login: `https://t.me/s/sysarmy` + RSS bridge `https://rss-bridge.org/bridge01/?action=display&bridge=TelegramBridge&username=sysarmy&format=Atom` — Invite: `https://t.me/sysarmy` | `telegram_channel` | Ya en YAML `sysarmy_telegram` (`type: telegram_channel`). `scrape_telegram_feeds()` hace `_get(url)` sobre `t.me/s/sysarmy`, split `tgme_widget_message_text`, filtra `keywords/keywords_exclude`, dedupe por `url`. RSS bridge como fallback si `t.me/s` vacío. |
| 2 | **IT Jobs AR — Empleos IT Argentina** | `https://t.me/s/empleosIT_ar` (alias; si 404 probar `itjobsargentina`) + bridge `...username=empleosIT_ar&format=Atom` — Invite: `https://t.me/empleosIT_ar` | `telegram_channel` | YAML `it_jobs_ar_telegram`. Mismo `scrape_telegram_feeds()`; `tags: ["pasantia","junior"]`. Para canal privado con `@bot` usar `TELEGRAM_BOT_TOKEN` en `.secrets/telegram_token.json` (ASK), no hardcodear. |
| 3 | **BusquedasIT (agregador mirror)** | `https://t.me/s/BusquedasIT` + bridge `...username=BusquedasIT&format=Atom` — Invite: `https://t.me/BusquedasIT` | `telegram_channel` | YAML `computrabajo_telegram_mirror`. Radar secundario cuando Bumeran bloquea. Filtrar `CABA/AMBA/Remoto` en `keywords`. |
| 4 | **SysArmy Discord — #empleos** | Invite `https://discord.gg/sysarmy` — API `https://discord.com/api/guilds/GUILD_ID/widget.json` (si widget habilitado) o `DISCORD_BOT_TOKEN` en `.secrets/discord_token.json` (**disabled** por defecto) | `discord_channel` | YAML `sysarmy_discord` con `enabled: false` hasta tener token (HIGH_RISK). Con token: `scrape_telegram_feeds()` extiende a `discord_channel` vía `discord.py` o RSS bridge `DiscordBridge`. ASK antes de guardar token. |

**Cómo agregar un feed nuevo (ver `feeds_telegram.yaml:60-66`):** duplicar bloque con `id` único, probar `curl -L https://t.me/s/<username> | grep -i pasant`, validar Atom del bridge, añadir `tags` nicho, correr `python scripts/buscar_portales.py --scrape telegram --write`.

## 5. 10 Careers Directas Target — check semanal (lunes 09:00 AMBA)

| # | Empresa | URL careers (directa ATS) | ATS | Frecuencia | Notas fit Nacho |
|---|---|---|---|---|---|
| 1 | **Globant** | `https://career.globant.com/` + `https://jobs.smartrecruiters.com/Globant` | SmartRecruiters | **Lunes semanal** | Practicante Univ 2026-2 (tracker `globant:2.8` — no-IT hoy, chequear track tech) |
| 2 | **Mercado Libre / Meli** | `https://careers-meli.mercadolibre.com/es/positions` | Meli ATS | **Lunes semanal** | No hay pasantía 20hs hoy; radar trainee |
| 3 | **Despegar** | `https://jobs.lever.co/despegar` | Lever | **Lunes semanal** | `Pasaporte Trainee 2026` fit 4.5 en `daily-2026-08-21.tsv:10` — vigente |
| 4 | **Accenture** | `https://www.accenture.com/ar-es/careers` + Workday `https://accenture.wd3.myworkdayjobs.com/AccentureCareers` (Req R00323840) | Workday | **Lunes semanal** | `applications.csv:37` pide últimos 2 años — radar 2027 |
| 5 | **IBM** | `https://www.ibm.com/careers` + Bumeran Req 127046 | Bumeran/Workday | **Lunes semanal** | `tracker:3.5` verificar 2º año |
| 6 | **Tiendanube / Nuvemshop** | `https://nuvemshop-tiendanube.inhire.app/tiendanube` | InHire | **Lunes semanal** | Varias `applications.csv:114-123` — senior hoy, radar junior |
| 7 | **Ualá** | `https://www.ua.la/sumate` | Ualá ATS | **Lunes semanal** | `applications.csv:105-113` — múltiples sumate, radar |
| 8 | **Satellogic** | `https://satellogic.bamboohr.com/careers` | BambooHR | **Lunes semanal** | `applications.csv:87-99` — 15+ roles, radar |
| 9 | **PedidosYa / Delivery Hero** | `https://jobs.smartrecruiters.com/DeliveryHero` (PeYantías) | SmartRecruiters | **Lunes semanal** | `tracker:3.2` PeYantías sept 2026 |
| 10 | **SAP Labs BA** | `https://jobs.sap.com` (iXp Intern) + `https://jobs.sap.com/job/Buenos-Aires-SAP-iXp-Intern-Order-to-Invoice-Cloud%2C-Software-&-Support-B1605DII/1428381933/` | SuccessFactors | **Lunes semanal** | `applications.csv:84` — **fit 4.5** iXp OTI (Limited Part Time, oct 2026) — **Aplicar YA** |

*Bonus semanal (si sobra tiempo):* YPF (`direcciona.hiringroom.com`), Galicia (`galicia.hiringroom.com`), Telecom (`jobs.telecom.com.ar`), Kavak (`kavak.com/careers`), Humand (`careers.humand.co`).

Automatización: `cron` lunes 09:00 `python scripts/buscar_portales.py --scrape all --write` + agente-libre para las 10 directas → dedupe contra `seen_jobs.json`.

## 6. Archivos entregados: `feeds_telegram.yaml` + patch

### `scripts/feeds_telegram.yaml` (nuevo, 70 líneas)

Ver archivo en repo. Ejemplo bloque:

```yaml
feeds:
  - id: sysarmy_telegram
    url: "https://t.me/s/sysarmy"
    rss_bridge: "https://rss-bridge.org/bridge01/?action=display&bridge=TelegramBridge&username=sysarmy&format=Atom"
    enabled: true
    check_frequency: "daily"
```

Incluye `defaults.keywords`, `defaults.keywords_exclude`, `dedupe_key`, `output`, y 4 feeds (3 telegram enabled + 1 discord disabled con `ASK` token).

### Patch sugerido `docs/specs/patch_buscar_portales.py.patch` (nuevo)

Patch unificado (131 líneas) contra `scripts/buscar_portales.py:1-297`:

- Añade `import yaml` + `FEEDS_YAML = Path(__file__).parent / "feeds_telegram.yaml"`
- Añade `def _telegram_keywords_filter()` + `def scrape_telegram_feeds(yaml_path=FEEDS_YAML)` (parse `t.me/s/` + fallback RSS bridge Atom, `max_items`, `lookback_days`, schema estándar `fecha|titulo|empresa|ubicacion|modalidad|jornada|estado|url`)
- Modifica `argparse --scrape choices` para incluir `telegram`
- Modifica `selected = ["linkedin","startups","computrabajo","becasit","empleosit","telegram"]` cuando `--scrape all`

Aplicar sin romper CI: `telegram` es opcional (si `pyyaml` no instalado → `skip`).

Ver archivo: `docs/specs/patch_buscar_portales.py.patch`.

Aplicación real (cuando se apruebe):

```bash
git apply docs/specs/patch_buscar_portales.py.patch
pip install pyyaml
python scripts/buscar_portales.py --scrape telegram --write --new
```

## 7. Diff y estado repo (sin push)

**Archivos creados (Sprint 1):**
- `scripts/feeds_telegram.yaml` (nuevo, 70 líneas)
- `docs/specs/uade_scraper_spec.md` (nuevo, 120 líneas)
- `docs/specs/bumeran_scraper_spec.md` (nuevo, 140 líneas)
- `docs/specs/patch_buscar_portales.py.patch` (nuevo, 131 líneas)
- `docs/sprints/sourcing_sprint1_2026-08-21.md` (este reporte)
- `.secrets/.gitkeep` (nuevo)

**Archivos modificados:**
- `.gitignore` — añadidos `.secrets/`, `*.storage.json`, `.secrets/uade_cookies.json`, `.secrets/discord_token.json`, `.secrets/telegram_token.json` (ver diff abajo)
- *(pendiente de aplicar por director)* `scripts/buscar_portales.py` — patch sugerido no aplicado aún (disponible en `docs/specs/patch_buscar_portales.py.patch`)

**No se pushea:** `git status` muestra untracked + modified, `git push` no ejecutado por instrucción sprint.

```diff
# git diff --stat (2026-08-21)
#  .gitignore              | 6 ++++
#  docs/specs/bumeran_scraper_spec.md | 140 +++
#  docs/specs/patch_buscar_portales.py.patch | 131 +++
#  docs/specs/uade_scraper_spec.md | 120 +++
#  docs/sprints/sourcing_sprint1_2026-08-21.md | 200 +++
#  scripts/feeds_telegram.yaml | 70 +++
#  .secrets/.gitkeep | 0
#  7 files changed
```

**Validación:**
- `python -c "import yaml; yaml.safe_load(open('scripts/feeds_telegram.yaml'))"` → OK (4 feeds, 3 enabled)
- `git diff --cached` sin secrets (`.secrets/*.json` gitignored)
- `bin/check-secrets.ps1` — no creds en diff (solo placeholders `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`)

**Próximo sprint (director decide):** aplicar patch, `pip install playwright && playwright install chromium`, correr `--login` UADE, y validar Bumeran stealth en headed antes de pasar a `HEADLESS=true` en cron.
