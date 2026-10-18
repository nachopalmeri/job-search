import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.request
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit, urlunsplit
import webbrowser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

FEEDS_YAML = Path(__file__).resolve().parent / "feeds_telegram.yaml"
ATS_BOARDS_FILE = Path(__file__).resolve().parent / "ats_boards.json"

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
    "uade": "https://www.empleos.uade.edu.ar/Postulaciones",
    "firstjob": "https://www.firstjob.com",
    "wellfound": "https://wellfound.com/role/l/intern/Argentina",
    "getonbrd": "https://www.getonbrd.com/empleos/programacion?per_page=20&search={kw}",
    "torre": "https://torre.ai/search/jobs?q={kw}",
    "cosign": "https://cosign.co/jobs",
    "startupsargentina": "https://www.startupsargentina.com/empleos",
    "linkedin": "https://www.linkedin.com/jobs/search?keywords=pasantia&location=Argentina&f_TPR=r345600",
    "getonbrd_ar": "https://www.getonbrd.com.ar/trabajo/{kw}",
}

LINKEDIN_URL = "https://www.linkedin.com/jobs/search"
MAX_AGE_DAYS = 4
AUTOMATED_SOURCES = ("greenhouse", "lever", "ashby", "startups", "yc", "speedrun", "cosign", "getonbrd", "torre", "computrabajo", "becasit", "empleosit", "jobicy", "himalayas", "remotive", "arbeitnow", "linkedin", "cafedev")
LINKEDIN_MAX_AGE_DAYS = MAX_AGE_DAYS
LINKEDIN_QUERIES = [
    "pasantía",
    "pasante sistemas",
    "pasantía tecnología",
    "internship IT",
    "trainee tecnología",
    "soporte IT junior",
    "analista de datos junior",
    "QA intern",
    "analista funcional junior",
    "automatización junior",
    "customer success intern",
    "product operations intern",
    "application support analyst Argentina",
    "implementation analyst Buenos Aires",
    "business systems analyst Argentina",
    "reporting analyst entry level Argentina",
    "financial operations analyst junior Argentina",
    "AI operations analyst Argentina",
    "AI adoption intern Argentina",
    "IT operations associate Argentina",
    "service desk analyst Argentina",
    "network support trainee Argentina",
    "cloud support associate Argentina",
    "cybersecurity intern Argentina",
    "ERP SAP trainee Argentina",
    "PMO technology analyst junior Argentina",
    "product analyst intern Argentina",
    "risk analytics junior Argentina",
    "automation specialist entry level Argentina",
    "technical customer success associate Argentina",
    "technology graduate program Argentina",
]
X_SEARCH_QUERIES = [
    'pasantía IT',
    'pasante sistemas',
    'trainee tecnología',
    'buscamos pasante soporte',
    'pasantía datos',
    '#EmpleoIT pasante',
    '"buscamos" "desarrollador jr"',
    '"buscamos" "analista junior" datos',
    '"sumate" automatización junior',
    '"estamos buscando" (trainee OR pasante) tecnología',
    '"oportunidad laboral" (junior OR pasantía) IT',
]
LINKEDIN_POST_QUERIES = [
    '"buscamos pasantes" (sistemas OR tecnología OR datos) Argentina',
    '"desarrollador/a jr" (software OR IA) Argentina',
    '"pasantía" (soporte OR infraestructura OR redes) Buenos Aires',
    '"buscamos" ("analista junior" OR "business analyst junior") Argentina',
    '"internship" (technology OR data OR product) "Buenos Aires"',
]
STARTUPS_URL = "https://www.startupsargentina.com/empleos"
COMPUTRABAJO_URL = "https://ar.computrabajo.com/trabajo-de-{kw}"
BECASIT_URL = "https://becasit.itechcareer.com/pasant%C3%ADas"
EMPLEOSIT_RSS = "https://www.empleosit.com.ar/rss/"

RADAR_DIR = Path(__file__).resolve().parent.parent / "radar"
SEEN_FILE = RADAR_DIR / "seen_jobs.json"
TSV_HEADER = "portal|fecha|fecha_portal|titulo|empresa|ubicacion|modalidad|jornada|estado|url|nuevo|tracker|job_id|descripcion|apply_url"
UNVERIFIED_HEADER = TSV_HEADER + "|motivo"
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
    today = date.today()
    since = (today - timedelta(days=MAX_AGE_DAYS)).isoformat()
    until = (today + timedelta(days=1)).isoformat()
    for query in X_SEARCH_QUERIES:
        params = {"q": f"{query} since:{since} until:{until}", "f": "live"}
        out.append(f"x_twitter | https://x.com/search?{urlencode(params)}")
    for query in LINKEDIN_POST_QUERIES:
        params = {"q": f"site:linkedin.com/posts/ {query} after:{since}", "tbs": "qdr:d3"}
        out.append(f"linkedin_posts | https://www.google.com/search?{urlencode(params)}")
    return out


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def _clean(text):
    return re.sub(r"\s+", " ", unescape(str(text or ""))).strip()


# --- Cruce contra el tracker de Nacho (tracker/postulaciones.csv): empresa + puesto, nunca solo la empresa ---
_TRK_STOP = {"argentina", "group", "inc", "llc", "ltd", "srl", "sas", "company", "the", "and", "for", "remote", "latam", "labs", "tech"}
_SPANISH_MONTHS = {
    "ene": 1, "enero": 1, "feb": 2, "febrero": 2, "mar": 3, "marzo": 3,
    "abr": 4, "abril": 4, "may": 5, "mayo": 5, "jun": 6, "junio": 6,
    "jul": 7, "julio": 7, "ago": 8, "agosto": 8, "sep": 9, "sept": 9,
    "septiembre": 9, "setiembre": 9, "oct": 10, "octubre": 10, "nov": 11,
    "noviembre": 11, "dic": 12, "diciembre": 12,
}


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _tokens(s):
    return {t for t in _norm(s).split() if len(t) >= 3 and t not in _TRK_STOP}   # >=3: entran IBM, SAP, ABB


def _same_company(a_tokens, b_tokens):
    """Misma empresa aunque el nombre varie: 'JPMorgan' vs 'JPMorganChase' (prefijo de 5+ letras) o palabra en comun."""
    return any(x == y or (min(len(x), len(y)) >= 5 and (x.startswith(y) or y.startswith(x))) for x in a_tokens for y in b_tokens)


def _load_tracker():
    """Estado del aviso exacto en el tracker, incluyendo pendientes para no re-descubrirlos como nuevos."""
    out = []
    if not TRACKER_CSV.exists():
        return out
    with TRACKER_CSV.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            est = (r.get("estado") or "").strip()
            if not est:
                continue
            label = "PARA_POSTULAR" if est == "Para postular" else ("DESCARTADA" if est == "Descartada" else "REGISTRADA")
            out.append((_tokens(r.get("empresa")), _norm(r.get("puesto")),
                        (r.get("link") or "").split("?")[0].strip().lower(),
                        label))
    return out


