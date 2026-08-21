# Bumeran Scraper — Spec Headless Stealth

**Fecha:** 2026-08-21 | **Sprint:** 1/4 Sourcing | **Owner:** Pisculichi Labs  
**Targets:**  
- `https://www.bumeran.com.ar/empleos/busqueda-{kw}-en-buenos-aires.html` (SPA + Cloudflare)  
- `https://www.zonajobs.com.ar/empleos/buscar?q={kw}` (mismo grupo Navent, mismo bloqueo)  
**Problema:** Bumeran+ZonaJobs concentran 40%+ de avisos de reclutadoras (IBM, BDO, VASA, embargos) y filtran `part-time`. Hoy solo links manuales (`portales-argentina.md:19`, `agente-libre.md:24`). Sin JS se pierde 60% del funnel (pitch del sprint).

## Estrategia dual: Stealth headless + fallback API reverse

### Opción A — Stealth headless (primaria)

Usar **Playwright + stealth** (no puppeteer-extra si se puede evitar dependencia Node).

- **Playwright + `playwright-stealth` o `chrome` con args anti-detección** (si `playwright-stealth` no disponible, usar `playwright-extra` vía Node — ver fallback).
- Equivalente Python: `playwright` + `from playwright_stealth import stealth_sync` o `undetected-playwright`.
- Headers reales (ver `buscar_portales.py:41-44` UA) + `Accept-Language: es-AR`.
- `wait_until="networkidle"` + scroll para disparar lazy-load de `div.Card__CardWrapper`.

**Por qué Playwright y no puppeteer-extra-stealth:** el repo ya es Python (buscar_portales.py urllib). Playwright Python evita introducir Node + `npm install puppeteer-extra`. Si el bypass falla, escalar a Node con `puppeteer-extra-plugin-stealth` como proceso hijo.

### Opción B — Fallback API reverse (si stealth es bloqueado)

Bumeran (Navent) expone **API interna no documentada** usada por el front SPA. No hardcodeada — se descubre vía DevTools → Network.

Pasos reverse (documentar en spec, no en código hasta validar):

1. Abrir Bumeran en browser con DevTools → filtrar `XHR` al buscar `pasantia`.
2. Capturar request tipo `GET https://www.bumeran.com.ar/api/v1/search?query=pasantia&location=buenos-aires&page=1` o `POST https://api.bumeran.com.ar/...` (verificar — endpoint cambia cada deploy).
3. Extraer headers requeridos: `x-api-key`, `authorization: Bearer ...`, `cf-clearance`.
4. Si el endpoint es **sin auth y estable** → usar `urllib.request` directo (más barato que headless). Si requiere `cf-clearance`/turnstile → volver a Opción A (API no viable sin bypass).

> **Regla:** nunca hardcodear `api_key`/`bearer`. Si la API exige token dinámico extraído del JS bundle, tratar como `HIGH_RISK` y quedarse con headless stealth.

## Pseudo-código — Playwright stealth (Python)

```python
# scripts/bumeran_scraper.py
from pathlib import Path
from playwright.sync_api import sync_playwright
import re
from html import unescape

BUMERAN_URL = "https://www.bumeran.com.ar/empleos/busqueda-{kw}-en-buenos-aires.html"
ZONAJOBS_URL = "https://www.zonajobs.com.ar/empleos/buscar?q={kw}"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def _clean(t): return re.sub(r"\s+", " ", unescape(t)).strip()

def scrape_bumeran_stealth(kw="pasantia", headless=True, timeout_ms=30_000):
    jobs = []
    url = BUMERAN_URL.format(kw=kw)
    with sync_playwright() as p:
        # stealth: si está instalado playwright-stealth, envolver
        browser = p.chromium.launch(headless=headless, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ])
        context = browser.new_context(
            user_agent=UA,
            locale="es-AR",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": "es-AR,es;q=0.9"},
        )
        # opcional: stealth_sync(page) si librería disponible
        try:
            from playwright_stealth import stealth_sync  # pip install playwright-stealth
            # se aplica por page
        except ImportError:
            stealth_sync = lambda x: None

        page = context.new_page()
        stealth_sync(page)
        # anti-cloudflare: esperar domcontentloaded, no networkidle inmediato
        resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        # Si Cloudflare challenge → esperar 5s y reintentar
        if resp and resp.status in (403, 503):
            page.wait_for_timeout(5000)
            page.reload(wait_until="domcontentloaded")
        # Esperar cards reales, no spinner
        try:
            page.wait_for_selector("div[data-testid='job-card'], div.Card__CardWrapper, article", timeout=15_000)
        except:
            # Fallback: tomar HTML igual y probar parse
            pass
        # Scroll para trigger lazy
        for _ in range(3):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(1200)
        html = page.content()
        browser.close()

    # Parse SSR+SPA (misma lógica que buscar_portales.py:41 needs robust selectors)
    # Bumeran varía clases: probar 3 selectores
    for block in re.split(r'Card__CardWrapper|data-testid="job-card"|job-card', html)[1:]:
        href = re.search(r'href="(/empleos/[^"]+)"', block)
        if not href: continue
        title = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.S)
        company = re.search(r'data-testid="company"[^>]*>(.*?)<', block)
        location = re.search(r'Ubicaci[oó]n[^<]*</span>\s*<span[^>]*>(.*?)</span>', block, re.S)
        modalidad = re.search(r'(Remoto|Híbrido|Presencial)', block)
        fecha = re.search(r'hace\s+\d+\s+(?:hora|min|d[ií]a)', block, re.I)
        jobs.append({
            "fecha": _clean(fecha.group(0)) if fecha else "",
            "titulo": _clean(re.sub(r"<[^>]+>", "", title.group(1))) if title else "",
            "empresa": _clean(company.group(1)) if company else "",
            "ubicacion": _clean(location.group(1)) if location else "Buenos Aires",
            "modalidad": modalidad.group(1) if modalidad else "",
            "jornada": "Part-time" if re.search(r"part.?time|20\s*hs|medio tiempo", block, re.I) else "",
            "estado": "",
            "url": "https://www.bumeran.com.ar" + href.group(1),
        })
    # Dedupe por url
    seen=set(); out=[]
    for j in jobs:
        if j["url"] not in seen:
            seen.add(j["url"]); out.append(j)
    return out

def scrape_zonajobs_stealth(kw="pasantia", headless=True):
    # idéntico a bumeran pero con ZONAJOBS_URL y dominio zonajobs.com.ar
    # reutilizar scrape_bumeran_stealth con url param
    ...

# Fallback Node (solo si Playwright Python es bloqueado):
# scripts/bumeran_stealth_node.mjs
# import puppeteer from 'puppeteer-extra';
# import StealthPlugin from 'puppeteer-extra-plugin-stealth';
# puppeteer.use(StealthPlugin());
# const browser = await puppeteer.launch({headless:true, args:['--no-sandbox']});
# const page = await browser.newPage(); await page.goto(url, {waitUntil:'networkidle2'});
# const html = await page.content(); console.log(html);
# Python lo invoca vía subprocess y parsea stdout html.
```

