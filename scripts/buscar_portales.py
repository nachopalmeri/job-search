import argparse
import csv
import json
import re
import sys
import unicodedata
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
    "torre": "https://torre.ai/search/jobs?q={kw}",
    "cosign": "https://cosign.co/jobs",
    "x_twitter": "https://x.com/search?q=(pasante%20OR%20pasantia%20OR%20trainee%20OR%20junior)%20(IT%20OR%20sistemas%20OR%20IA%20OR%20datos)%20(buscamos%20OR%20contratando%20OR%20hiring)%20lang%3Aes&f=live",
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
TSV_HEADER = "portal|fecha|titulo|empresa|ubicacion|modalidad|jornada|estado|url|nuevo|tracker"
TRACKER_CSV = Path(__file__).resolve().parent.parent / "tracker" / "postulaciones.csv"

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


# --- Cruce contra el tracker de Nacho (tracker/postulaciones.csv): empresa + puesto, nunca solo la empresa ---
_TRK_STOP = {"argentina", "group", "inc", "llc", "ltd", "company", "the", "and", "remote", "latam"}


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _tokens(s):
    return {t for t in _norm(s).split() if len(t) >= 4 and t not in _TRK_STOP}


def _load_tracker():
    """Postulaciones ya registradas (enviadas o descartadas a proposito). 'Para postular' no cuenta: todavia no se mando."""
    out = []
    if not TRACKER_CSV.exists():
        return out
    with TRACKER_CSV.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            est = (r.get("estado") or "").strip()
            if est in ("", "Para postular"):
                continue
            out.append((_tokens(r.get("empresa")), _norm(r.get("puesto")),
                        (r.get("link") or "").split("?")[0].strip().lower(),
                        "DESCARTADA" if est == "Descartada" else "POSTULADA"))
    return out


def _tracker_mark(job, tracker):
    """'POSTULADA' / 'DESCARTADA' si ese aviso exacto ya esta en el tracker; '' si es nuevo para Nacho.
    Igual URL = seguro. Si no, misma empresa (token en comun) Y mismo puesto (igual, prefijo de 3+ palabras, o 80% de palabras en comun)."""
    url = (job.get("url") or "").split("?")[0].strip().lower()
    emp, tit = _tokens(job.get("empresa")), _norm(job.get("titulo"))
    for toks, puesto, link, label in tracker:
        if url and link and url == link:
            return label
        if not (emp & toks) or not tit or not puesto:
            continue
        short, long_ = sorted((tit, puesto), key=len)
        wa, wb = set(tit.split()), set(puesto.split())
        # palabras completas: "Analista BI" vs "Analista IA" NO es el mismo aviso (por letras se parecerian)
        if tit == puesto or (len(short.split()) >= 3 and long_.startswith(short)) or len(wa & wb) / len(wa | wb) >= 0.8:
            return label
    return ""


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
                row = [j.get(k, "") for k in ["fecha", "titulo", "empresa", "ubicacion", "modalidad", "jornada", "estado", "url", "nuevo", "tracker"]]
                row = [str(v).replace("|", "/") for v in row]
                fh.write(f"{portal}|" + "|".join(row) + "\n")
    for j in jobs:
        print(f"{portal} | {j['titulo']} | {j['empresa']} | {j['ubicacion']} | {j['fecha']} | {j['modalidad']} | {j['jornada']} | {j['estado']} | {j['url']} | {j.get('nuevo','')} | {j.get('tracker','')}")


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


# Para agregadores masivos (Cosign, Torre, Get on Board) "intern"/"junior" solo no alcanza: tiene que ser tech/ops tecnico.
_TECH_RE = re.compile(
    r"(support|soporte|help ?desk|\bqa\b|tester|testing|data|datos|python|automat|\bai\b|\bia\b|\bml\b|machine learning|prompt|"
    r"sistemas|developer|desarrollador|engineer|ingenier|software|programad|implementation|implementaci|onboarding|"
    r"customer success|technical|t[eé]cnic|\bit\b|tecnolog|devops|cloud|backend|frontend|full.?stack|analytics|analista|"
    r"product|security|seguridad|infra|network|redes|sql|web)", re.I)