_UADE_ID_RE = re.compile(r"\b20\d{2}-\d{3,5}\b")
_GENERIC_PORTAL_URLS = {
    "https://www.empleos.uade.edu.ar",
    "https://www.empleos.uade.edu.ar/",
    "https://www.empleos.uade.edu.ar/postulaciones",
}


def _tracker_mark(job, tracker):
    """'PARA_POSTULAR' / 'REGISTRADA' / 'DESCARTADA' si el aviso ya está en tracker; '' si es nuevo.
    Un enlace genérico al portal UADE no identifica una oferta individual."""
    url = (job.get("url") or "").split("?")[0].strip().lower()
    emp, tit = _tokens(job.get("empresa")), _norm(job.get("titulo"))
    job_id = str(job.get("job_id") or "")
    if not _UADE_ID_RE.fullmatch(job_id):
        match = _UADE_ID_RE.search(f"{job.get('titulo', '')} {job.get('url', '')}")
        job_id = match.group() if match else ""
    for toks, puesto, link, label in tracker:
        match = _UADE_ID_RE.search(f"{puesto} {link}")
        tracker_id = match.group() if match else ""
        if job_id and tracker_id:
            if job_id == tracker_id:
                return label
            continue
        if url and link and url == link and url not in _GENERIC_PORTAL_URLS:
            return label
        if not _same_company(emp, toks) or not tit or not puesto:
            continue
        short, long_ = sorted((tit, puesto), key=len)
        wa, wb = set(tit.split()), set(puesto.split())
        # palabras completas: "Analista BI" vs "Analista IA" NO es el mismo aviso (por letras se parecerian)
        if tit == puesto or (len(short.split()) >= 3 and long_.startswith(short)) or len(wa & wb) / len(wa | wb) >= 0.8:
            return label
    return ""


def _seen_key(job):
    job_id = str(job.get("job_id") or "")
    if job.get("portal") == "uade" and _UADE_ID_RE.fullmatch(job_id):
        return f"uade:{job_id}"
    company, title, location = (_norm(job.get(k, "")) for k in ("empresa", "titulo", "ubicacion"))
    if company and title:
        return f"fingerprint:{company}|{title}|{location}"
    raw_url = (job.get("url") or "").strip()
    if raw_url:
        parts = urlsplit(raw_url)
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/").lower(), "", ""))
    return f"fallback:{job.get('portal','')}|{title}|{location}".lower()


def _legacy_seen_url(job):
    """URL-key migration for seen_jobs.json created before stable employer/title fingerprints."""
    if job.get("portal") == "uade":
        return ""
    return (job.get("url") or "").strip().split("?")[0]


def _job_fingerprint(job):
    job_id = str(job.get("job_id") or "")
    if job.get("portal") == "uade" and _UADE_ID_RE.fullmatch(job_id):
        return f"uade:{job_id}"
    company, title, location = (_norm(job.get(k, "")) for k in ("empresa", "titulo", "ubicacion"))
    if location and _REMOTE_OK_RE.search(location) and not _FOREIGN_GEO_RE.search(location):
        location = "argentina-or-remote"
    return f"{company}|{title}|{location}" if company and title else ""


def _safe_source(name, function, *args, **kwargs):
    """Aísla fallos por portal para que una API caída no cancele el resto de la pasada."""
    try:
        return function(*args, **kwargs)
    except Exception as exc:
        print(f"WARN {name}: {type(exc).__name__}: {exc}; se continúa con las demás fuentes", file=sys.stderr)
        return []


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
                row = [j.get(k, "") for k in ["fecha", "fecha_portal", "titulo", "empresa", "ubicacion", "modalidad", "jornada", "estado", "url", "nuevo", "tracker", "job_id", "descripcion", "apply_url"]]
                row = [re.sub(r"\s+", " ", str(v)).replace("|", "/")[:8000] for v in row]
                fh.write(f"{portal}|" + "|".join(row) + "\n")
    for j in jobs:
        print(f"{portal} | {j['titulo']} | {j['empresa']} | {j['ubicacion']} | {j['fecha']} | {j['modalidad']} | {j['jornada']} | {j['estado']} | {j['url']} | {j.get('nuevo','')} | {j.get('tracker','')} | {j.get('job_id','')}")


def _linkedin_search_url(keywords):
    """Construye la consulta con Boolean, espacios y acentos escapados correctamente."""
    params = {
        "keywords": keywords,
        "location": "Argentina",
        "f_TPR": f"r{LINKEDIN_MAX_AGE_DAYS * 24 * 60 * 60}",
    }
    return f"{LINKEDIN_URL}?{urlencode(params)}"


def scrape_linkedin(kw):
    jobs = []
    html = _get(_linkedin_search_url(kw))
    stale_or_future = 0
    unknown_date = 0
    cutoff = date.today() - timedelta(days=LINKEDIN_MAX_AGE_DAYS)
    for block in re.split(r'data-entity-urn="urn:li:jobPosting:', html)[1:]:
        job_id = block.split('"', 1)[0]
        href = _first(r'href="([^"]*linkedin\.com/jobs/view/[^"?]+)', block)
        if not job_id.isdigit() and not href:
            continue
        published = _first(r'job-search-card__listdate" datetime="([^" ]+)', block)
        try:
            published_day = date.fromisoformat(published[:10])
        except (TypeError, ValueError):
            unknown_date += 1
            continue
        if published_day < cutoff or published_day > date.today():
            stale_or_future += 1
            continue
        title = _first(r'base-search-card__title">(.*?)</h3>', block)
        company = _first(r'hidden-nested-link[^>]*>\s*(.*?)\s*</a>', block)
        location = _first(r'job-search-card__location">(.*?)</span>', block)
        hiring = "Actively Hiring" if _first(r'job-posting-benefits__text">(.*?)</span>', block) else ""
        if not title and not company:
            continue
        canonical_url = f"https://www.linkedin.com/jobs/view/{job_id}" if job_id.isdigit() else href.split("?", 1)[0].rstrip("/")
        jobs.append({
            "fecha": published_day.isoformat(), "titulo": title, "empresa": company, "ubicacion": location,
            "modalidad": "", "jornada": "", "estado": hiring, "url": canonical_url, "job_id": job_id,
        })
    if stale_or_future or unknown_date:
        print(f"  LinkedIn {kw[:48]}: excluidos {stale_or_future} fuera de fecha y {unknown_date} sin fecha verificable")
    return jobs


