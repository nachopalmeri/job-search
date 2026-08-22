# Life Context Spec — vida real de Nacho (21/08/2026)

Evidencia:
- Calendar `google_workspace_listCalendarEvents:1` 50 eventos 01/08-07/09: UADE Lun-Vie 18:45-22:15, Psicóloga Lun 14:15, Ritual Vie 10-12:30, Startup World Cup 21/08 18:00 vs UADE 18:45.
- Gmail `google_workspace_searchGmail:1` 15 msgs: Wetcom Fátima 21/08 15:00 "seguimos avanzando", Tetra Pak 20/08 Thank you, Bumeran 21/08 Ya recibieron.
- Sheets `1CFP-AKbxUBNPNtUwTD7ADwNq63reIm1XMoHAXrt9wq8` Postulaciones 21 filas, Dashboard 17 activos, Contactos Wetcom.

Uso:
- `calendar_fit.py` penaliza jornadas que pisan bloques.
- `gmail_sync.py` auto-actualiza tracker.
- `life_prioritizer.py` boostea Wetcom entrevista.
- `daily_digest.py` evita recomendar en huecos ocupados.

Validación: `pytest`, `calendar_fit --check`, `gmail_sync --dry-run`.
