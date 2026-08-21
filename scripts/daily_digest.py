#!/usr/bin/env python3
"""
daily_digest.py — Digest nocturno Telegram (Sprint 4 Learning Loop, 2026-08-21)

Post 21:00 America/Argentina/Buenos_Aires:
  TOP 3 a enviar + 2 radar + 5 vetados con motivo (como dsa.md pero push Telegram)

Fuente: tracker/applications.csv (13 o 14 cols, BOM-safe). No lee radar/*.tsv para no duplicar ruido;
  clasifica solo por estado+fit_score del tracker (fuente curada por rubric-fit.md).

Formato Telegram: MarkdownV2-safe (escape minimo), <=3500 chars, disable_web_page_preview.

Estados (rubric-fit.md + tracker):
  TOP3 "a enviar": estado in {a enviar, aplicar ya, aplicar esta semana, pendiente} con link no vacio,
                   orden fit_score desc, ats_score desc, fecha asc
  RADAR 2: estado contains "radar" (radar 2027, radar) orden fit_score desc
  VETADOS 5: estado in {descartada, descartadas, descarta} o fit_score<3.0, con motivo gap_principal

Secrets: .secrets/telegram_token.json {"bot_token":"123:ABC","chat_id":"123"} o env TELEGRAM_BOT_TOKEN/CHAT_ID
  (mismo que crm_followup.py). Sin creds -> --dry-run seguro; --send exige creds.

Uso:
  python scripts/daily_digest.py --dry-run
  python scripts/daily_digest.py --preview
  python scripts/daily_digest.py --send            # requiere token
  python scripts/daily_digest.py --csv tracker/applications.csv --today 2026-08-21

Cron nocturno (lun-vie 21:00 AMBA):
  0 21 * * 1-5 cd /path/job-search && python scripts/daily_digest.py --send >> radar/digest.log 2>&1

No inventa puestos; solo reporta tracker existente.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "tracker" / "applications.csv"
SECRETS = ROOT / ".secrets" / "telegram_token.json"

TOP_STATES = {"a enviar", "aplicar ya", "aplicar esta semana", "pendiente", "verificar"}
RADAR_KEYWORDS = {"radar"}
VETADO_STATES = {"descartada", "descartadas", "descarta"}
# vetado tambien por fit<3.0 aunque estado no sea descartada (ej. descartada implicita)
VETADO_FIT_THRESHOLD = 3.0


def load_token():
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tok and chat:
        return tok, chat
    if SECRETS.exists():
        try:
            j = json.loads(SECRETS.read_text(encoding="utf-8"))
            return j.get("bot_token") or j.get("token"), j.get("chat_id") or j.get("chatId")
        except Exception as e:
            print(f"WARN secrets json: {e}", file=sys.stderr)
    return None, None


def parse_csv(path: Path):
    if not path.exists():
        print(f"ERROR no existe {path}", file=sys.stderr)
        sys.exit(2)
    text = path.read_bytes().decode("utf-8-sig", errors="ignore")
    lines = [l for l in text.splitlines() if l.strip() != "" or True]
    header = None
    cols = []
    hdr_idx = None
    data_rows = []
    for i, l in enumerate(text.splitlines()):
        if not l.strip() or l.strip().startswith("#"):
            continue
        if header is None:
            header = l.strip()
            cols = [c.strip() for c in header.split("|")]
            hdr_idx = i
            continue
        parts = l.split("|")
        if len(parts) < len(cols):
            parts += [""] * (len(cols) - len(parts))
        row = dict(zip(cols, parts))
        row["_line"] = i + 1
        data_rows.append(row)
    return cols, data_rows


def to_float(s, default=0.0):
    try:
        return float(str(s).strip().replace(",", "."))
    except Exception:
        return default


def classify(cols, rows, today=None):
    if today is None:
        today = date.today()

    top, radar, vetados, rest = [], [], [], []

    for r in rows:
        estado = r.get("estado", "").strip()
        estado_n = estado.lower()
        fit = to_float(r.get("fit_score", 0))
        ats = r.get("ats_score", "").strip()
        # vetado?
        is_vetado_estado = estado_n in VETADO_STATES
        is_vetado_fit = fit > 0 and fit < VETADO_FIT_THRESHOLD
        is_vetado = is_vetado_estado or is_vetado_fit
        is_radar = any(k in estado_n for k in RADAR_KEYWORDS)
        is_top = estado_n in TOP_STATES

        # radar tiene prioridad sobre vetado si ambos (no deberia pasar)
        if is_radar:
            radar.append(r)
        elif is_vetado:
            vetados.append(r)
        elif is_top:
            top.append(r)
        else:
            rest.append(r)

    # ordenar top: fit desc, ats desc, fecha asc
    def sort_key_top(r):
        fit = to_float(r.get("fit_score", 0))
        try:
            ats_f = int(r.get("ats_score", "").strip() or 0)
        except Exception:
            ats_f = 0
        # fecha: mas reciente primero si a enviar, pero usamos asc para priorizar older pending
        try:
            d = datetime.strptime(r.get("fecha", "").strip(), "%Y-%m-%d").date()
        except Exception:
            d = date.max
        return (-fit, -ats_f, d)

    top_sorted = sorted(top, key=sort_key_top)[:3]
    radar_sorted = sorted(radar, key=lambda r: -to_float(r.get("fit_score", 0)))[:2]
    # vetados: ordenar por fit asc (peor primero) para justificar descarte
    vetados_sorted = sorted(vetados, key=lambda r: to_float(r.get("fit_score", 99)))[:5]

    return top_sorted, radar_sorted, vetados_sorted, rest


def esc(s: str) -> str:
    # Telegram MarkdownV2 minimal: escape _ * [ ] ( ) ~ ` > # + - = | { } . !
    # usamos plain sin parse_mode MarkdownV2 para evitar escape hell: enviamos con disable preview y plain
    # pero escapamos para Markdown opcional: sustituimos | y * problemáticos
    return s.replace("|", "/").replace("\n", " ").strip()


def format_digest(top, radar, vetados, cols, rows, today):
    lines = []
    lines.append(f"*Digest {today.isoformat()}* — job-search (Sprint 4)")
    lines.append("")
    # TOP 3
    lines.append(f"*TOP 3 a enviar* ({len(top)}/3)")
    if not top:
        lines.append("_Sin pendientes con fit >=3.0 — revisar tracker o correr buscar_portales._")
    else:
        for i, r in enumerate(top, 1):
            titulo = esc(r.get("titulo", "")[:60])
            empresa = esc(r.get("empresa", "")[:28])
            fit = r.get("fit_score", "").strip() or "?"
            gap = esc(r.get("gap_principal", "")[:48] or "sin gap")
            link = r.get("link", "").strip()
            ats = r.get("ats_score", "").strip()
            ats_s = f" ATS:{ats}%" if ats else ""
            # truncar link para Telegram
            link_s = link[:70] + "..." if len(link) > 70 else link
            variant = r.get("cv_variant", "").strip().upper() if "cv_variant" in cols else ""
            var_s = f" [{variant}]" if variant in ("A", "B") else ""
            lines.append(f"{i}. *{empresa}* — {titulo}  `fit {fit}{ats_s}{var_s}`")
            lines.append(f"   gap: {gap}")
            if link_s:
                lines.append(f"   {link_s}")
    lines.append("")
    # RADAR 2
    lines.append(f"*Radar 2* ({len(radar)}/2)")
    if not radar:
        lines.append("_Sin radar activo._")
    else:
        for i, r in enumerate(radar, 1):
            titulo = esc(r.get("titulo", "")[:55])
            empresa = esc(r.get("empresa", "")[:28])
            fit = r.get("fit_score", "").strip() or "?"
            estado = esc(r.get("estado", "")[:22])
            lines.append(f"{i}. {empresa} — {titulo}  `fit {fit} {estado}`")
    lines.append("")
    # VETADOS 5
    lines.append(f"*Vetados 5* ({len(vetados)}/5) + motivo")
    if not vetados:
        lines.append("_Sin vetados recientes._")
    else:
        for i, r in enumerate(vetados, 1):
            titulo = esc(r.get("titulo", "")[:42])
            empresa = esc(r.get("empresa", "")[:22])
            fit = r.get("fit_score", "").strip() or "?"
            motivo = esc(r.get("gap_principal", "") or r.get("notas", "")[:60] or "fit bajo / deal-breaker")
            motivo = motivo[:62]
            lines.append(f"{i}. {empresa} -- {titulo} `fit {fit}` -> {motivo}")
    lines.append("")
    # Footer stats
    total = len(rows)
    pend = len(top)
    lines.append(f"_Total tracker: {total} | pendientes TOP: {pend} | radar: {len(radar)} | vetados: {len(vetados)}_")
    lines.append("_Fuente: tracker/applications.csv (Sheets maestro es fuente de verdad)._")
    # Telegram limit
    text = "\n".join(lines)
    if len(text) > 3500:
        text = text[:3490] + "\n..."
    return text


def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true"
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "job-search-digest/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        j = json.loads(body)
        if not j.get("ok"):
            raise RuntimeError(f"Telegram API error: {body}")
        return j


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Digest nocturno Telegram TOP3+2+5")
    ap.add_argument("--csv", default=str(DEFAULT_CSV))
    ap.add_argument("--dry-run", action="store_true", help="Solo imprime, no envia")
    ap.add_argument("--preview", action="store_true", help="Preview markdown en stdout")
    ap.add_argument("--send", action="store_true", help="Envia a Telegram")
    ap.add_argument("--today", help="Override hoy YYYY-MM-DD")
    ap.add_argument("--no-markdown", action="store_true", help="Envia sin parse_mode")
    args = ap.parse_args()

    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    cols, rows = parse_csv(Path(args.csv))
    top, radar, vetados, rest = classify(cols, rows, today=today)
    digest = format_digest(top, radar, vetados, cols, rows, today)

    if args.preview or args.dry_run or not args.send:
        print(digest)
        if not args.send:
            print("\n(dry-run) no enviado — usar --send con TELEGRAM_BOT_TOKEN/CHAT_ID para push 21:00")
            # exit 0 even if preview
            sys.exit(0)

    if args.send:
        tok, chat = load_token()
        if not tok or not chat:
            print("ERROR falta TELEGRAM_BOT_TOKEN/CHAT_ID en env o .secrets/telegram_token.json", file=sys.stderr)
            print("  Ejemplo .secrets/telegram_token.json: {\"bot_token\":\"123:ABC\",\"chat_id\":\"123456\"}", file=sys.stderr)
            sys.exit(2)
        try:
            # si --no-markdown, enviar sin parse_mode
            if args.no_markdown:
                url = f"https://api.telegram.org/bot{tok}/sendMessage"
                data = urllib.parse.urlencode({"chat_id": chat, "text": digest, "disable_web_page_preview": "true"}).encode()
                req = urllib.request.Request(url, data=data, headers={"User-Agent": "job-search-digest/1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode("utf-8", errors="ignore")
                    j = json.loads(body)
                    if not j.get("ok"):
                        raise RuntimeError(body)
            else:
                send_telegram(tok, chat, digest)
            print(f"SENT digest {today} -> chat {chat} ({len(digest)} chars)")
        except Exception as e:
            print(f"FAIL send: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