def _posted_date(raw, today=None):
    """Parsea fechas absolutas y relativas comunes; None significa que no se puede verificar."""
    if not raw:
        return None
    today = today or date.today()
    value = _clean(str(raw)).strip().lower()
    if value in {"hoy", "today", "just posted", "recién publicado", "recien publicado"}:
        return today
    if value in {"ayer", "yesterday"}:
        return today - timedelta(days=1)
    relative = re.search(
        r"(?:(?:hace|publicado(?:\s+hace)?|posted)\s+)?(\d+|un|una|one)\s*"
        r"(min(?:ute|uto)?s?|horas?|hours?|hrs?|h|d[ií]as?|days?|d|semanas?|weeks?|w|"
        r"mes(?:es)?|months?|mo|a[nñ]os?|years?|y)\b\s*(?:ago)?",
        value,
    )
    if relative:
        amount_raw, unit = relative.groups()
        amount = {"un": 1, "una": 1, "one": 1}.get(amount_raw, int(amount_raw) if amount_raw.isdigit() else 1)
        if unit.startswith(("min", "hor", "hour", "hr", "h")):
            return today
        if unit.startswith("sem") or unit.startswith("week"):
            amount *= 7
        elif unit.startswith(("mes", "month", "mo")):
            amount *= 30
        elif unit.startswith(("a", "year", "y")):
            amount *= 365
        return today - timedelta(days=amount)
    iso = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[Tt ](.*))?$", value)
    if iso:
        try:
            return date.fromisoformat(iso.group(1))
        except ValueError:
            return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    spanish = re.fullmatch(r"(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)\.?\s+(?:de\s+)?(\d{4})", value)
    if spanish:
        month = _SPANISH_MONTHS.get(spanish.group(2).replace("é", "e").replace("á", "a"))
        if month:
            try:
                return date(int(spanish.group(3)), month, int(spanish.group(1)))
            except ValueError:
                pass
    return None


def _filter_fresh(jobs, portal, max_age_days=MAX_AGE_DAYS, today=None, unverified_path=None, secondary_path=None):
    """Puerta final común: solo deja avisos con fecha verificable dentro de la ventana configurada."""
    today = today or date.today()
    fresh, secondary, unverified, stale, future = [], [], [], 0, 0
    for job in jobs:
        posted = _posted_date(job.get("fecha"), today)
        if posted is None:
            observed = job.get("fecha_portal")
            reason = "fecha original no verificable" + (f"; fecha del portal {observed}" if observed else "")
            if "GEO_NO_VERIFICADA" in str(job.get("estado", "")):
                reason += "; elegibilidad geográfica no verificable"
            unverified.append((job, reason))
        elif posted > today:
            future += 1
            unverified.append((job, "fecha futura; requiere validar el aviso original"))
        elif "GEO_NO_VERIFICADA" in str(job.get("estado", "")):
            unverified.append((job, "elegibilidad geográfica no verificable; confirmar el aviso original"))
        elif (today - posted).days > max_age_days:
            age = (today - posted).days
            if age <= 14:
                secondary.append((job, f"publicado hace {age} días; ventana secundaria 5–14 días"))
            else:
                stale += 1
        else:
            if portal in {"linkedin", "computrabajo", "speedrun"}:
                unverified.append((job, "fecha del portal dentro de la ventana configurada; confirmar primera publicación en empleador/ATS"))
            else:
                fresh.append(job)
    if unverified_path and unverified:
        with unverified_path.open("a", encoding="utf-8") as fh:
            for job, reason in unverified:
                values = [portal] + [job.get(k, "") for k in ("fecha", "fecha_portal", "titulo", "empresa", "ubicacion", "modalidad", "jornada", "estado", "url", "nuevo", "tracker", "job_id", "descripcion", "apply_url")] + [reason]
                fh.write("|".join(re.sub(r"\s+", " ", str(v)).replace("|", "/")[:8000] for v in values) + "\n")
    if unverified or secondary or stale:
        print(f"  -> Vigencia {portal}: {len(fresh)} vigentes; {stale} antiguos; {future} futuros y {len(unverified)-future} pendientes de fecha, fuente o elegibilidad" + (f" (detalle: {unverified_path})" if unverified_path and unverified else ""))
    return fresh, [job for job, _ in secondary]


# --- Filtros de relevancia para fuentes grandes (Startups Argentina / YC / Speedrun) ---
# Regla v3 (25/09/2026): full-time YA NO es veto. Se descarta solo por seniority claramente alto.
_SENIOR_RE = re.compile(r"\b(senior|sr\.?|staff|principal|lead|leader|head|director|vp|manager|architect|cto|cfo|chief|ssr|semi[- ]?senior|expert|ii|iii|iv)\b", re.I)
# Regla v4 (28/09/2026): lo que manda es "sin experiencia" (intern/trainee/junior) y que acepte Argentina.
# Una palabra de entrada en el titulo gana sobre la de seniority ("Product Manager Intern", "Jr. Team Lead" pasan).
_ENTRY_RE = re.compile(r"(intern|pasant|junior|\bjr\b|trainee|becari|practicante|entry|new grad|graduate|apprentic|"
                       r"fellow|early career|emerging talent|j[oó]venes|estudiante|student|sin experiencia|primer empleo)", re.I)
_ENTRY_TECH_RE = re.compile(
    _ENTRY_RE.pattern[:-1] + r"|"
    r"support|soporte|help ?desk|\bqa\b|tester|test |data|datos|python|automat|\bai\b|\bia\b|\bml\b|prompt|"
    r"sistemas|developer|desarrollador|engineer|software|implementation|onboarding|"
    r"customer success|technical|it operations|devops|"
    r"analyst|analista|operations|operaciones|\bops\b|growth|research|business|associate|asistente|assistant|"
    r"no.?code|low.?code|zapier|n8n|llm|gpt|agent|agente|crm|\bbi\b|product)", re.I)


def _is_senior(title):
    t = title or ""
    return bool(_SENIOR_RE.search(t)) and not _ENTRY_RE.search(t)


def _relevant(title):
    t = title or ""
    # Recall-first discovery: seniority is an eligibility decision after the
    # full description is read. A title may say "Manager/Engineer" yet be a
    # campus or associate programme; do not drop it here.
    return bool(_ENTRY_TECH_RE.search(t))


# Para agregadores masivos (Cosign, Torre, Get on Board) "intern"/"junior" solo no alcanza: tiene que ser tech/ops tecnico,
# pero se acepta tambien ops/analista/growth/research: es el tipo de rol de entrada que Nacho puede tomar.
_TECH_RE = re.compile(
    r"(support|soporte|help ?desk|\bqa\b|tester|testing|data|datos|python|automat|\bai\b|\bia\b|\bml\b|machine learning|prompt|"
    r"sistemas|developer|desarrollador|engineer|ingenier|software|programad|implementation|implementaci|onboarding|"
    r"customer success|technical|t[eé]cnic|\bit\b|tecnolog|devops|cloud|backend|frontend|full.?stack|analytics|analista|"
    r"product|security|seguridad|infra|network|redes|sql|web|"
    r"analyst|operations|operaciones|\bops\b|growth|research|business|no.?code|low.?code|zapier|n8n|llm|gpt|agent|agente|"
    r"crm|\bbi\b|excel|process|proceso|solutions|customer|cx\b|digital)", re.I)


def _tech_entry(title, entry_hint=False):
    t = title or ""
    if not _TECH_RE.search(t):
        return False
    return bool(entry_hint or _relevant(t) or _TECH_RE.search(t))