def _tech_entry(title, entry_hint=False):
    t = title or ""
    if _SENIOR_RE.search(t) or not _TECH_RE.search(t):
        return False
    return entry_hint or _relevant(t)


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


def _post_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


_AR_LOC_RE = re.compile(r"argentin|buenos aires|caba|c\.a\.b\.a|latam|latin america|south america|\bAR\b", re.I)


def scrape_cosign(pages=3):
    """Cosign (cosign.co/jobs): agregador de avisos de empresas grandes y startups (red de a16z).
    La pagina es Next.js y busca contra Convex: accion publica jobSearchAction:search con
    args {term, remoteOnly, cursor, limit}. Buscamos por Argentina/Buenos Aires/LATAM y por
    intern/junior remoto, y filtramos entry/tech + ubicacion alcanzable desde AR."""
    endpoint = "https://cheerful-donkey-418.convex.cloud/api/action"
    searches = [("Argentina", False), ("Buenos Aires", False), ("LATAM", True),
                ("intern", True), ("junior", True), ("trainee", False), ("pasantia", False)]
    jobs, seen_ids = [], set()
    for term, remote_only in searches:
        cursor = None
        for _ in range(pages):
            args = {"term": term, "cursor": cursor, "limit": 30}
            if remote_only:
                args["remoteOnly"] = True
            try:
                res = _post_json(endpoint, {"path": "jobSearchAction:search", "args": args, "format": "json"})
            except Exception as e:
                print(f"WARN cosign term={term}: {e}", file=sys.stderr)
                break
            if res.get("status") != "success":
                print(f"WARN cosign term={term}: {res.get('errorMessage', '')[:120]}", file=sys.stderr)
                break
            val = res.get("value") or {}
            for a in val.get("page") or []:
                pid = a.get("postingId")
                if not pid or pid in seen_ids or a.get("closed"):
                    continue
                seen_ids.add(pid)
                title, loc = a.get("title") or "", a.get("location") or ""
                is_intern = (a.get("employmentType") or "").lower() == "intern"
                if not _tech_entry(title, is_intern):
                    continue
                if not (_AR_LOC_RE.search(loc) or (a.get("remote") and _remote_ok(loc))):
                    continue
                jobs.append({
                    "fecha": "", "titulo": title, "empresa": a.get("organizationName") if a.get("organizationName") not in (None, "index") else (a.get("organizationPath") or "").split("/")[-1],
                    "ubicacion": loc, "modalidad": "Remoto" if a.get("remote") else "", "jornada": a.get("employmentType") or "",
                    "estado": "Cosign", "url": a.get("applyUrl") or a.get("url") or "https://cosign.co/jobs",
                })
            cursor = val.get("continueCursor")
            if val.get("isDone") or not cursor:
                break
    print(f"  -> Cosign: {len(seen_ids)} avisos revisados, {len(jobs)} relevantes para AR")
    if not seen_ids:
        print("WARN Cosign devolvio 0 avisos: revisar si cambio el deployment Convex o la accion jobSearchAction:search", file=sys.stderr)
    return jobs


