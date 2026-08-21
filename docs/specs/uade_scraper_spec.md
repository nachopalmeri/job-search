# UADE Scraper — Spec Headless (Playwright + Cookies)

**Fecha:** 2026-08-21 | **Sprint:** 1/4 Sourcing | **Owner:** Pisculichi Labs — Nacho Palmeri  
**Target:** `https://www.empleos.uade.edu.ar/busquedaslaborales` (login con libreta UADE)  
**Problema:** 3.600+ instituciones / 1.800 convenios pasantía-año exclusivos UADE. Sin scraper se pierde ~30% del funnel pasantías Ley 26.427 (evidencia: `portales-argentina.md:41-47`, `discoveries-2026-08-06.md` muestra 0 ofertas portal UADE en scraping actual).

## Principios

- **Nunca hardcodear creds.** Usuario hace login manual una vez; el scraper reutiliza storage_state (cookies+localStorage).
- **ASK para guardar sesión.** Todo guardado en `.secrets/` (gitignored). No en repo, no en .env commiteado.
- **Headless real pero operable.** Playwright Chromium headless con guard de 2FA si UADE lo pide.
- **Respeto ToS UADE:** rate 1 req/3s, solo listado de búsquedas laborales (no scraping de legajo/notas). Uso personal del alumno — no redistribuir CVs de terceros.

## Arquitectura

```
[login manual headed] → .secrets/uade_cookies.json (storage_state)
                            ↓
scripts/uade_scraper.py --headless → radar/daily-*.tsv + seen_jobs.json
        ↓                             ↓
   Playwright (chromium)         _emit("uade", jobs, tsv_path)
   · storage_state=.secrets/uade_cookies.json
   · goto /busquedaslaborales
   · waitForSelector("article|div.card")
   · paginación (ver §Paginación)
```

## Dónde guardar cookies

| Archivo | Contenido | Git |
|---|---|---|
| `.secrets/uade_cookies.json` | `storage_state` de Playwright (`cookies`, `origins[].localStorage`) | **gitignored** |
| `.secrets/.gitkeep` | placeholder | tracked |
| `.gitignore` entry | `.secrets/` + `uade_cookies.json` + `*.storage.json` | tracked |

> **Ruta canónica:** `Path(__file__).resolve().parent.parent / ".secrets" / "uade_cookies.json"` — no usar `radar/` ni `tracker/`.

`.gitignore` a añadir:

```
.secrets/
*.storage.json
.secrets/uade_cookies.json
```

## Flujo ASK (obligatorio)

1. **Primer setup (headed):** `python scripts/uade_scraper.py --login` abre Chromium headed en `https://www.empleos.uade.edu.ar/login`.
2. Usuario loguea con libreta + clave UADE. Script espera `page.wait_for_url("**/busquedaslaborales**")`.
3. **ASK:** `¿Guardamos la sesión en .secrets/uade_cookies.json? [s/N]` → si `s`, `context.storage_state(path=SECRETS/"uade_cookies.json")`.
4. Próximas corridas usan `--headless` sin creds. Si 401/expiry → mensaje `Sesión expirada — correr --login de nuevo` (no reintentar con creds guardadas).
5. **Nunca** loggear usuario/clave. Solo loggear `storage_state saved: .secrets/uade_cookies.json (N cookies, exp YYYY-MM-DD)`.

## Pseudo-código (Python 3.11, playwright==1.44+)

