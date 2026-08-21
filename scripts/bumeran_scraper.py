"""Bumeran/ZonaJobs scraper stealth — Navent SPA (Cloudflare).

Estado: esqueleto funcional. Usa playwright stealth si está disponible, sino fallback a requests.
No hardcodear api keys. Si Cloudflare bloquea, devuelve [] y loguea WARN sin romper --scrape all.

Uso:
  python scripts/bumeran_scraper.py --kw "pasantia" --headed  # debug
  python scripts/bumeran_scraper.py                            # headless Bumeran+ZonaJobs

Integrado en buscar_portales.py via scrape_bumeran_stealth() si se importa este módulo.
"""
import re
import sys
from pathlib import Path
from html import unescape

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
}

def _clean(text):
    return re.sub(r"\s+", " ", unescape(text)).strip()

def _get_requests(url):
    import urllib.request
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def scrape_bumeran_stealth(kw="pasantia", headed=False):
    jobs = []
    url = f"https://www.bumeran.com.ar/empleos/busqueda-{kw}-en-buenos-aires.html"
    # Intentar playwright stealth si está
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not headed, args=["--disable-blink-features=AutomationControlled"])
            ctx = browser.new_context(locale="es-AR", user_agent=UA["User-Agent"])
            page = ctx.new_page()
            # Stealth mínimo: ocultar webdriver
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector("div.Card__CardWrapper, [data-testid='job-card'], article", timeout=15000)
            except Exception as e:
                print(f"WARN Bumeran stealth: no selector ({e}) — fallback requests", file=sys.stderr)
                browser.close()
                raise
            html = page.content()
            browser.close()
    except Exception as e:
        # Fallback requests directo (puede dar 403 Cloudflare)
        try:
            html = _get_requests(url)
        except Exception as e2:
            print(f"WARN Bumeran requests fallback falló: {e2}", file=sys.stderr)
            return jobs

    # Parse cards — múltiples selectores por cambio de layout
    for block in re.split(r'Card__CardWrapper|data-testid=.job-card.|<article', html)[1:]:
        title = _clean(re.search(r'>([^<]{5,80})</a>', block).group(1)) if re.search(r'>([^<]{5,80})</a>', block) else ""
        href_m = re.search(r'href="(/empleos/[^"]+|https://www\.bumeran\.com\.ar/empleos/[^"]+)"', block)
        href = href_m.group(1) if href_m else ""
        if href and href.startswith("/"):
            href = "https://www.bumeran.com.ar" + href
        if not title or not href:
            continue
        # Filtro pasantía/part-time para no inundar
        if not re.search(r"pasant|trainee|junior|part.time|20hs", title + block, re.I):
            continue
        jobs.append({"fecha": "", "titulo": title[:90], "empresa": "", "ubicacion": "CABA", "modalidad": "", "jornada": "", "estado": "Bumeran", "url": href})
        if len(jobs) >= 15:
            break
    return jobs

def scrape_zonajobs_stealth(kw="pasantia"):
    # ZonaJobs mismo backend Navent, reusar bumeran con otro dominio
    url = f"https://www.zonajobs.com.ar/empleos/buscar?q={kw}"
    # Por ahora reuse bumeran logic con url distinta — placeholder
    return []

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kw", default="pasantia")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    for j in scrape_bumeran_stealth(args.kw, headed=args.headed):
        print(f"Bumeran | {j['titulo']} | {j['url']}")
