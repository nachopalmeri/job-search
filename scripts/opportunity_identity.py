"""Stable and conservative identity helpers for job observations."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_KEYS = {"ref", "source", "campaign", "trk", "trackingid", "mc_cid", "mc_eid"}


def normalize(value: object) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def canonical_url(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw)
    if not parsed.scheme or not parsed.netloc:
        return raw.split("#", 1)[0].rstrip("/")
    query = [
        (key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_KEYS
    ]
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), urlencode(query), ""))


def identity_key(job: dict, *, source_hint: str = "") -> tuple[str, str]:
    """Return (key, confidence): stable source ID, exact URL, or conservative content fingerprint."""
    source = normalize(job.get("portal") or source_hint) or "unknown-source"
    job_id = str(job.get("job_id") or job.get("id") or "").strip()
    if job_id:
        return f"source-id:{source}:{job_id}", "stable_id"
    url = canonical_url(job.get("url") or job.get("link"))
    if url:
        return f"url:{url}", "canonical_url"

    # A content fallback is source/date scoped and includes the full description;
    # company/title/location alone are deliberately insufficient to merge rows.
    fields = [
        source,
        normalize(job.get("empresa") or job.get("company")),
        normalize(job.get("titulo") or job.get("title")),
        normalize(job.get("ubicacion") or job.get("location")),
        str(job.get("fecha") or job.get("published_date") or "")[:10],
        normalize(job.get("descripcion") or job.get("description")),
    ]
    digest = hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()[:20]
    return f"content:{source}:{digest}", "content_fingerprint"


def observation(job: dict, *, source_hint: str = "") -> dict:
    source = normalize(job.get("portal") or source_hint) or "unknown-source"
    return {
        "source": source,
        "job_id": str(job.get("job_id") or job.get("id") or ""),
        "url": str(job.get("url") or job.get("link") or "").strip(),
        "canonical_url": canonical_url(job.get("url") or job.get("link")),
        "publication_date": str(job.get("fecha") or job.get("published_date") or "")[:10],
        "company": str(job.get("empresa") or job.get("company") or ""),
        "title": str(job.get("titulo") or job.get("title") or ""),
        "location": str(job.get("ubicacion") or job.get("location") or ""),
        "description": str(job.get("descripcion") or job.get("description") or ""),
    }
