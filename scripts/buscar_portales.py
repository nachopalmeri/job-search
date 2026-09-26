import argparse
import json
import re
import sys
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from datetime import date
from html import unescape
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

FEEDS_YAML = Path(__file__).resolve().parent / "feeds_telegram.yaml"

KEYWORDS = ["pasantia", "pasantias", "pasante", "trainee", "jovenes+talentos", "jovenes+profesionales", "estudiante+sistemas", "junior", "part-time", "inteligencia+artificial", "python", "datos", "soporte", "help+desk", "AI+intern", "intern", "becario", "becarios", "practicante", "practicas+profesionales", "internship"]

BASE_LINKS = {
    "computrabajo": "https://ar.computrabajo.com/trabajo-de-{kw}",
    "bumeran": "https://www.bumeran.com.ar/empleos/busqueda-{kw}-en-buenos-aires.html",
    "zonajobs": "https://www.zonajobs.com.ar/empleos/buscar?q={kw}",
    "empleosit": "https://www.empleosit.com.ar/buscar/{kw}",
    "jooble": "https://ar.jooble.org/trabajo-{kw}/Buenos-Aires",
    "indeed": "https://ar.indeed.com/q-{kw}-empleos.html",
    "jobsora": "https://ar.jobsora.com/trabajo-{kw}-buenos-aires",
    "google": "https://www.google.com/search?ibp=htl;jobs&q={kw}+pasantia+IT+Argentina",
    "uade": "https://www.empleos.uade.edu.ar/busquedaslaborales",
    "firstjob": "https://www.firstjob.com",
    "wellfound": "https://wellfound.com/role/l/intern/Argentina",
    "getonbrd": "https://www.getonbrd.com/empleos/programacion?per_page=20&search={kw}",
    "torre": "https://torre.co/api/opportunities/_search?query={kw}&location=Argentina",
    "startupsargentina": "https://www.startupsargentina.com/jobs",
    "linkedin": "https://www.linkedin.com/jobs/search?keywords=pasantia&location=Argentina&f_TPR=r604800&f_E=1",
    "getonbrd_ar": "https://www.getonbrd.com.ar/trabajo/{kw}",
}

LINKEDIN_URL = "https://www.linkedin.com/jobs/search?keywords={kw}&location=Argentina&f_TPR=r604800&f_E=1"
STARTUPS_URL = "https://www.startupsargentina.com/jobs"
COMPUTRABAJO_URL = "https://ar.computrabajo.com/trabajo-de-{kw}"
BECASIT_URL = "https://becasit.itechcareer.com/pasant%C3%ADas"
EMPLEOSIT_RSS = "https://www.empleosit.com.ar/rss/"

RADAR_DIR = Path(__file__).resolve().parent.parent / "radar"
SEEN_FILE = RADAR_DIR / "seen_jobs.json"
TSV_HEADER = "fecha|portal|titulo|empresa|ubicacion|modalidad|jornada|estado|url|nuevo"

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
}


def build_links():
    out = []
    for portal, template in BASE_LINKS.items():
        if "{kw}" in template:
            for kw in KEYWORDS[:4]:
                out.append(f"{portal} | {template.format(kw=kw)}")
        else:
            out.append(f"{portal} | {template}")
    return out


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def _clean(text):
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _seen_key(job):
    return job.get("url", "").strip().split("?")[0] or f"{job.get('portal','')}|{job.get('titulo','')}".lower()


