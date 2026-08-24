"""GetOnBoard scraper — pasantías part-time AR."""
import re
from html import unescape

def _clean(t): return re.sub(r"\s+", " ", unescape(t)).strip()

def scrape_getonbrd(html):
    jobs=[]
    for block in re.split(r'<div class="gb-results__item', html)[1:]:
        title = _clean(re.search(r'<a[^>]*class="[^"]*gb-results__title[^"]*"[^>]*>(.*?)</a>', block, re.S).group(1)) if re.search(r'gb-results__title', block) else ""
        href = re.search(r'href="([^"]+)"', block).group(1) if re.search(r'href="([^"]+)"', block) else ""
        if href and href.startswith("/"): href="https://www.getonbrd.com"+href
        company = _clean(re.search(r'gb-results__company[^>]*>(.*?)</', block, re.S).group(1)) if re.search(r'gb-results__company', block) else ""
        if not title: continue
        if not re.search(r"pasant|intern|trainee|junior|part.time", title, re.I): continue
        jobs.append({"titulo":title[:90],"empresa":company[:30],"ubicacion":"CABA/Remote","url":href,"fecha":"","modalidad":"","jornada":"","estado":"GetOnBoard"})
    return jobs
