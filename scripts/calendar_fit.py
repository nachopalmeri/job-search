import re
from datetime import time

BLOCKS = [
    ("UADE", [(0, time(18,45), time(22,15)), (1, time(18,30), time(22,0)), (2, time(18,45), time(22,15)), (3, time(18,45), time(22,15)), (4, time(18,45), time(22,15))]),
    ("Psicologa", [(0, time(14,15), time(15,15))]),
    ("Ritual", [(4, time(10,0), time(12,30))]),
]

def parse_jornada(jornada: str):
    m = re.search(r"(\d{1,2})-(\d{1,2})", jornada)
    if not m:
        return None
    return time(int(m.group(1)),0), time(int(m.group(2)),0)

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