_REMOTE_OK_RE = re.compile(
    r"(?i:argentina|argentinian|latin america|latam|south america|americas|worldwide|global|anywhere|"
    r"buenos aires|caba|ciudad autonoma|cordoba|rosario|mendoza|santa fe|la plata|mar del plata|amba)|\bar\b", re.I
)
_US_ONLY_RE = re.compile(
    r"\b(?:us|usa|united states|canada|uk|united kingdom|eu|europe|india)\s*(?:only|exclusive)\b|"
    r"\b(?:only|must be based in|based in|authorized to work in|eligible to work in)\s+(?:the\s+)?"
    r"(?:us|usa|united states|canada|uk|united kingdom|india)\b|"
    r"\b(?:remote|remoto)\s+(?:in\s+)?(?:us|usa|united states|canada|uk|india)\b|"
    r"\b(?:remote|remoto)\s*[-:–—(\[]\s*(?:us|usa|united states|canada|uk|india)\b",
    re.I,
)


def _remote_ok(loc):
    """Remoto alcanzable desde Argentina: acepta LatAm/Argentina/Worldwide o 'Remote' a secas (ambiguo, se revisa a mano).
    Rechaza 'Remote (US)', 'Toronto ... / Remote', 'Remote (FR)' y cualquier remoto atado a otra region/pais."""
    l = (loc or "").strip()
    if _US_ONLY_RE.search(l):
        return False
    if _REMOTE_OK_RE.search(l):
        return True
    return bool(re.fullmatch(r"remote|remoto|remote \(worldwide\)|anywhere", l, re.I))


# --- Filtro anti-estafas (28/09/2026) ---
# Se aplica a TODAS las fuentes antes de escribir el TSV. Lo descartado va a radar/estafas-<fecha>.tsv
# para poder revisarlo, nunca al reporte. Lista negra editable en scripts/estafas.txt.
ESTAFAS_FILE = Path(__file__).resolve().parent / "estafas.txt"
_SCAM_TITLE_RE = re.compile(
    r"(paid survey|encuestas? pagas?|focus group|panel(ista)?s? de|mystery shopper|cliente oculto|"
    r"earn (up to|\$)|gan[aá] (hasta|desde) \$|ingresos? extra|dinero r[aá]pido|work from home.*\$|"
    r"sin experiencia.*\$\s?\d{3,}.*(d[ií]a|hora)|data entry.*(remote|remoto).*\$|"
    r"(crypto|cripto|forex) (trad|invers|invest)|trading (assistant|trainee)|trader trainee|"
    r"reshipp|package (handler|forward)|reenv[ií]o de paquetes|payment (processing )?agent|agente de pagos|"
    r"money transfer|transferencias? de dinero|"
    r"pag[aá] (la|tu) capacitaci|training fee|registration fee|inscripci[oó]n paga|"
    r"multinivel|mlm|network marketing|"
    r"(contact|escrib|envi[aá]).{0,25}(whats ?app|telegram))", re.I)
_SCAM_URL_RE = re.compile(r"(bit\.ly|tinyurl|t\.me/|wa\.me/|chat\.whatsapp|forms\.gle|linktr\.ee|\.(xyz|top|click|icu)(/|$))", re.I)


def _load_scam_list():
    try:
        lines = ESTAFAS_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [l.strip().lower() for l in lines if l.strip() and not l.lstrip().startswith("#")]


def _scam_reason(j, blocklist):
    """Motivo si el aviso es una estafa probable; '' si pasa. Solo senales fuertes: ante la duda pasa y se lee a mano."""
    empresa = (j.get("empresa") or "").strip()
    url = j.get("url") or ""
    hay = f"{empresa} {url}".lower()
    for b in blocklist:
        if b in hay:
            return f"lista negra: {b}"
    if _SCAM_TITLE_RE.search(j.get("titulo") or ""):
        return "titulo con patron de estafa"
    if _SCAM_URL_RE.search(url):
        return "link acortado, de mensajeria o dominio de riesgo"
    # Torre y Get on Board permiten avisos sin empresa: sin empresa identificable no se puede verificar nada.
    if j.get("estado") in ("Torre", "GetOnBoard") and not empresa:
        return "sin empresa identificable"
    return ""


def _filter_scams(jobs, portal, blocklist, out_path=None):
    ok, bad = [], []
    for j in jobs:
        why = _scam_reason(j, blocklist)
        (bad if why else ok).append((j, why))
    if bad:
        print(f"  -> {portal}: {len(bad)} descartados por posible estafa")
        if out_path:
            with out_path.open("a", encoding="utf-8") as f:
                for j, why in bad:
                    f.write("|".join([portal, why, j.get("titulo", ""), j.get("empresa", ""), j.get("url", "")]) + "\n")
    return [j for j, _ in ok]


