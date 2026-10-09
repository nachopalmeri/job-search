# Comparación preliminar de repositorios — 08/10/2026

La comparación evalúa patrones para una búsqueda personal de pasantías y roles junior en Argentina. Las cifras de cada proyecto son afirmaciones de sus autores, no una medición propia. No se instaló ni copió código.

| Proyecto | Patrón útil | Límite para Nacho | Decisión |
| --- | --- | --- | --- |
| [Feashliaa/job-board-aggregator](https://github.com/Feashliaa/job-board-aggregator) | Varios ATS, normalización y catálogo de empresas; MIT para código | El catálogo de empresas tiene CC BY-NC 4.0; en `scripts/scraper.py` Greenhouse usa `updated_at`, que no prueba primera publicación | Adaptar arquitectura de adaptadores; conservar nuestra regla `first_published`; no importar catálogo |
| [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy) | Una interfaz para LinkedIn, Indeed y Glassdoor; MIT | Bloqueos, fechas de portal y geografía siguen sin garantizar elegibilidad ni 3 días originales | Evaluar luego como descubrimiento, sin instalación hoy |
| [atharvguitarist/resume-rag](https://github.com/atharvguitarist/resume-rag) | Recuperación híbrida BM25 + semántica, requisitos obligatorios y razones por dimensión | Demostración con corpus sintético; licencia no verificada en la portada; introduce dependencias y datos personales | Usar el patrón conceptual de evidencia por requisito; no copiar código ni añadir RAG aún |
| [wickfeed/ats-job-aggregator](https://github.com/wickfeed/ats-job-aggregator) | API pública por ATS, esquema común y detección de cambios/cierres; MIT | Servicio Apify con costo por uso; sólo dos commits visibles al revisar | No contratar ni integrar; considerar un diff local de cierre |
| [jayakrishnan98/Job-Search-agent](https://github.com/jayakrishnan98/Job-Search-agent) | SQLite con ID por fuente y hash empresa+título+ubicación; pausa LinkedIn ante 429 | Poca actividad; licencia no visible; automatiza emails y modelos con costo opcional | Mantener deduplicación local y límite por fuente; no adoptar el stack completo |

## Código examinado y decisiones

- En [`Feashliaa/scripts/scraper.py`](https://github.com/Feashliaa/job-board-aggregator/blob/main/scripts/scraper.py), cada ATS devuelve una estructura uniforme y su propia fuente/fecha de raspado. El adaptador Greenhouse lee `updated_at`; nuestro filtro ya usa `first_published` para evitar considerar como nuevo un aviso editado. No se tomó su geocodificación porque una ubicación `Remote` no demuestra que acepte Argentina.
- En [`resume-rag/job_matcher.py`](https://github.com/atharvguitarist/resume-rag/blob/main/job_matcher.py), los requisitos obligatorios y los motivos se calculan aparte del parecido semántico. `opportunity_rank.py` toma esa separación como criterio de diseño, con reglas explícitas y sin embeddings. No se atribuye mejora de precisión hasta tener avisos etiquetados.
- `wickfeed` describe una cola de cambios y cierres. Nuestro `seen_jobs.json` sólo marca descubrimientos; un estado de cierre y una cola de enriquecimiento para los 377 candidatos son la próxima mejora de mayor valor.

## Medición propia de hoy

Greenhouse 232 avisos leídos y Lever 204; 18 avisos con fecha dentro de tres días en el resultado diario (15 UADE, 3 Lever) y 377 señales para verificar. La búsqueda manual de LinkedIn Posts encontró Rendel, que el feed de Jobs no había aportado. No hay etiquetas suficientes para medir precisión, recall o falsos negativos de manera válida. Ninguna librería externa quedó instalada.
