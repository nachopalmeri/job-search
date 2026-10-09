"""Importar texto visible de Empleos UADE sin inventar fechas ni enlaces.

Uso: python scripts/uade_import.py --text <export.txt> [--json <salida.json>]
El archivo lo copia el usuario desde su sesión. Nunca maneja credenciales ni postula.
"""

import argparse
import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path

PORTAL_URL = "https://www.empleos.uade.edu.ar/Postulaciones"
HEADER = re.compile(r"(?im)^B[uú]squeda\s+(20\d{2}-\d{3,5})\s*\((\d{2}/\d{2}/\d{4})\)\s*$")


def parse_list(text: str, career: str = "Sin carrera específica") -> list[dict]:
    text = unescape(text).replace("\xa0", " ")
    found = list(HEADER.finditer(text))
    rows = []
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(text)
        lines = [line.strip() for line in text[match.end():end].splitlines() if line.strip()]
        if not lines:
            continue
        title = re.sub(r"\s*Postularse\s*$", "", lines[0], flags=re.I).strip()
        try:
            posted = datetime.strptime(match.group(2), "%d/%m/%Y").date().isoformat()
        except ValueError:
            posted = ""
        description = "\n".join(lines[1:])
        employer = ""
        employer_match = re.search(
            r"(?im)^(.{2,75}?)\s+(?:se encuentra en la b[uú]squeda|busca incorporar|busca sumar|busca un|busca una)\b",
            description,
        )
        if employer_match:
            employer = employer_match.group(1).strip(" .")
        location_match = re.search(r"(?im)^(?:Lugar(?: de trabajo)?|Ubicaci[oó]n)\s*:\s*(.+)$", description)
        modality_match = re.search(r"(?im)^Modalidad\s*:\s*(.+)$", description)
        hours_match = re.search(r"(?i)\b(?:\d+\s*horas?\s*diarias|\d+\s*h(?:oras)?\s*/\s*semana|full[- ]?time|part[- ]?time)\b", description)
        rows.append({
            "portal": "uade", "job_id": match.group(1), "fecha": posted,
            "titulo": title, "empresa": employer,
            "ubicacion": location_match.group(1).strip() if location_match else "",
            "modalidad": modality_match.group(1).strip() if modality_match else "",
            "jornada": hours_match.group(0) if hours_match else "",
            "estado": "", "url": PORTAL_URL,
            "carrera_filtro": career, "descripcion": description,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Leer aviso UADE exportado desde el navegador")
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--career", default="Sin carrera específica")
    parser.add_argument("--json", type=Path, help="archivo de salida opcional")
    args = parser.parse_args()
    rows = parse_list(args.text.read_text(encoding="utf-8-sig"), args.career)
    if args.json:
        args.json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"UADE: {len(rows)} avisos con ID; {sum(bool(row['fecha']) for row in rows)} con fecha original válida")
    for row in rows:
        print(f"{row['job_id']} | {row['fecha'] or 'SIN FECHA'} | {row['titulo']}")


if __name__ == "__main__":
    main()
