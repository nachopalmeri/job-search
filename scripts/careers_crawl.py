"""Careers direct crawl — 10 ATS target (Lever/Greenhouse/Workday/BambooHR).

Uso:
  python scripts/careers_crawl.py --check         # solo lista URLs y estado HTTP
  python scripts/careers_crawl.py --scrape       # intenta extraer pasantías part-time (heurística)
"""
import re
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

TARGETS = [
    ("Globant", "https://career.globant.com/", "SmartRecruiters"),
    ("Mercado Libre", "https://careers-meli.mercadolibre.com/es/positions", "Meli"),
    ("Despegar", "https://jobs.lever.co/despegar", "Lever"),
    ("Accenture", "https://accenture.wd3.myworkdayjobs.com/AccentureCareers", "Workday"),
    ("IBM", "https://www.ibm.com/careers", "Workday"),
    ("Tiendanube", "https://nuvemshop-tiendanube.inhire.app/tiendanube", "InHire"),
    ("Uala", "https://www.ua.la/sumate", "Custom"),
    ("Satellogic", "https://satellogic.bamboohr.com/careers", "BambooHR"),
    ("PedidosYa", "https://jobs.smartrecruiters.com/DeliveryHero", "SmartRecruiters"),
    ("SAP", "https://jobs.sap.com", "SuccessFactors"),
]

def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace"), r.status

def check():
    for name, url, ats in TARGETS:
        try:
            _, status = _get(url)
            print(f"[OK {status}] {name:14} {ats:16} {url}")
        except Exception as e:
            print(f"[FAIL] {name:14} {ats:16} {url} -> {e}")

def scrape():
    # Heurística simple: buscar "pasant" en HTML
    for name, url, ats in TARGETS:
        try:
            html, _ = _get(url)
            hits = len(re.findall(r"pasant|intern|trainee", html, re.I))
            print(f"{name:14} hits={hits:2} {url}")
            if hits:
                for m in re.finditer(r'>([^<]*pasant[^<]{5,60})<', html, re.I):
                    print(f"  - {_clean(m.group(1))[:80]}")
        except Exception as e:
            print(f"{name} error: {e}")

def _clean(t):
    import html as h
    return re.sub(r"\s+", " ", h.unescape(t)).strip()

if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        check()
    else:
        scrape()