def scrape_getonbrd(pages=2):
    """Get on Board via API publica v0 (/api/v0/search/jobs). Seniority 1=sin experiencia, 2=junior."""
    queries = ["practicante", "pasantia", "trainee", "junior", "intern", "soporte", "qa", "python", "datos"]
    jobs, seen_urls = [], set()
    for q in queries:
        for page in range(1, pages + 1):
            try:
                data = _get_json(f"https://www.getonbrd.com/api/v0/search/jobs?query={urllib.request.quote(q)}&per_page=50&page={page}&expand=%5B%22company%22%5D")
            except Exception as e:
                print(f"WARN getonbrd q={q}: {e}", file=sys.stderr)
                break
            items = data.get("data") or []
            for it in items:
                a = it.get("attributes") or {}
                url = (it.get("links") or {}).get("public_url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                title = a.get("title") or ""
                sen = (((a.get("seniority") or {}).get("data") or {}).get("id"))
                countries = a.get("countries") or []
                remote = bool(a.get("remote"))
                zone = (a.get("remote_zone") or "") if remote else ""
                if not _tech_entry(title, sen in (1, 2)):
                    continue
                if not ("Argentina" in countries or (remote and (not zone or _AR_LOC_RE.search(str(zone)) or "latam" in str(zone).lower() or "world" in str(zone).lower()))):
                    continue
                ts = a.get("published_at")
                fecha = date.fromtimestamp(ts).isoformat() if isinstance(ts, (int, float)) else ""
                jobs.append({
                    "fecha": fecha, "titulo": title,
                    "empresa": (((a.get("company") or {}).get("data") or {}).get("attributes") or {}).get("name", ""),
                    "ubicacion": ", ".join(countries) or ("Remoto" if remote else ""),
                    "modalidad": a.get("remote_modality") or "", "jornada": {1: "sin experiencia", 2: "junior"}.get(sen, ""),
                    "estado": "GetOnBoard", "url": url,
                })
            if page >= (data.get("meta") or {}).get("total_pages", 1):
                break
    print(f"  -> GetOnBoard: {len(jobs)} (Argentina o remoto alcanzable, sin experiencia/junior)")
    return jobs


def scrape_torre(pages=3):
    """Torre (torre.ai): API de busqueda publica por POST (search.torre.co). Maximo size=20 por pedido
    (con mas devuelve 400), se pagina con offset. Solo abiertas, AR o remoto anywhere/LatAm."""
    queries = ["pasante", "pasantia", "intern", "trainee", "junior", "python", "soporte", "qa", "analista de datos"]
    jobs, seen_ids = [], set()
    results = []
    for q in queries:
        payload = {"and": [{"keywords": {"term": q, "locale": "es"}}]}  # la API no acepta filtro de estado: se filtra abajo
        for p in range(pages):
            try:
                data = _post_json(f"https://search.torre.co/opportunities/_search/?size=20&offset={p * 20}&lang=es", payload)
            except Exception as e:
                print(f"WARN torre q={q}: {e}", file=sys.stderr)
                break
            batch = data.get("results") or []
            results.extend(batch)
            if len(batch) < 20:
                break
    for r in results:
        oid = r.get("id")
        if not oid or oid in seen_ids:
            continue
        seen_ids.add(oid)
        if r.get("status") != "open":
            continue
        title = r.get("objective") or ""
        locs = r.get("locations") or []
        anywhere = bool((r.get("place") or {}).get("anywhere"))
        if not _tech_entry(title, r.get("opportunity") == "intern"):
            continue
        if not ("Argentina" in locs or anywhere or any(_AR_LOC_RE.search(l) for l in locs)):
            continue
        org = ((r.get("organizations") or [{}])[0]).get("name", "")
        jobs.append({
            "fecha": (r.get("created") or "")[:10], "titulo": title, "empresa": org,
            "ubicacion": ", ".join(locs) or ("Remoto (anywhere)" if anywhere else ""),
            "modalidad": "Remoto" if r.get("remote") else "", "jornada": r.get("type") or "",
            "estado": "Torre", "url": f"https://torre.ai/post/{oid}",
        })
    print(f"  -> Torre: {len(jobs)} abiertas (AR o remoto alcanzable)")
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
    ap.add_argument("--scrape", choices=["linkedin", "cosign", "startups", "yc", "speedrun", "getonbrd", "torre", "computrabajo", "becasit", "empleosit", "telegram", "bumeran", "uade", "wellfound", "all"], help="scrapeo de avisos")
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
        # "all" = fuentes que funcionan sin login. Wellfound (SPA) queda fuera; UADE y X se revisan en el navegador.
        tracker = _load_tracker()
        selected = ["linkedin", "cosign", "startups", "yc", "speedrun", "getonbrd", "torre", "computrabajo", "becasit", "empleosit", "telegram", "bumeran", "uade"] if args.scrape == "all" else [args.scrape]
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
            elif name == "cosign":
                jobs = scrape_cosign()
            elif name == "getonbrd":
                jobs = scrape_getonbrd()
            elif name == "torre":
                jobs = scrape_torre()
            elif name == "wellfound":
                # Wellfound es una SPA con login: no hay listado scrapeable. Queda como link manual (--links).
                print("  -> Wellfound: 0 (SPA con login; revisar a mano con --links)")
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
            for j in jobs:
                j["tracker"] = _tracker_mark(j, tracker)
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