```python
# scripts/uade_scraper.py
from pathlib import Path
from playwright.sync_api import sync_playwright
import re, json
from datetime import date

SECRETS = Path(__file__).resolve().parent.parent / ".secrets"
STORAGE = SECRETS / "uade_cookies.json"
UADE_URL = "https://www.empleos.uade.edu.ar/busquedaslaborales"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0"

def login_flow():
    SECRETS.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=UA)
        page = context.new_page()
        page.goto("https://www.empleos.uade.edu.ar/login", wait_until="domcontentloaded")
        print(">> Logueate manualmente en la ventana. Se esperará a /busquedaslaborales")
        page.wait_for_url("**/busquedaslaborales**", timeout=120_000)
        page.wait_for_selector("article, div.card, .busqueda-card", timeout=15_000)
        if input("¿Guardar sesión en .secrets/uade_cookies.json? [s/N] ").lower() == "s":
            context.storage_state(path=str(STORAGE))
            print(f"[OK] storage_state → {STORAGE} ({len(context.cookies())} cookies)")
        browser.close()

def scrape_uade(headless=True):
    if not STORAGE.exists():
        raise SystemExit("Sin sesión: correr `python scripts/uade_scraper.py --login` primero (ASK)")
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=UA, storage_state=str(STORAGE))
        page = context.new_page()
        # Guard: sesión expirada
        page.goto(UADE_URL, wait_until="domcontentloaded", timeout=30_000)
        if "login" in page.url.lower():
            raise SystemExit("Sesión expirada o inválida — re-login con --login")
        page.wait_for_selector("article, div.card, .busqueda-card", timeout=15_000)
        # Paginación: UADE usa ?page=N o scroll infinito → detectar ambos
        for _ in range(5):  # tope 5 páginas
            html = page.content()
            # parse: título, empresa, modalidad, jornada, ubicación, url detalle
            for block in re.split(r'class="busqueda-card|card-oferta', html)[1:]:
                title = re.search(r'<h[2-3][^>]*>(.*?)</h[2-3]>', block)
                # ...mapear a schema buscar_portales.py...
                jobs.append({...})
            # next
            nxt = page.locator('a[rel="next"], button:has-text("Siguiente")')
            if nxt.count() == 0 or not nxt.first.is_enabled():
                break
            nxt.first.click()
            page.wait_for_load_state("networkidle", timeout=10_000)
        browser.close()
    return jobs

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", action="store_true", help="login manual headed y guardar storage_state (ASK)")
    ap.add_argument("--headless", action="store_true", default=True)
    args = ap.parse_args()
    if args.login:
        login_flow()
    else:
        jobs = scrape_uade(headless=True)
        print(f"[UADE] {len(jobs)} ofertas")
```

## Schema de salida (compat `buscar_portales.py`)

```python
{
  "fecha": "2026-08-21", "titulo": "Pasante de Datos",
  "empresa": "Central Puerto", "ubicacion": "CABA (híbrido)",
  "modalidad": "Híbrido", "jornada": "Part-time 20hs",
  "estado": "Vigente", "url": "https://www.empleos.uade.edu.ar/busquedaslaborales/12345",
}
```

Emite vía `_emit("uade", jobs, tsv_path)` → `radar/daily-YYYY-MM-DD.tsv` y `seen_jobs.json` (clave = url sin query).

## Integración con `buscar_portales.py`

```python
# en buscar_portales.py
elif name == "uade":
    try:
        from scripts.uade_scraper import scrape_uade
        jobs = scrape_uade(headless=True)
    except SystemExit as e:
        print(f"[uade] {e}"); jobs=[]
```

Y en `BASE_LINKS["uade"]` mantener fallback link manual si no hay sesión: `https://www.empleos.uade.edu.ar/busquedaslaborales [manual]`.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| UADE cambia DOM/anti-bot | Selectores fallback + `page.wait_for_selector` con 3 variantes + screenshot debug `.secrets/uade_debug.png` (no commitear) |
| Expiry sesión cada 30-60 días | Detectar redirect a /login → mensaje claro + no loop |
| 2FA SMS | `--login` headed permite al usuario pasar 2FA manualmente |
| Rate limit | `page.wait_for_timeout(3000)` entre páginas + `networkidle` |

## Verificación

```bash
python scripts/uade_scraper.py --login   # headed, login manual, ASK guardar
python scripts/uade_scraper.py           # headless dry-run → consola
python scripts/buscar_portales.py --scrape uade --write --new  # integra radar + seen
# Esperado: radar/daily-YYYY-MM-DD.tsv con líneas portal=uade, sin creds en git status
```

CI: no corre UADE (requiere secrets). Local only.

## No hacer

- Guardar usuario/clave en `.env`, `config.json` o código.
- Pushear `.secrets/` o `storage_state`.
- Scrapear perfil/notas del alumno.
