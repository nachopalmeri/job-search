# Rúbrica de fit — evaluación de postulaciones

Adaptada del framework ai-job-search (MadsLorentzen). Cada oportunidad se puntúa 1-5 en 5 dimensiones. Deal-breakers veto.

## Dimensiones (peso) — v2 life-context (21/08/2026)

| Dimensión | Peso | Qué mira |
|---|---|---|
| Evidencia en bullets | 40% | ¿Tus bullets muestran verb+resultado+keyword JD? (ATS 2026 parsea bullets, no walls) |
| Jornada | 25% | ¿Part-time 20hs Lun-Vie mañana/tarde? (full-time = veto) |
| Compatibilidad horaria real | 15% | vs Calendar: UADE 18:45-22:15 veto, Psicóloga Lun 14:15 -30, Ritual Vie 10-12:30 -20 (`scripts/calendar_fit.py:1`) |
| Carrera | 15% | ¿Es IA/data/IT escalable a puesto real? |
| Demanda | 5% | Señal externa ruidosa, solo ordena backlog |

## Deal-breakers (veto directo, score final 0)

- Exige inglés certificado avanzado/fluent (tengo B1+/B2 sin cert).
- Exige full-time sin opción part-time.
- Exige título o 3er año (puede pedir "últimos años" → revisar con cuidado, ver IBM).
- Fuera de AMBA sin remoto.
- Empresa/rol que exigiría mentir en CV para postular.

## Escala

- 4.5–5.0 → Aplicar YA (hoy)
- 4.0–4.4 → Aplicar esta semana
- 3.0–3.9 → Aplicar solo si sobra tiempo / plan B
- <3.0 → Descartar o marcar "seguir de lejos"

## Output por oportunidad evaluada (para tracker)

```
fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas
```

estado: aplicada, aplicando, descartada, pendiente, entrevista, oferta, rechazo, silencio