# Rúbrica de fit — evaluación de postulaciones

Adaptada del framework ai-job-search (MadsLorentzen). Cada oportunidad se puntúa 1-5 en 5 dimensiones. Deal-breakers veto.

## Dimensiones (peso)

| Dimensión | Peso | Qué mira |
|---|---|---|
| Habilidades | 30% | ¿Usa Python/automatización/APIs/Linux/SQL? ¿Pide algo que no tengo? |
| Experiencia/edu | 25% | ¿Estudiante de sistemas es excluyente? ¿Exige seniority que no tengo? |
| Ubicación/horario | 20% | ¿Part-time 20hs? ¿AMBA/híbrido? ¿Choca con cursada noche? |
| Alineación carrera | 15% | ¿Es IA/data/IT? ¿Escalable a mi objetivo (pasantía → puesto real)? |
| Demanda del puesto | 10% | ¿Realmente necesitan cubrir (campaña activa, recrutando activo)? |

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