def _get_json(url):
    """Speedrun (Cloudflare) rechaza el UA completo del script pero acepta uno simple."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def _get_json_with_retry(url, retries=2):
    """Retry transient public API errors, respecting Retry-After and keeping waits bounded."""
    for attempt in range(retries + 1):
        try:
            return _get_json(url)
        except HTTPError as exc:
            transient = exc.code == 429 or 500 <= exc.code <= 599
            if not transient or attempt >= retries:
                raise
            raw_delay = exc.headers.get("Retry-After", "") if exc.headers else ""
            try:
                delay = float(raw_delay)
            except (TypeError, ValueError):
                try:
                    retry_at = parsedate_to_datetime(raw_delay)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=timezone.utc)
                    delay = max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
                except (TypeError, ValueError, OverflowError):
                    delay = float(2 ** attempt)
            if delay > 30:
                raise
            time.sleep(max(0.0, delay))


def scrape_cafedev():
    """Discover broad and junior jobs via CafeDev's documented public REST API.

    CafeDev's published_at is treated as an aggregator signal only; first_seen_at
    is never copied into fecha because it is an indexing timestamp, not the
    employer's original publication date. Candidates stay in the unverified
    queue until checked against the employer/ATS.
    """
    base = "https://api.cafedev.co/v1/jobs"
    # The API's q parameter is documented for text search. A single empty
    # query can hide roles when the board is larger than the pagination cap.
    queries = ("", "junior", "trainee", "intern", "internship", "graduate",
               "early career", "pasantia", "practicante", "entry level",
               "IT support", "data analyst", "QA", "cybersecurity",
               "automation", "business analyst")
    jobs, seen, request_count, last_request = [], set(), 0, 0.0
    max_requests, request_interval = 50, 1.05  # Conservative pacing; keep below 60 requests/minute.
    for query in queries:
        if request_count >= max_requests:
            print(f"  -> CafeDev: alcanzado límite local de {max_requests} solicitudes; quedan consultas para la próxima pasada", file=sys.stderr)
            break
        params = {"limit": 100}
        if query:
            params["q"] = query
        page = 1
        while page <= 5:
            if request_count >= max_requests:
                break
            wait = request_interval - (time.monotonic() - last_request)
            if request_count and wait > 0:
                time.sleep(wait)
            params["page"] = page
            payload = _get_json_with_retry(base + "?" + urlencode(params))
            last_request = time.monotonic()
            request_count += 1
            if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
                raise ValueError("respuesta CafeDev inválida: se esperaba objeto con items")
            items = payload["items"]
            for row in items:
                job_id = str(row.get("id") or "").strip()
                title = _clean(row.get("title"))
                company = _clean(row.get("company_name"))
                job_url = str(row.get("url") or "").strip()
                apply_url = str(row.get("apply_url") or "").strip()
                job_parts, apply_parts = urlsplit(job_url), urlsplit(apply_url)
                if (not job_id or job_id in seen or not title or not company
                        or job_parts.scheme != "https" or job_parts.hostname != "cafedev.co"
                        or not job_parts.path.startswith("/empleos/")
                        or apply_parts.scheme != "https" or not apply_parts.hostname):
                    continue
                # Keep senior-titled records in discovery so age/seniority is
                # assessed from the original description instead of silently
                # disappearing at the connector boundary.
                if not _tech_entry(title):
                    continue
                seen.add(job_id)
                countries = {str(value).strip().lower() for value in (row.get("countries") or [])}
                country = str(row.get("country") or "").strip().lower()
                explicitly_eligible = {str(value).strip().lower() for value in (row.get("eligible_countries") or [])}
                if explicitly_eligible:
                    countries = explicitly_eligible
                if countries and not ({"ar", "argentina"} & countries):
                    # Do not surface jobs whose explicit country eligibility excludes Argentina.
                    continue
                remote = str(row.get("workplace_type") or "").strip().lower() == "remote"
                location = _clean(row.get("city"))
                country_names = {
                    "ar": "Argentina", "br": "Brasil", "cl": "Chile", "co": "Colombia",
                    "cr": "Costa Rica", "mx": "México", "uy": "Uruguay", "pe": "Perú",
                    "us": "Estados Unidos", "es": "España",
                }
                if country in country_names:
                    location = f"{location}, {country_names[country]}" if location else country_names[country]
                elif country in {"ar", "argentina"}:
                    location = f"{location}, Argentina" if location else "Argentina"
                elif not countries and remote:
                    location = location or "Remote (elegibilidad por confirmar)"
                else:
                    location = location or "Ubicación no informada"
                if country not in {"", "ar", "argentina"} and ({"ar", "argentina"} & countries):
                    location = f"{location} (acepta Argentina)"
                skills = row.get("skills") or []
                category = _clean(row.get("category"))
                meta = "; ".join(part for part in (
                    f"Categoría: {category}" if category else "",
                    f"Tecnologías/skills: {', '.join(map(str, skills))}" if skills else "",
                    f"CafeDev first_seen_at (no es fecha de publicación): {row.get('first_seen_at')}" if row.get("first_seen_at") else "",
                ) if part)
                jobs.append({
                    "fecha": "", "fecha_portal": _clean(row.get("published_at")),
                    "titulo": title, "empresa": company, "ubicacion": location,
                    "modalidad": "Remoto" if remote else _clean(row.get("workplace_type")),
                    "jornada": _clean(row.get("employment_type")),
                    "estado": "GEO_NO_VERIFICADA" if not ({"ar", "argentina"} & countries) else "",
                    "url": job_url, "apply_url": apply_url, "job_id": job_id,
                    "descripcion": meta,
                })
            pages = int(payload.get("pages") or page)
            if page >= pages or not items:
                break
            page += 1
    print(f"  -> CafeDev API: {len(jobs)} señales tecnológicas/entry; {request_count} solicitudes con paginación y consultas amplias; fecha original pendiente de verificar")
    return jobs


def _load_ats_boards(ats):
    """Carga sólo tableros ATS públicos previamente verificados, sin descubrir tokens por scraping."""
    try:
        data = json.loads(ATS_BOARDS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"WARN ATS: no se pudo leer {ATS_BOARDS_FILE.name}: {exc}", file=sys.stderr)
        return []
    return [row for row in data if row.get("ats", "").lower() == ats]


_ARGENTINA_GEO_RE = re.compile(
    r"\b(argentina|argentinian|latam|latin america|south america|americas|"
    r"buenos aires|caba|ciudad autonoma|cordoba|rosario|mendoza|santa fe|la plata|mar del plata|amba)\b", re.I
)
_ATS_DESC_GEO_RE = re.compile(
    r"\b(argentina|argentinian|latam|latin america|south america|americas|buenos aires|caba|"
    r"ciudad autonoma|cordoba|rosario|mendoza|santa fe|la plata|mar del plata|amba|"
    r"remote worldwide|worldwide remote|work from anywhere|anywhere in the world|globally remote)\b", re.I
)
_FOREIGN_GEO_RE = re.compile(
    r"\b(us|usa|u\.s\.|united states|canada|mexico|brazil|chile|colombia|peru|uruguay|"
    r"united kingdom|uk|europe|india|australia|new zealand|singapore|philippines|poland)\b", re.I
)


def _ats_candidate(title, location, description):
    """Reduce ruido ATS: rol relacionado al perfil y ubicación compatible/ambigua para revisión manual."""
    # Search title plus description so "Operations Associate" can survive
    # when its actual responsibilities involve SQL, automation, or systems.
    search_text = f"{title}\n{_clean(description[:3000])}"
    if not _TECH_RE.search(search_text):
        return False
    if _US_ONLY_RE.search(f"{location} {description[:2200]}"):
        return False
    if _remote_ok(location):
        return True
    if _FOREIGN_GEO_RE.search(location) and not _ARGENTINA_GEO_RE.search(location):
        return False
    # Algunas bolsas publican una ciudad genérica y detallan elegibilidad en el aviso.
    # No usar la descripción corporativa completa: sólo su encabezado geográfico.
    geo_context = _clean(description[:1800])
    return bool(_ATS_DESC_GEO_RE.search(geo_context))


def scrape_ats(ats):
    """Lee tableros Greenhouse/Lever/Ashby; nunca envía formularios."""
    boards = _load_ats_boards(ats)
    jobs, failures, fetched = [], 0, 0
    for board in boards:
        token = board.get("token", "").strip()
        company = board.get("company", "").strip()
        if not token or not company:
            print(f"WARN {ats}: tablero incompleto omitido ({board.get('id', 'sin id')})", file=sys.stderr)
            failures += 1
            continue
        if ats == "greenhouse":
            url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        elif ats == "lever":
            url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        else:
            url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
        try:
            payload = _get_json(url)
            if ats == "greenhouse" and (not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list)):
                raise ValueError("respuesta Greenhouse sin la lista jobs esperada")
            rows = payload.get("jobs", []) if isinstance(payload, dict) and ats in {"greenhouse", "ashby"} else payload
            if ats == "ashby" and not isinstance(payload, dict):
                raise ValueError("respuesta Ashby sin objeto JSON")
            if not isinstance(rows, list):
                raise ValueError("respuesta JSON sin lista de avisos")
            fetched += len(rows)
        except Exception as exc:
            failures += 1
            print(f"WARN {ats} board={board.get('id', token)}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        for row in rows:
            if ats == "greenhouse":
                title = _clean(row.get("title", ""))
                location = _clean((row.get("location") or {}).get("name", ""))
                description = _clean(re.sub(r"<[^>]+>", " ", row.get("content", "") or ""))[:8000]
                posted = row.get("first_published", "") or ""
                link = row.get("absolute_url", "")
                workplace = "Remoto" if re.search(r"remote|remoto|anywhere", location, re.I) else ""
                commitment = ""
                employer = _clean(row.get("company_name", "")) or company
            elif ats == "lever":
                title = _clean(row.get("text", "") or row.get("title", ""))
                categories = row.get("categories") or {}
                location = _clean(
                    categories.get("location", "")
                    or ", ".join(categories.get("allLocations", []) or [])
                )
                description = row.get("descriptionPlain", "") or row.get("descriptionBodyPlain", "") or ""
                created = row.get("createdAt")
                try:
                    posted = datetime.fromtimestamp(float(created) / 1000, tz=timezone.utc).date().isoformat() if created else ""
                except (TypeError, ValueError, OSError, OverflowError):
                    posted = ""
                link = row.get("hostedUrl", "")
                workplace = _clean(row.get("workplaceType", ""))
                commitment = _clean(categories.get("commitment", ""))
                employer = company
            else:
                title = _clean(row.get("title", ""))
                location = _clean(row.get("location", ""))
                description = _clean(row.get("descriptionPlain", ""))[:8000]
                posted = _clean(row.get("publishedAt", ""))[:10]
                link = row.get("applyUrl") or row.get("jobUrl") or ""
                workplace = _clean(row.get("workplaceType", ""))
                commitment = _clean(row.get("employmentType", ""))
                employer = company
            if not title or not link or not _ats_candidate(title, location, description):
                continue
            jobs.append({
                "fecha": posted, "titulo": title, "empresa": employer, "ubicacion": location,
                "modalidad": workplace, "jornada": commitment, "estado": "", "url": link,
                "job_id": str(row.get("id", "")),
                "descripcion": description,
            })
    print(f"  -> {ats.title()}: {len(boards)-failures}/{len(boards)} tableros respondieron; {fetched} avisos leídos; {len(jobs)} candidatos por rol/ubicación")
    return jobs


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
            # Startups Argentina ya es 100% Argentina: filtro amplio (v4), saca senior y lo que no es tech/ops/datos/analista.
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
            jobs.append({
                "fecha": "", "titulo": title, "empresa": f"{company} ({batch})" if batch else company,
                "ubicacion": loc, "modalidad": jtype, "jornada": salary, "estado": "YC",
                "url": f"https://www.ycombinator.com{href}",
            })
    print(f"  -> YC Work at a Startup: {len(jobs)} (remoto alcanzable desde AR)")
    return jobs


def scrape_speedrun(pages=3):
    """a16z Speedrun Talent Network. Discovery is broad; score eligibility later."""
    jobs, seen_ids = [], set()
    queries = ["intern", "junior", "entry level", "student", "python", "support", "qa", "automation",
               "data analyst", "business analyst", "operations", "product operations", "IT", "systems", "AI"]
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
                # Seniority is scored after description enrichment, not used
                # as an early discovery veto (title labels can be noisy).
                jobs.append({
                    "fecha": (j.get("published_at") or "")[:10], "titulo": title, "empresa": j.get("company_key", ""),
                    "ubicacion": loc, "modalidad": j.get("employment_type") or "", "jornada": j.get("seniority") or "",
                    "estado": "Speedrun", "url": "https://speedrun-talent-network.com" + j.get("path", ""),
                    "descripcion": _clean(j.get("description") or j.get("description_text") or "")[:8000],
                })
    print(f"  -> a16z Speedrun: {len(jobs)} roles remotos relacionados (eligibilidad pendiente de descripción)")
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
                ("intern", True), ("junior", True), ("trainee", False), ("pasantia", False),
                ("entry level", True), ("new grad", True), ("fellowship", False), ("analyst", True)]
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
                    "descripcion": _clean(a.get("description") or a.get("descriptionText") or "")[:8000],
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
    queries = ["practicante", "pasantia", "trainee", "junior", "intern", "soporte", "qa", "python", "datos",
               "analista", "operaciones", "automatizacion", "inteligencia artificial", "no code"]
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
                argentina = any(str(country).lower() == "argentina" for country in countries)
                region_ok = bool(remote and zone and (_AR_LOC_RE.search(str(zone)) or "latam" in str(zone).lower() or "world" in str(zone).lower()))
                if not (argentina or region_ok or remote):
                    continue
                ts = a.get("published_at")
                fecha = ""
                try:
                    timestamp = float(ts)
                    if timestamp > 100_000_000_000:  # algunos feeds entregan milisegundos
                        timestamp /= 1000
                    fecha = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
                except (TypeError, ValueError, OSError, OverflowError):
                    pass  # El filtro común separa lo que no tenga fecha verificable.
                jobs.append({
                    # published_at puede ser republicación; no prueba la fecha original.
                    "fecha": "", "fecha_portal": fecha, "titulo": title,
                    "empresa": (((a.get("company") or {}).get("data") or {}).get("attributes") or {}).get("name", ""),
                    "ubicacion": ", ".join(countries) or ("Remoto" if remote else ""),
                    "modalidad": a.get("remote_modality") or "", "jornada": {1: "sin experiencia", 2: "junior"}.get(sen, ""),
                    "estado": "FECHA_ORIGINAL_NO_VERIFICADA" + ("; GEO_NO_VERIFICADA" if not (argentina or region_ok) else ""), "url": url,
                    "descripcion": _clean(a.get("description") or a.get("description_html") or "")[:8000],
                })
            if page >= (data.get("meta") or {}).get("total_pages", 1):
                break
    print(f"  -> GetOnBoard: {len(jobs)} candidatos; fecha original y zona remota requieren revisión antes de priorizar")
    return jobs


def scrape_torre(pages=3):
    """Torre (torre.ai): API de busqueda publica por POST (search.torre.co). Maximo size=20 por pedido
    (con mas devuelve 400), se pagina con offset. Solo abiertas, AR o remoto anywhere/LatAm.
    Las 9 busquedas van en paralelo: en serie tardaban ~70 s y hacian que el shell de un agente pasara el comando a segundo plano."""
    endpoint = "https://search.torre.co/opportunities/_search/?size=20&offset=0&lang=es"
    probe = {"and": [{"keywords": {"term": "junior", "locale": "es"}}]}
    try:
        _post_json(endpoint, probe)
    except HTTPError as exc:
        if exc.code == 400:
            print("WARN Torre: la API pública rechaza las consultas (HTTP 400 Invalid request); se detienen los reintentos y queda solo la búsqueda manual", file=sys.stderr)
            return []
        print(f"WARN Torre: prueba de disponibilidad falló (HTTP {exc.code}); queda parcial", file=sys.stderr)
        return []
    except Exception as exc:
        print(f"WARN Torre: prueba de disponibilidad falló ({type(exc).__name__}); queda parcial", file=sys.stderr)
        return []
    queries = ["pasante", "pasantia", "intern", "trainee", "junior", "python", "soporte", "qa", "analista de datos",
               "operaciones", "automatizacion", "inteligencia artificial", "entry level"]
    jobs, seen_ids = [], set()

    def one_query(q):
        payload = {"and": [{"keywords": {"term": q, "locale": "es"}}]}  # la API no acepta filtro de estado: se filtra abajo
        got = []
        for pg in range(pages):
            try:
                data = _post_json(f"https://search.torre.co/opportunities/_search/?size=20&offset={pg * 20}&lang=es", payload)
            except Exception as e:
                print(f"WARN torre q={q}: {e}", file=sys.stderr)
                break
            batch = data.get("results") or []
            got.extend(batch)
            if len(batch) < 20:
                break
        return got

    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        for batch in pool.map(one_query, queries):
            results.extend(batch)
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


def scrape_jobicy(pages=2):
    """Feed público de Jobicy; las fichas quedan pendientes de verificación primaria."""
    jobs, seen = [], set()
    cursor = None
    for _ in range(pages):
        params = {"count": 200}
        if cursor:
            params["cursor"] = cursor
        data = _get_json("https://jobicy.com/api/v2/remote-jobs?" + urlencode(params))
        if not isinstance(data, dict) or data.get("success") is False or not isinstance(data.get("jobs"), list):
            raise ValueError("respuesta Jobicy inválida")
        for row in data["jobs"]:
            job_id = str(row.get("id") or "")
            title = _clean(row.get("jobTitle"))
            location = _clean(row.get("jobGeo"))
            if not job_id or job_id in seen or not title or _is_senior(title) or not _tech_entry(title) or not _remote_ok(location):
                continue
            seen.add(job_id)
            link = row.get("url") or ""
            if not link.startswith("https://"):
                continue
            jobs.append({
                "fecha": row.get("pubDate") or "", "titulo": title,
                "empresa": _clean(row.get("companyName")), "ubicacion": location,
                "modalidad": "Remoto", "jornada": ", ".join(row.get("jobType") or []),
                "estado": "GEO_NO_VERIFICADA", "url": link, "job_id": job_id,
                "descripcion": _clean(re.sub(r"<[^>]+>", " ", row.get("jobDescription") or row.get("jobExcerpt") or ""))[:8000],
            })
        cursor = data.get("nextCursor")
        if not cursor:
            break
    print(f"  -> Jobicy: {len(jobs)} señales relevantes; validar empleador/ATS y Argentina")
    return jobs


def scrape_himalayas():
    """Búsqueda pública acotada a AR; no presume que el aviso original esté vigente."""
    jobs, seen = [], set()
    for query in ("intern", "junior", "trainee", "QA", "AI"):
        params = urlencode({"country": "AR", "q": query, "sort": "recent"})
        data = _get_json("https://himalayas.app/jobs/api/search?" + params)
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ValueError("respuesta Himalayas inválida")
        for row in data["jobs"]:
            job_id = str(row.get("guid") or "")
            title = _clean(row.get("title"))
            restrictions = row.get("locationRestrictions") or []
            allowed = not restrictions or any(str(place).upper() in {"AR", "ARG", "ARGENTINA"} for place in restrictions)
            link = row.get("applicationLink") or ""
            if not job_id or job_id in seen or not title or _is_senior(title) or not _tech_entry(title) or not allowed or not link.startswith("https://"):
                continue
            seen.add(job_id)
            jobs.append({
                "fecha": row.get("pubDate") or "", "titulo": title,
                "empresa": _clean(row.get("companyName")),
                "ubicacion": "Argentina" if restrictions else "Worldwide",
                "modalidad": "Remoto", "jornada": _clean(row.get("employmentType")),
                "estado": "GEO_NO_VERIFICADA", "url": link, "job_id": job_id,
                "descripcion": _clean(re.sub(r"<[^>]+>", " ", row.get("description") or row.get("excerpt") or ""))[:8000],
            })
    print(f"  -> Himalayas: {len(jobs)} señales relevantes; validar empleador/ATS y Argentina")
    return jobs


def scrape_remotive():
    """API pública de Remotive; su feed tiene demoras y se confirma en origen."""
    jobs, seen = [], set()
    for query in ("intern", "junior", "trainee"):
        url = "https://remotive.com/api/remote-jobs?" + urlencode({"search": query, "limit": 100})
        data = _get_json(url)
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ValueError("respuesta Remotive inválida")
        for row in data["jobs"]:
            job_id = str(row.get("id") or "")
            title = _clean(row.get("title"))
            location = _clean(row.get("candidate_required_location"))
            link = row.get("url") or ""
            if not job_id or job_id in seen or not title or _is_senior(title) or not _tech_entry(title) or not _remote_ok(location) or not link.startswith("https://"):
                continue
            seen.add(job_id)
            jobs.append({
                "fecha": row.get("publication_date") or "", "titulo": title,
                "empresa": _clean(row.get("company_name")), "ubicacion": location,
                "modalidad": "Remoto", "jornada": _clean(row.get("job_type")),
                "estado": "GEO_NO_VERIFICADA", "url": link, "job_id": job_id,
                "descripcion": _clean(re.sub(r"<[^>]+>", " ", row.get("description") or ""))[:8000],
            })
    print(f"  -> Remotive: {len(jobs)} señales relevantes; validar empleador/ATS y Argentina")
    return jobs


def scrape_arbeitnow():
    """API pública con foco europeo; solo conserva candidatos con alcance global explícito."""
    data = _get_json("https://www.arbeitnow.com/api/job-board-api")
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise ValueError("respuesta Arbeitnow inválida")
    jobs = []
    for row in data["data"]:
        title = _clean(row.get("title"))
        location = _clean(row.get("location"))
        link = row.get("url") or ""
        if not row.get("remote") or not title or _is_senior(title) or not _tech_entry(title) or not _remote_ok(location) or not link.startswith("https://"):
            continue
        created = row.get("created_at")
        try:
            posted = datetime.fromtimestamp(float(created), tz=timezone.utc).date().isoformat() if created else ""
        except (ValueError, TypeError, OSError, OverflowError):
            posted = ""
        jobs.append({
            "fecha": posted, "titulo": title,
            "empresa": _clean(row.get("company_name")), "ubicacion": location,
            "modalidad": "Remoto", "jornada": "",
            "estado": "GEO_NO_VERIFICADA", "url": link,
            "job_id": str(row.get("slug") or ""),
            "descripcion": _clean(re.sub(r"<[^>]+>", " ", row.get("description") or ""))[:8000],
        })
    print(f"  -> Arbeitnow: {len(jobs)} señales globales; validar empleador/ATS y Argentina")
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
    ap.add_argument("--scrape", choices=["linkedin", "cosign", "startups", "yc", "speedrun", "getonbrd", "torre", "computrabajo", "becasit", "empleosit", "jobicy", "himalayas", "remotive", "arbeitnow", "greenhouse", "lever", "ashby", "cafedev", "telegram", "bumeran", "uade", "wellfound", "all"], help="scrapeo de avisos")
    ap.add_argument("--kw", default="pasantia", help="keyword para Computrabajo; LinkedIn usa familias curadas de consultas")
    ap.add_argument("--uade-text", type=Path, help="texto copiado de Búsquedas sin carrera específica en la sesión UADE")
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
        blocklist = _load_scam_list()
        scam_path = None
        if args.write:
            scam_path = RADAR_DIR / f"estafas-{date.today().isoformat()}.tsv"
            scam_path.write_text("portal|motivo|titulo|empresa|url\n", encoding="utf-8")
            unverified_path = RADAR_DIR / f"unverified-{date.today().isoformat()}.tsv"
            unverified_path.write_text(UNVERIFIED_HEADER + "\n", encoding="utf-8")
            secondary_path = RADAR_DIR / f"secondary-{date.today().isoformat()}.tsv"
            secondary_path.write_text(UNVERIFIED_HEADER + "\n", encoding="utf-8")
        else:
            unverified_path = None
            secondary_path = None
        # `all` means sources that work unattended. Login/captcha and disabled feeds remain explicit/manual.
        # ATS/empleadores oficiales primero: si un agregador replica el aviso, se conserva la URL primaria.
        selected = list(AUTOMATED_SOURCES) if args.scrape == "all" else [args.scrape]
        if args.scrape == "all" and args.uade_text:
            selected.append("uade")
        fingerprints_today = set()
        secondary_fingerprints = set()
        for name in selected:
            print(f"## {name.capitalize()}")
            if name == "linkedin":
                # Consultas breves y amplias; deduplica por ID estable.
                linkedin_kws = LINKEDIN_QUERIES
                seen_linkedin_jobs = set()
                jobs = []
                rate_limited = False
                attempted_queries = 0
                zero_yield_streak = 0
                for kw in linkedin_kws:
                    attempted_queries += 1
                    query_new = 0
                    try:
                        for j in scrape_linkedin(kw):
                            key = j.get("job_id") or j["url"].split("?", 1)[0].rstrip("/").lower()
                            if key not in seen_linkedin_jobs:
                                seen_linkedin_jobs.add(key)
                                jobs.append(j)
                                query_new += 1
                    except HTTPError as e:
                        if e.code == 429:
                            print(f"WARN LinkedIn limitó la búsqueda (HTTP 429); se detienen las consultas restantes ({len(linkedin_kws)} familias configuradas).", file=sys.stderr)
                            rate_limited = True
                            break
                        print(f"WARN linkedin kw={kw}: HTTP {e.code}", file=sys.stderr)
                    except Exception as e:
                        print(f"WARN linkedin kw={kw}: {e}", file=sys.stderr)
                    # Bounded query expansion: stop only after broad coverage
                    # is established and eight consecutive variants add no IDs.
                    if attempted_queries >= 12 and query_new == 0:
                        zero_yield_streak += 1
                    else:
                        zero_yield_streak = 0
                    if zero_yield_streak >= 8:
                        print(f"LinkedIn: se detienen variantes sin nuevos IDs tras {attempted_queries} consultas")
                        break
                suffix = " (circuito abierto por 429)" if rate_limited else ""
                print(f"  -> LinkedIn expandido: {len(jobs)} únicos; {attempted_queries}/{len(linkedin_kws)} consultas intentadas{suffix}")
            elif name in ("greenhouse", "lever", "ashby"):
                jobs = scrape_ats(name)
            elif name == "cafedev":
                jobs = _safe_source(name, scrape_cafedev)
            elif name == "startups":
                jobs = _safe_source(name, scrape_startupsargentina)
            elif name == "yc":
                jobs = _safe_source(name, scrape_yc)
            elif name == "speedrun":
                jobs = _safe_source(name, scrape_speedrun)
            elif name == "computrabajo":
                jobs = _safe_source(name, scrape_computrabajo, args.kw)
            elif name == "becasit":
                jobs = _safe_source(name, scrape_becasit)
            elif name == "empleosit":
                jobs = _safe_source(name, scrape_empleosit)
            elif name == "jobicy":
                jobs = _safe_source(name, scrape_jobicy)
            elif name == "himalayas":
                jobs = _safe_source(name, scrape_himalayas)
            elif name == "remotive":
                jobs = _safe_source(name, scrape_remotive)
            elif name == "arbeitnow":
                jobs = _safe_source(name, scrape_arbeitnow)
            elif name == "telegram":
                jobs = _safe_source(name, scrape_telegram_feeds)
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
            elif name == "uade" and args.uade_text:
                try:
                    try:
                        from scripts.uade_import import parse_list
                    except ImportError:
                        from uade_import import parse_list  # type: ignore
                    jobs = parse_list(args.uade_text.read_text(encoding="utf-8-sig"))
                    print(f"  -> UADE, texto de sesión: {len(jobs)} avisos con ID")
                except (OSError, UnicodeError) as e:
                    print(f"WARN UADE texto no legible: {e}", file=sys.stderr)
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
                jobs = _safe_source(name, scrape_cosign)
            elif name == "getonbrd":
                jobs = _safe_source(name, scrape_getonbrd)
            elif name == "torre":
                jobs = _safe_source(name, scrape_torre)
            elif name == "wellfound":
                # Wellfound es una SPA con login: no hay listado scrapeable. Queda como link manual (--links).
                print("  -> Wellfound: 0 (SPA con login; revisar a mano con --links)")
                jobs = []
            else:
                jobs = []
            jobs, secondary_jobs = _filter_fresh(jobs, name, unverified_path=unverified_path, secondary_path=secondary_path)
            jobs = _filter_scams(jobs, name, blocklist, scam_path)
            secondary_jobs = _filter_scams(secondary_jobs, name, blocklist, scam_path)
            secondary_unique = []
            for candidate in secondary_jobs:
                fingerprint = _job_fingerprint(candidate)
                if fingerprint and fingerprint in secondary_fingerprints:
                    continue
                if fingerprint:
                    secondary_fingerprints.add(fingerprint)
                candidate["tracker"] = _tracker_mark(candidate, tracker)
                secondary_unique.append(candidate)
            if args.write and secondary_path:
                with secondary_path.open("a", encoding="utf-8") as fh:
                    for candidate in secondary_unique:
                        posted = _posted_date(candidate.get("fecha"))
                        age = (date.today() - posted).days if posted else ""
                        reason = f"publicado hace {age} días; ventana secundaria 5–14 días" if age != "" else ""
                        values = [name] + [candidate.get(k, "") for k in ("fecha", "fecha_portal", "titulo", "empresa", "ubicacion", "modalidad", "jornada", "estado", "url", "nuevo", "tracker", "job_id", "descripcion", "apply_url")] + [reason]
                        normalized = [re.sub(r"\s+", " ", str(value)).replace("|", "/")[:8000] for value in values]
                        fh.write("|".join(normalized) + "\n")
            unique_jobs = []
            for job in jobs:
                fingerprint = _job_fingerprint(job)
                if fingerprint and fingerprint in fingerprints_today:
                    continue
                if fingerprint:
                    fingerprints_today.add(fingerprint)
                unique_jobs.append(job)
            if len(unique_jobs) != len(jobs):
                print(f"  -> {name}: {len(jobs)-len(unique_jobs)} duplicados entre fuentes omitidos")
            jobs = unique_jobs
            if args.write or args.new:
                seen_today[name] = []
                for j in jobs:
                    key = _seen_key(j)
                    legacy_key = _legacy_seen_url(j)
                    if key not in seen and (not legacy_key or legacy_key not in seen):
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
