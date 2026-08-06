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

KEYWORDS = ["pasantia", "pasantias", "pasante", "trainee", "jovenes+talentos", "estudiante+sistemas", "junior", "part-time", "inteligencia+artificial", "python", "datos", "soporte", "help+desk"]

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
    "wellfound": "https://wellfound.com/role/{kw}",
    "startupsargentina": "https://www.startupsargentina.com/jobs",
    "linkedin": "https://www.linkedin.com/jobs/search?keywords=pasantia&location=Argentina&f_TPR=r604800&f_E=1",
    "getonbrd": "https://www.getonbrd.com.ar/trabajo/{kw}",
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


def scrape_startupsargentina():
    jobs = []
    html = _get(STARTUPS_URL)
    for block in re.split(r'<article class="job-card">', html)[1:]:
        m_co = re.search(r'<a href="/startups/[^"]*"[^>]*>([^<]+)</a>', block)
        company = _clean(m_co.group(1)) if m_co else ""
        m_tags = re.search(r'</a>\s*<span>(.*?)</span>', block, re.S)
        tags = _clean(m_tags.group(1)) if m_tags else ""
        tags = tags.replace("<!-- -->", "/")
        fecha = _first(r'job-card__role"><span>([^<]+)</span>', block)
        title = _first(r'job-card__role">.*?<h2>(.*?)</h2>', block)
        m_loc = re.search(r'job-card__meta"><span>.*?</svg>\s*(?:<!-- -->)?\s*(.*?)</span>', block, re.S)
        location = _clean(m_loc.group(1)) if m_loc else ""
        m_apply = re.search(r'job-card__apply" href="([^"]+)"', block)
        apply_url = m_apply.group(1) if m_apply else ""
        slug = _first(r'<a href="(/startups/[^"]+)"', block)
        profile_url = f"https://www.startupsargentina.com{slug}" if slug.startswith("/") else ""
        jobs.append({
            "fecha": fecha, "titulo": title, "empresa": company, "ubicacion": location,
            "modalidad": "", "jornada": "", "estado": tags, "url": apply_url or profile_url,
        })
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


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Busqueda diaria de pasantias IT Argentina")
    ap.add_argument("--links", action="store_true", help="imprimir links de busqueda prearmados")
    ap.add_argument("--open", action="store_true", help="abrir links en el navegador")
    ap.add_argument("--scrape", choices=["linkedin", "startups", "computrabajo", "becasit", "empleosit", "all"], help="scrapeo de avisos")
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
        selected = ["linkedin", "startups", "computrabajo", "becasit", "empleosit"] if args.scrape == "all" else [args.scrape]
        for name in selected:
            print(f"## {name.capitalize()}")
            if name == "linkedin":
                jobs = scrape_linkedin(args.kw)
            elif name == "startups":
                jobs = scrape_startupsargentina()
            elif name == "computrabajo":
                jobs = scrape_computrabajo(args.kw)
            elif name == "becasit":
                jobs = scrape_becasit()
            elif name == "empleosit":
                jobs = scrape_empleosit()
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
