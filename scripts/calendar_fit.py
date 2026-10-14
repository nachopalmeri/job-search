import re
from datetime import time

BLOCKS = [
    ("UADE", [(0, time(18,45), time(22,15)), (1, time(18,30), time(22,0)), (2, time(18,45), time(22,15)), (3, time(18,45), time(22,15)), (4, time(18,45), time(22,15))]),
    ("Psicologa", [(0, time(14,15), time(15,15))]),
    ("Ritual", [(4, time(10,0), time(12,30))]),
]

def parse_jornada(jornada: str):
    m = re.search(
        r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(?:-|–|—|\ba\b|\bhasta\b)\s*"
        r"(\d{1,2})(?::(\d{2}))?(?!\d)",
        jornada,
        re.IGNORECASE,
    )
    if not m:
        return None
    start_hour, start_minute, end_hour, end_minute = (
        int(m.group(1)), int(m.group(2) or 0), int(m.group(3)), int(m.group(4) or 0)
    )
    if start_hour > 23 or end_hour > 23 or start_minute > 59 or end_minute > 59:
        return None
    start, end = time(start_hour, start_minute), time(end_hour, end_minute)
    if end <= start:
        return None
    return start, end

def score_compat(jornada: str, weekday: int = None) -> int:
    parsed = parse_jornada(jornada)
    if not parsed:
        return 80
    start, end = parsed
    penalty = 0
    for name, blocks in BLOCKS:
        for wd, bstart, bend in blocks:
            if weekday is not None and wd != weekday:
                continue
            if not (end <= bstart or start >= bend):
                if name == "UADE":
                    return 0
                penalty += 30 if name=="Psicologa" else 20
    return max(0, 100 - penalty)
