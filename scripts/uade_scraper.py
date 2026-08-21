"""UADE scraper headless — empleos.uade.edu.ar (login con libreta UADE).

Diseño: nunca hardcodear credenciales. El usuario loguea 1 vez en modo headed,
guarda storage_state en .secrets/uade_cookies.json (gitignored). Luego headless usa
ese storage. Si expira, pide re-login.

Uso:
  python scripts/uade_scraper.py --login          # abre browser headed, logueate manual, espera a /busquedaslaborales y guarda
  python scripts/uade_scraper.py --scrape         # headless, parsea 1-2 páginas y devuelve jobs
  python scripts/uade_scraper.py --scrape --write # integra con buscar_portales (llamado desde main)

Req: playwright==1.44  -> pip install playwright && playwright install chromium
Env: .secrets/uade_cookies.json (no commitear)

Email cuenta UADE: ignaciopalmeri1@gmail.com NO — UADE usa libreta/legajo, no Gmail. Este scraper usa tu libreta UADE.
"""
import json
import re
import sys
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
SECRETS_DIR = BASE / ".secrets"
STORAGE = SECRETS_DIR / "uade_cookies.json"
UADE_LOGIN = "https://www.empleos.uade.edu.ar/"
UADE_LIST = "https://www.empleos.uade.edu.ar/busquedaslaborales"

# Import lazy para no romper --help si playwright no instalado
def _ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        return sync_playwright
    except ImportError:
        print("Falta playwright: pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(2)


def do_login():
    sync_playwright = _ensure_playwright()
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    # .gitignore ya tiene .secrets/
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="es-AR")
        page = context.new_page()
        print(f"Abriendo {UADE_LOGIN} — logueate con tu libreta UADE y navegá hasta /busquedaslaborales")
        print("Cuando veas la lista de búsquedas, vuelve acá y presiona ENTER para guardar sesión.")
        page.goto(UADE_LOGIN, wait_until="domcontentloaded")
        # Esperar navegación manual — no auto timeout, el usuario avisa
        input(">>> Presiona ENTER cuando ya estés en la lista de búsquedas (busquedaslaborales) ...")
        # Validar que esté en lista
        if "busquedaslaborales" not in page.url:
            try:
                page.goto(UADE_LIST, wait_until="domcontentloaded")
                page.wait_for_url("**/busquedaslaborales**", timeout=15000)
            except Exception:
                print(f"WARN: no se detectó /busquedaslaborales, url actual: {page.url} — igual guardando", file=sys.stderr)
        # Guardar storage
        context.storage_state(path=str(STORAGE))
        print(f"OK — sesión guardada en {STORAGE} ({STORAGE.stat().st_size} bytes)")
        # ASK explícito
        ans = input("¿Mantener sesión para futuros scrapes headless? [S/n]: ").strip().lower()
        if ans in ("n", "no"):
            STORAGE.unlink(missing_ok=True)
            print("Sesión descartada por pedido.")
        browser.close()


def scrape_uade(headless=True, max_pages=2):
    """Devuelve lista jobs dict compatible con buscar_portales._emit."""
    sync_playwright = _ensure_playwright()
    if not STORAGE.exists():
        print(f"ERROR: no existe {STORAGE} — corre primero: python scripts/uade_scraper.py --login", file=sys.stderr)
        sys.exit(1)
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="es-AR", storage_state=str(STORAGE))
        page = context.new_page()
        try:
            page.goto(UADE_LIST, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("article, div.card, .busqueda-card, .listado-buscadores", timeout=15000)
        except Exception as e:
            print(f"ERROR: no cargó lista UADE ({e}) — sesión expirada? Re-login con --login", file=sys.stderr)
            browser.close()
            sys.exit(1)

        for pg in range(max_pages):
            # Extraer cards de esta página
            cards = page.query_selector_all("article, div.card, .busqueda-card")
            if not cards:
                # fallback: todo el body
                html = page.content()
                # Regex fallback si SPA no renderizó cards
                for m in re.finditer(r'busqueda\s*(\d{4}-\d+)', html, re.I):
                    bid = m.group(1)
                    jobs.append({"fecha": str(date.today()), "titulo": f"Busqueda {bid}", "empresa": "", "ubicacion": "UADE", "modalidad": "", "jornada": "", "estado": "UADE", "url": f"{UADE_LIST}/{bid}"})
                break
            for c in cards:
                try:
                    txt = c.inner_text().strip()
                    # Heurística: primera línea = título, segunda = empresa
                    lines = [l.strip() for l in txt.splitlines() if l.strip()]
                    titulo = lines[0] if lines else "Busqueda UADE"
                    empresa = lines[1] if len(lines) > 1 else ""
                    # Link
                    a = c.query_selector("a[href*='busqueda']")
                    href = a.get_attribute("href") if a else ""
                    if href and href.startswith("/"):
                        href = "https://www.empleos.uade.edu.ar" + href
                    elif not href:
                        # buscar id en texto
                        m = re.search(r'(\d{4}-\d+)', txt)
                        href = f"{UADE_LIST}/{m.group(1)}" if m else UADE_LIST
                    jobs.append({"fecha": str(date.today()), "titulo": titulo[:90], "empresa": empresa[:40], "ubicacion": "UADE", "modalidad": "", "jornada": "", "estado": "UADE", "url": href})
                except Exception:
                    continue
            # Paginación
            if pg + 1 >= max_pages:
                break
            nxt = page.query_selector("a[rel='next'], button:has-text('Siguiente'), a:has-text('Siguiente')")
            if not nxt or not nxt.is_enabled():
                break
            try:
                nxt.click()
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                page.wait_for_timeout(2000)
            except Exception:
                break
        browser.close()
    # Dedupe por url
    seen = set()
    uniq = []
    for j in jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            uniq.append(j)
    return uniq


def main():
    import argparse
    ap = argparse.ArgumentParser(description="UADE scraper headless")
    ap.add_argument("--login", action="store_true", help="login manual headed y guardar storage")
    ap.add_argument("--scrape", action="store_true", help="scrape headless")
    ap.add_argument("--headed", action="store_true", help="scrape pero headed (debug)")
    ap.add_argument("--pages", type=int, default=2, help="páginas a scrapear")
    ap.add_argument("--write", action="store_true", help="guardar en radar/daily-*.tsv + seen (para compat)")
    args = ap.parse_args()
    if args.login:
        do_login()
        return
    if args.scrape:
        jobs = scrape_uade(headless=not args.headed, max_pages=args.pages)
        print(f"UADE: {len(jobs)} avisos")
        for j in jobs:
            print(f"UADE | {j['titulo']} | {j['empresa']} | {j['url']}")
        if args.write:
            # Integración con buscar_portales: reusa su TSV/seen
            from buscar_portales import _load_seen, _save_seen, _seen_key, _emit, RADAR_DIR, TSV_HEADER  # type: ignore
            from datetime import date as d
            tsv = RADAR_DIR / f"daily-{d.today().isoformat()}.tsv"
            if not tsv.exists():
                tsv.write_text(TSV_HEADER + "\n", encoding="utf-8")
            seen = _load_seen()
            new_jobs = []
            for j in jobs:
                k = _seen_key(j)
                if k not in seen:
                    j["nuevo"] = "NUEVO"
                    seen[k] = str(d.today())
                    new_jobs.append(j)
                else:
                    j["nuevo"] = ""
            _emit("uade", (new_jobs if new_jobs else jobs), tsv)
            _save_seen(seen)
            print(f"TSV -> {tsv}")
        return
    ap.print_help()

if __name__ == "__main__":
    main()
