import re
import sys
from pathlib import Path

PATTERNS = [
    (re.compile(r"Thank you for your interest|profile has been successfully created", re.I), "aplicada"),
    (re.compile(r"Ya recibieron tu postulaci[oó]n", re.I), "aplicada"),
    (re.compile(r"seguimos avanzando|todav[ií]a no tenemos.*decisi[oó]n", re.I), "entrevista"),
]

def parse_gmail_to_status(subject, sender, body=""):
    text = f"{subject} {body}"
    for pat, status in PATTERNS:
        if pat.search(text):
            return status
    return None

def sync(dry_run=True):
    print("dry-run" if dry_run else "sync")

if __name__ == "__main__":
    print("dry-run" if "--dry-run" in sys.argv else "sync")