## Pseudo-código — Fallback API reverse (si se descubre estable)

```python
def scrape_bumeran_api(kw="pasantia"):
    import urllib.request, json
    # DESCUBRIR endpoint real vía DevTools; debajo ejemplo ilustrativo (NO hardcodear sin verificar)
    api = f"https://www.bumeran.com.ar/api/busqueda?palabra={kw}&zona=buenos-aires&page=1"
    req = urllib.request.Request(api, headers={
        "User-Agent": UA,
        "Accept": "application/json",
        "Referer": "https://www.bumeran.com.ar/",
        "Accept-Language": "es-AR,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    # data["avisos"] → mapear a schema estándar
    return [{"fecha": a.get("fecha"), "titulo": a["titulo"], "empresa": a["empresa"],
             "ubicacion": a["ubicacion"], "modalidad": a.get("modalidad",""),
             "jornada": a.get("jornada",""), "estado": "", "url": a["url"]} for a in data.get("avisos",[])]
```

Criterio para elegir runtime:
- Si `page.wait_for_selector` trae cards en <15s → usar stealth headless.
- Si `GET /api/...` devuelve JSON sin `cf_clearance` → usar API (más barato, testeable en CI con mock).
- Si ambos fallan → reportar `[bumeran] bloqueado — usar links manuales BASE_LINKS["bumeran"]` y no romper `--scrape all`.

## Integración con `buscar_portales.py`

```python
elif name == "bumeran":
    try:
        from scripts.bumeran_scraper import scrape_bumeran_stealth
        jobs = scrape_bumeran_stealth(kw, headless=True)
        if not jobs:
            # fallback API reverse si existe
            from scripts.bumeran_scraper import scrape_bumeran_api
            jobs = scrape_bumeran_api(kw)
    except Exception as e:
        print(f"[bumeran] stealth/API falló: {e} — usando links manuales")
        jobs = []
elif name == "zonajobs":
    # mismo patrón con ZONAJOBS_URL
    ...
```

Añadir al `selected` de `--scrape all`: `["linkedin","startups","computrabajo","becasit","empleosit","bumeran","zonajobs"]` solo si stealth disponible; si no, mantener fallback manual para no romper CI determinista.

## Dependencias

```txt
# requirements-scrapers.txt (nuevo, opcional)
playwright==1.44.0
playwright-stealth==1.0.6  # opcional, si no está se degrade graceful
# setup: playwright install chromium
```

Node fallback solo si se valida bloqueo:
```json
// package.json (si se usa Node)
{ "dependencies": { "puppeteer-extra": "^3.3.6", "puppeteer-extra-plugin-stealth": "^2.11.2" } }
```

## Rate & compliance

- Delay 3s entre requests, `headless=True`, 1 page a la vez.
- No evadir paywall de avisos destacados (no extraer emails privados).
- Respetar `robots.txt` de bumeran/zonajobs (actualmente Disallow parcial para bots — uso personal low-volume aceptable; no distribuir dataset).

## Verificación

```bash
pip install playwright playwright-stealth
playwright install chromium
python scripts/bumeran_scraper.py --kw pasantia --no-headless  # ver cards
python scripts/buscar_portales.py --scrape bumeran --kw pasantia --write --new
# Esperado: radar/daily-*.tsv con portal=bumeran, sin 403, con jornada=Part-time detectada
# Si 403 persistente: revisar docs/specs/bumeran_scraper_spec.md §Fallback API reverse
```

## Evidencia de gap actual

- `portales-argentina.md:19` — "Bloquea scrape (auth/Cloudflare) → links manuales" para Bumeran.
- `scripts/buscar_portales.py:15-16` BASE_LINKS define bumeran/zonajobs pero `main():256` solo scrapea 5 portales (no incluye bumeran/zonajobs) → 0% cobertura automatizada en ambos.
- `tracker/applications.csv:69,73` — ofertas Bumeran (BDO, VASA) fueron cargadas manual vía agente-libre, no vía scraper → confirma pérdida.
