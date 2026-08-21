#!/usr/bin/env python3
"""
crm_followup.py -- Bot Telegram ping si no hay follow-up (Sprint 3 CRM)

Lee tracker/applications.csv (fecha_followup +7d, contacto_interno, estado)
y notifica via Telegram si fecha_followup <= hoy (o vencida) y estado no final.

Uso:
  python scripts/crm_followup.py --dry-run          # solo lista, no envia
  python scripts/crm_followup.py --check            # lista vencidos y propone mensaje
  python scripts/crm_followup.py --send             # envia real (requiere .secrets/telegram_token.json)
  TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python scripts/crm_followup.py --send

Secrets (gitignored, ver .gitignore:10):
  .secrets/telegram_token.json  -> {"bot_token":"123:ABC","chat_id":"123456"}
  o env vars TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID

Cron sugerido (lun-vie 09:00 AMBA):
  0 9 * * 1-5 cd /path/job-search && py scripts/crm_followup.py --send >> radar/crm.log 2>&1

Sin creds -> dry-run seguro (no HIGH_RISK).
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "tracker" / "applications.csv"
SECRETS = ROOT / ".secrets" / "telegram_token.json"

FINAL_STATES = {"descartada", "descartadas", "rechazo", "oferta", "radar 2027", "radar"}
HOLD_STATES = {"backup", "semana", "evaluar", "dudosa", "verificar", "pendiente"}

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
        print(f"ERROR no existe {path}", file=sys.stderr); sys.exit(2)
    txt = path.read_bytes().decode("utf-8-sig", errors="ignore")
    rows = []
    header = None
    header_idx = None
    cols = []
    for i, line in enumerate(txt.splitlines()):
        if not line.strip() or line.strip().startswith("#"):
            continue
        if header is None:
            header = line.strip()
            cols = [c.strip() for c in header.split("|")]
            header_idx = i
            continue
        parts = line.split("|")
        if len(parts) < len(cols):
            parts += [""] * (len(cols) - len(parts))
        row = dict(zip(cols, parts))
        row["_line"] = i+1
        rows.append(row)
    return cols, rows

def due_rows(rows, cols, today=None):
    if today is None:
        today = date.today()
    due = []
    has_follow = "fecha_followup" in cols
    has_contact = "contacto_interno" in cols
    for r in rows:
        estado = r.get("estado","").strip().lower()
        if estado in FINAL_STATES:
            continue
        # si no tiene fecha_followup y es hold, skip
        follow = r.get("fecha_followup","").strip() if has_follow else ""
        if not follow:
            continue
        try:
            d = datetime.strptime(follow, "%Y-%m-%d").date()
        except Exception:
            continue
        # vencido o vence hoy / manana
        delta = (d - today).days
        if delta <= 1:  # incluye vencidos y manana
            r["_delta"] = delta
            r["_has_contact"] = bool(r.get("contacto_interno","").strip()) if has_contact else False
            due.append(r)
    # ordenar por delta (vencidos primero)
    due.sort(key=lambda x: x["_delta"])
    return due

def format_msg(r):
    titulo = r.get("titulo","")
    empresa = r.get("empresa","")
    estado = r.get("estado","")
    link = r.get("link","")
    contacto = r.get("contacto_interno","").strip() or "(sin contacto - agregar en Sheets col K)"
    follow = r.get("fecha_followup","")
    delta = r.get("_delta", 0)
    when = "VENCIDO" if delta < 0 else "HOY" if delta == 0 else "manana"
    # truncar link
    link_s = link[:80] if len(link) > 80 else link
    return f"[ALERT] Follow-up {when} ({follow}): {empresa} - {titulo} [{estado}] - contacto: {contacto} - {link_s}"

def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent":"job-search-crm/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        j = json.loads(body)
        if not j.get("ok"):
            raise RuntimeError(f"Telegram API error: {body}")
        return j

def main():
    ap = argparse.ArgumentParser(description="CRM follow-up Telegram ping")
    ap.add_argument("--csv", default=str(CSV))
    ap.add_argument("--dry-run", action="store_true", help="Solo lista, no envia")
    ap.add_argument("--check", action="store_true", help="Alias dry-run verboso")
    ap.add_argument("--send", action="store_true", help="Envia real a Telegram")
    ap.add_argument("--today", help="Override hoy YYYY-MM-DD (para test)")
    args = ap.parse_args()
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    cols, rows = parse_csv(Path(args.csv))
    if "fecha_followup" not in cols:
        print(f"WARN {args.csv} no tiene fecha_followup - correr python scripts/migrate_tracker_add_crm.py --backfill", file=sys.stderr)
    due = due_rows(rows, cols, today=today)
    if not due:
        print(f"OK {today}: 0 follow-ups vencidos/hoy (total {len(rows)} filas)")
        sys.exit(0)
    print(f"Follow-ups {today}: {len(due)} vencidos/hoy/manana (de {len(rows)} filas):")
    for r in due:
        print(f"  [{r['_delta']:+d}d] L{r['_line']} {format_msg(r)}")
    if args.send and not args.dry_run and not args.check:
        tok, chat = load_token()
        if not tok or not chat:
            print("ERROR falta TELEGRAM_BOT_TOKEN/CHAT_ID - poner en .secrets/telegram_token.json o env (ver header)", file=sys.stderr)
            print("  Ejemplo .secrets/telegram_token.json: {\"bot_token\":\"123:ABC\",\"chat_id\":\"123456\"}", file=sys.stderr)
            print("  Sin creds se hace dry-run. No se envia.", file=sys.stderr)
            sys.exit(2)
        sent = 0
        for r in due:
            msg = format_msg(r)
            try:
                send_telegram(tok, chat, msg)
                print(f"SENT -> {chat}: {msg[:80]}")
                sent += 1
            except Exception as e:
                print(f"FAIL send: {e}", file=sys.stderr)
        print(f"Enviados {sent}/{len(due)}")
    else:
        if args.send:
            print("(dry-run) --send requiere creds, no se envio (usar --send sin --dry-run con token)")
        else:
            print("(dry-run) no se envio - usar --send con token para notificar")

if __name__ == "__main__":
    main()