def _load_seen():
    if not SEEN_FILE.exists():
        return {}
    try:
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def _save_seen(seen):
    SEEN_FILE.write_text(
        json.dumps(seen, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _first(pattern, block):
    m = re.search(pattern, block, re.S)
    return _clean(m.group(1)) if m else ""


def _emit(portal, jobs, tsv_path=None):
    if tsv_path is not None:
        tsv_path.parent.mkdir(parents=True, exist_ok=True)
        with tsv_path.open("a", encoding="utf-8") as fh:
            for j in jobs:
                row = [j.get(k, "") for k in ["fecha", "titulo", "empresa", "ubicacion", "modalidad", "jornada", "estado", "url", "nuevo"]]
                row = [str(v).replace("|", "/") for v in row]
                fh.write(f"{portal}|" + "|".join(row) + "\n")
    for j in jobs:
        print(f"{portal} | {j['titulo']} | {j['empresa']} | {j['ubicacion']} | {j['fecha']} | {j['modalidad']} | {j['jornada']} | {j['estado']} | {j['url']} | {j.get('nuevo','')}")


def scrape_linkedin(kw):
    jobs = []
    html = _get(LINKEDIN_URL.format(kw=kw))
    for block in re.split(r'data-entity-urn="urn:li:jobPosting:', html)[1:]:
        job_id = block.split('"', 1)[0]
        href = _first(r'href="(https://ar\.linkedin\.com/jobs/view/[^"?]+)', block)
        if href.endswith("?") or not href:
            continue
        title = _first(r'base-search-card__title">(.*?)</h3>', block)
        company = _first(r'hidden-nested-link[^>]*>\s*(.*?)\s*</a>', block)
        location = _first(r'job-search-card__location">(.*?)</span>', block)
        fecha = _first(r'job-search-card__listdate" datetime="([^"]+)"', block)
        hiring = "Actively Hiring" if _first(r'job-posting-benefits__text">(.*?)</span>', block) else ""
        if not title and not company:
            continue
        jobs.append({
            "fecha": fecha, "titulo": title, "empresa": company, "ubicacion": location,
            "modalidad": "", "jornada": "", "estado": hiring, "url": href,
        })
    return jobs


# --- Filtros de relevancia para fuentes grandes (Startups Argentina / YC / Speedrun) ---
# Regla v3 (25/09/2026): full-time YA NO es veto. Se descarta solo por seniority claramente alto.
_SENIOR_RE = re.compile(r"\b(senior|sr\.?|staff|principal|lead|leader|head|director|vp|manager|architect|cto|cfo|chief|ssr|semi[- ]?senior|expert|ii|iii|iv)\b", re.I)
_ENTRY_TECH_RE = re.compile(
    r"(intern|pasant|junior|\bjr\b|trainee|becari|practicante|entry|new grad|graduate|apprentic|"
    r"support|soporte|help ?desk|\bqa\b|tester|test |data|datos|python|automat|\bai\b|\bia\b|\bml\b|prompt|"
    r"sistemas|developer|desarrollador|engineer|software|implementation|onboarding|"
    r"customer success|technical|it operations|devops)", re.I)


def _relevant(title):
    t = title or ""
    return bool(_ENTRY_TECH_RE.search(t)) and not _SENIOR_RE.search(t)


_REMOTE_OK_RE = re.compile(r"(?i:argentina|latin america|latam|south america|americas|worldwide|global|anywhere)|\bAR\b")
_US_ONLY_RE = re.compile(r"\((?:us|usa|canada|ca|uk|eu|india|in)[^)]*\)|\bus only\b|united states|, us\b|/ us\b", re.I)


def _remote_ok(loc):
    """Remoto alcanzable desde Argentina: acepta LatAm/Argentina/Worldwide o 'Remote' a secas (ambiguo, se revisa a mano).
    Rechaza 'Remote (US)', 'Toronto ... / Remote', 'Remote (FR)' y cualquier remoto atado a otra region/pais."""
    l = (loc or "").strip()
    if _REMOTE_OK_RE.search(l):
        return True
    return bool(re.fullmatch(r"remote|remoto|remote \(worldwide\)|anywhere", l, re.I))


def _get_json(url):
    """Speedrun (Cloudflare) rechaza el UA completo del script pero acepta uno simple."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def scrape_startupsargentina(max_pages=40, only_relevant=True):
    """Startups Argentina: el sitio migro (2026-09) de /jobs con <article class="job-card"> a
    /empleos?page=N con <article class="...__card">. Recorre las paginas hasta que no haya avisos nuevos."""
    jobs, seen_ids = [], set()
    card_re = re.compile(
        r'<h2><a href="(/empleos/([^/"]+)/([0-9a-f-]{36})/[^"]+)">(.*?)</a></h2>\s*'
        r'<p><a href="/startups/[^"]*">(.*?)</a></p>\s*<span>(.*?)</span>', re.S)
    page = 0
    for page in range(1, max_pages + 1):
        try:
            html = _get(f"https://www.startupsargentina.com/empleos?page={page}")
        except Exception as e:
            if "404" not in str(e):  # 404 = fin de la paginacion (esperado)
                print(f"WARN startupsargentina page={page}: {e}", file=sys.stderr)
            break
        found = 0
        for href, co_slug, jid, title, company, loc in card_re.findall(html):
            if jid in seen_ids:
                continue
            seen_ids.add(jid)
            found += 1
            title, company, loc = _clean(title), _clean(company), _clean(loc)
            if only_relevant and not _relevant(title):
                continue
            jobs.append({
                "fecha": "", "titulo": title, "empresa": company, "ubicacion": loc,
                "modalidad": "", "jornada": "", "estado": "StartupsAR",
                "url": f"https://www.startupsargentina.com{href}",
            })
        if found == 0:
            break
    print(f"  -> Startups Argentina: {len(seen_ids)} avisos totales, {len(jobs)} relevantes (paginas: {page})")
    if len(seen_ids) == 0:
        print("WARN Startups Argentina devolvio 0 avisos: revisar si cambio el HTML (regex card_re)", file=sys.stderr)
    return jobs


def scrape_yc(only_relevant=True):
    """YC Work at a Startup (paginas SSR /jobs/role/<rol>/remote). Solo entry/tech con remoto alcanzable desde AR."""
    jobs, seen_urls = [], set()
    roles = ["software-engineer", "operations", "support-success", "science", "product-manager"]
    for role in roles:
        try:
            html = _get(f"https://www.ycombinator.com/jobs/role/{role}/remote")
        except Exception as e:
            print(f"WARN yc role={role}: {e}", file=sys.stderr)
            continue
        for li in re.split(r'<li class="my-2 flex', html)[1:]:
            href = _first(r'href="(/companies/[^"/]+/jobs/[^"]+)"', li)
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            title = _first(r'href="/companies/[^"/]+/jobs/[^"]+"[^>]*>([^<]+)</a>', li)
            company = _first(r'<span class="block font-bold md:inline">([^<]+)<!-- --> \([^)]*\)</span>', li)
            batch = _first(r'<span class="block font-bold md:inline">[^<]+<!-- --> \(([^)]*)\)</span>', li)
            metas = [_clean(x) for x in re.findall(r'<div class="whitespace-nowrap">([^<]*)</div>', li)]
            loc_m = re.search(r'<div class="break-all md:break-normal">([^<]*)</div>', li)
            loc = _clean(loc_m.group(1)) if loc_m else ""
            jtype = metas[0] if metas else ""
            salary = next((m for m in metas if re.search(r"[$£€]", m)), "")
            is_intern = bool(re.search(r"intern", jtype, re.I))
            if not _remote_ok(loc):
                continue
            if only_relevant and not (is_intern or _relevant(title)):
                continue
            if _SENIOR_RE.search(title):
                continue
            jobs.append({
                "fecha": "", "titulo": title, "empresa": f"{company} ({batch})" if batch else company,
                "ubicacion": loc, "modalidad": jtype, "jornada": salary, "estado": "YC",
                "url": f"https://www.ycombinator.com{href}",
            })
    print(f"  -> YC Work at a Startup: {len(jobs)} (remoto alcanzable desde AR)")
    return jobs


def scrape_speedrun(pages=3):
    """a16z Speedrun Talent Network via su API JSON (/api/jobs). Remoto + entry/intern/junior + keywords de nuestro perfil."""
    jobs, seen_ids = [], set()
    queries = ["intern", "junior", "entry level", "python", "support", "qa", "automation", "data analyst"]
    for q in queries:
        for page in range(pages):
            try:
                data = _get_json(f"https://speedrun-talent-network.com/api/jobs?limit=50&remote=1&page={page}&q={urllib.request.quote(q)}")
            except Exception as e:
                print(f"WARN speedrun q={q} page={page}: {e}", file=sys.stderr)
                break
            batch = data.get("jobs", [])
            if not batch:
                break
            for j in batch:
                jid = j.get("id")
                if jid in seen_ids:
                    continue
                seen_ids.add(jid)
                title = j.get("title", "")
                loc = j.get("location", "") or "Remote"
                if not j.get("is_remote"):
                    continue
                if not _remote_ok(loc):
                    continue
                if j.get("seniority") in ("senior", "staff", "exec", "director", "vp") or _SENIOR_RE.search(title):
                    continue
                jobs.append({
                    "fecha": (j.get("published_at") or "")[:10], "titulo": title, "empresa": j.get("company_key", ""),
                    "ubicacion": loc, "modalidad": j.get("employment_type") or "", "jornada": j.get("seniority") or "",
                    "estado": "Speedrun", "url": "https://speedrun-talent-network.com" + j.get("path", ""),
                })
    print(f"  -> a16z Speedrun: {len(jobs)} remotos entry/intern")
    return jobs


def scrape_computrabajo(kw):
    jobs = []
    html = _get(COMPUTRABAJO_URL.format(kw=kw))
    for block in re.split(r'class="box_offer', html)[1:]:
        href = _first(r'href="(/ofertas-de-trabajo/oferta-de-trabajo-de-[^"#]+)', block)
        if not href:
            continue
        title = _first(r'js-o-link[^>]*>\s*(.*?)\s*</a>', block)
        m_emp = re.search(r'offer-grid-article-company-url[^>]*>\s*([^<]+)\s*</a>', block)
        company = _clean(m_emp.group(1)) if m_emp else ""
        location = _first(r'<p class="fs16 fc_base mt5">\s*<span class="mr10">(.*?)</span>', block)
        m_mod = re.search(r'<p class="fs16 fc_base mt5">\s*<span class="mr10">.*?</span>\s*(?:<span[^>]*>)?\s*(.*?)\s*</p>', block, re.S)
        modalidad = _clean(m_mod.group(1)) if m_mod else ""
        fecha = _first(r'<p class="fs13 fc_aux mt15">\s*(.*?)\s*</p>', block)
        jobs.append({
            "fecha": fecha, "titulo": title, "empresa": company, "ubicacion": location,
            "modalidad": modalidad, "jornada": "", "estado": "", "url": "https://ar.computrabajo.com" + href,
        })
    return jobs


def scrape_becasit():
    jobs = []
    html = _get(BECASIT_URL)
    for block in re.split(r'<div class="oKdM2c ZZyype">', html)[1:]:
        m_id = re.search(r'id="(h\.[^"]+)"', block)
        block_id = m_id.group(1) if m_id else ""
        m_head = re.search(r"<(h[1-4])[^>]*>(.*?)</\1>", block, re.S)
        if not m_head:
            continue
        title = _clean(re.sub(r"<[^>]+>", "", m_head.group(2)))
        title = re.sub(r"^[✓✔️]+\s*", "", title).strip()
        title = re.sub(r"\s*[-·]?\s*Imp\. Multinac\..*$", "", title).strip()
        if not title.lower().startswith("pasante"):
            continue
        jobs.append({
            "fecha": "", "titulo": title, "empresa": "ITEchCampus (BecasIT)", "ubicacion": "Buenos Aires",
            "modalidad": "", "jornada": "", "estado": "", "url": f"https://becasit.itechcareer.com/pasant%C3%ADas#{block_id}",
        })
    return jobs


def _strip_tags(html):
    return _clean(re.sub(r"<[^>]+>", " ", html))


def scrape_empleosit():
    jobs = []
    xml = _get(EMPLEOSIT_RSS)
    root = ET.fromstring(xml)
    keywords = re.compile(r"pasant|trainee|junior|part.?time|medio tiempo|estudiante|primer.?a experiencia|joven", re.I)
    for item in root.iter("item"):
        title = _clean(item.findtext("title", "") or "")
        link = _clean(item.findtext("link", "") or "")
        desc = _strip_tags(item.findtext("description", "") or "")
        if not keywords.search(title) and not keywords.search(desc[:400]):
            continue
        location = ""
        m_loc = re.search(r"([A-Za-zÁÉÍÓÚÑáéíóúñ ]+?(?:\(CABA\)|Capital Federal|Buenos Aires|AMBA|GBA))", desc)
        if m_loc:
            location = m_loc.group(1).strip()
        modalidad = ""
        m_mod = re.search(r"Modalidad:\s*([^\n<]{2,30})", desc)
        if m_mod:
            modalidad = m_mod.group(1).strip()
        jornada = ""
        m_jor = re.search(r"Jornada laboral:\s*([^\n<]{2,40})", desc)
        if m_jor:
            jornada = m_jor.group(1).strip()
        jobs.append({
            "fecha": "", "titulo": title, "empresa": "", "ubicacion": location,
            "modalidad": modalidad, "jornada": jornada, "estado": "", "url": link,
        })
    return jobs


def scrape_telegram_feeds():
    jobs = []
    if yaml is None or not FEEDS_YAML.exists():
        return jobs
    try:
        data = yaml.safe_load(FEEDS_YAML.read_text(encoding="utf-8"))
    except Exception:
        return jobs
    feeds = data.get("feeds", []) or []
    keywords = re.compile(r"pasant|trainee|junior|part.?time|20hs|intern|soporte|help desk|python|datos|infra", re.I)
    for feed in feeds:
        if not feed.get("enabled", True):
            continue
        if feed.get("type") not in ("telegram_channel", "rss"):
            continue
        url = feed.get("url", "")
        if not url:
            continue
        try:
            html = _get(url)
        except Exception:
            continue
        for block in re.split(r'class="tgme_widget_message_text', html)[1:]:
            # block empieza con ' js-message_text" dir="auto">CONTENIDO...'
            if ">" in block:
                block = block.split(">", 1)[1]
            text = _clean(re.sub(r"<[^>]+>", " ", block.split("</div>", 1)[0]))
            if not text or not keywords.search(text):
                continue
            m_link = re.search(r'href="(https://t\.me/[^"]+)"', block)
            link = m_link.group(1) if m_link else url
            title = text[:90] + "..." if len(text) > 90 else text
            jobs.append({
                "fecha": "", "titulo": title, "empresa": feed.get("name", "Telegram"), "ubicacion": "Telegram",
                "modalidad": "", "jornada": "", "estado": "Telegram", "url": link,
            })
            if len(jobs) >= 20:
                break
    return jobs


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Busqueda diaria de pasantias IT Argentina")
    ap.add_argument("--links", action="store_true", help="imprimir links de busqueda prearmados")
    ap.add_argument("--open", action="store_true", help="abrir links en el navegador")
    ap.add_argument("--scrape", choices=["linkedin", "startups", "yc", "speedrun", "computrabajo", "becasit", "empleosit", "telegram", "bumeran", "uade", "getonbrd", "wellfound", "torre", "all"], help="scrapeo de avisos")
    ap.add_argument("--kw", default="pasantia", help="keyword para el scrapeo (LinkedIn / Computrabajo)")
    ap.add_argument("--write", action="store_true", help="guardar en radar/daily-YYYY-MM-DD.tsv y actualizar seen_jobs.json")
    ap.add_argument("--new", action="store_true", help="mostrar solo avisos no vistos antes (comparado contra seen_jobs.json)")
    args = ap.parse_args()

    if args.links or args.open:
        links = build_links()
        for l in links:
            print(l)
        if args.open:
            for l in links:
                url = l.split(" | ", 1)[1]
                webbrowser.open(url)
        return

    if args.scrape:
        tsv_path = None
        seen = _load_seen() if (args.write or args.new) else {}
        seen_today = {}
        if args.write:
            tsv_path = RADAR_DIR / f"daily-{date.today().isoformat()}.tsv"
            tsv_path.write_text(TSV_HEADER + "\n", encoding="utf-8")
        selected = ["linkedin", "startups", "yc", "speedrun", "computrabajo", "becasit", "empleosit", "telegram", "bumeran", "uade", "getonbrd", "wellfound", "torre"] if args.scrape == "all" else [args.scrape]
        for name in selected:
            print(f"## {name.capitalize()}")
            if name == "linkedin":
                # Expand LinkedIn: 10 keywords (pasantia + AI intern + becario + etc.) — deduplicado por URL
                linkedin_kws = ["pasantia", "pasante", "AI+intern", "intern", "becario", "practicante", "trainee", "junior", "part-time", "inteligencia+artificial", "jovenes+profesionales", "jovenes+talentos"]
                seen_urls = set()
                jobs = []
                for kw in linkedin_kws:
                    try:
                        for j in scrape_linkedin(kw):
                            if j["url"] not in seen_urls:
                                seen_urls.add(j["url"])
                                jobs.append(j)
                    except Exception as e:
                        print(f"WARN linkedin kw={kw}: {e}", file=sys.stderr)
                print(f"  -> LinkedIn expandido: {len(jobs)} únicos de {len(linkedin_kws)} keywords")
            elif name == "startups":
                jobs = scrape_startupsargentina()
            elif name == "yc":
                jobs = scrape_yc()
            elif name == "speedrun":
                jobs = scrape_speedrun()
            elif name == "computrabajo":
                jobs = scrape_computrabajo(args.kw)
            elif name == "becasit":
                jobs = scrape_becasit()
            elif name == "empleosit":
                jobs = scrape_empleosit()
            elif name == "telegram":
                jobs = scrape_telegram_feeds()
            elif name == "bumeran":
                # Intenta stealth via bumeran_scraper.py (soporta ambos import paths)
                try:
                    try:
                        from scripts.bumeran_scraper import scrape_bumeran_stealth
                    except ImportError:
                        from bumeran_scraper import scrape_bumeran_stealth  # type: ignore
                    jobs = scrape_bumeran_stealth(kw="pasantia", headed=False)
                    print(f"  -> Bumeran stealth: {len(jobs)}")
                except Exception as e:
                    print(f"WARN bumeran stealth no disponible: {e}", file=sys.stderr)
                    jobs = []
            elif name == "uade":
                # UADE via uade_scraper.py (requiere .secrets/uade_cookies.json, si no existe → 0 y WARN)
                try:
                    try:
                        from scripts.uade_scraper import scrape_uade
                    except ImportError:
                        from uade_scraper import scrape_uade  # type: ignore
                    jobs = scrape_uade(headless=True, max_pages=2)
                    print(f"  -> UADE: {len(jobs)}")
                except SystemExit as e:
                    print(f"WARN UADE no autenticado: {e}", file=sys.stderr)
                    jobs = []
                except Exception as e:
                    print(f"WARN uade scraper: {e}", file=sys.stderr)
                    jobs = []
            elif name == "getonbrd":
                try:
                    html = _get(f"https://www.getonbrd.com/empleos/programacion?per_page=20&search=pasantia")
                    jobs = []
                    for block in re.split(r'class="gb-results__item', html)[1:]:
                        title = _first(r'gb-results__title[^>]*>(.*?)</a>', block)
                        href = _first(r'href="([^"]+)"', block)
                        if href.startswith("/"): href = "https://www.getonbrd.com"+href
                        if title and re.search(r"pasant|intern|junior|trainee", title, re.I):
                            jobs.append({"titulo":title[:90],"empresa":"","ubicacion":"Remote","url":href,"fecha":"","modalidad":"","jornada":"","estado":"GetOnBoard"})
                    print(f"  -> GetOnBoard: {len(jobs)}")
                except Exception as e:
                    print(f"WARN getonbrd: {e}", file=sys.stderr)
                    jobs = []
            elif name == "wellfound":
                try:
                    html = _get("https://wellfound.com/role/l/intern/Argentina")
                    jobs = []
                    # Wellfound is SPA, fallback to 0, handled via websearch
                    print(f"  -> Wellfound: {len(jobs)} (SPA, usar websearch)")
                except Exception as e:
                    print(f"WARN wellfound: {e}", file=sys.stderr)
                    jobs = []
            elif name == "torre":
                try:
                    html = _get("https://torre.co/api/opportunities/_search?query=pasantia&location=Argentina")
                    jobs = []
                    print(f"  -> Torre: {len(jobs)} (API requiere POST)")
                except Exception as e:
                    print(f"WARN torre: {e}", file=sys.stderr)
                    jobs = []
            else:
                jobs = []
            if args.write or args.new:
                seen_today[name] = []
                for j in jobs:
                    key = _seen_key(j)
                    if key not in seen:
                        j["nuevo"] = "NUEVO"
                        seen[key] = date.today().isoformat()
                        seen_today[name].append(j)
                    else:
                        j["nuevo"] = ""
                if args.new:
                    jobs = [j for j in jobs if j["nuevo"] == "NUEVO"]
                    print(f"[--new] {name}: {len(jobs)} sin ver de {len(seen)} conocidos\n")
            _emit(name, jobs, tsv_path)
        if args.write:
            _save_seen(seen)
            print(f"\nTSV guardado en {tsv_path}")
        if args.new:
            total_new = sum(len(v) for v in seen_today.values())
            print(f"\nNuevos totales: {total_new} (ya conocidos: {len(seen) - total_new})")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
