# Búsqueda laboral V2: evidencia, oportunidades y presencia profesional

## Qué agrega

- **Fuentes con frecuencia:** `scripts/source_inventory.py` construye un inventario de las 38 fuentes configuradas (la base previa tenía 37; ahora se suma Silver.dev) y cruza el último intento/éxito registrado. `source_coverage.py --init` lo actualiza. El campo `eligible_count` queda vacío mientras el pipeline no mida elegibilidad por fuente.
- **Dos colas laborales:** los avisos con fecha original verificada dentro de 4 días siguen en `recommendations-<fecha>.json`; señales prometedoras con fecha o requisitos pendientes van a `potential-review-<fecha>.json`. Ninguna fecha ausente se considera reciente ni se usa por sí sola para descartar.
- **CafeDev:** las búsquedas usan texto amplio y recorren páginas hasta un límite local de 50 solicitudes, pausando 1,05 s entre consultas. `cafedev_audit.py` revisa el snapshot disponible y marca como desconocidos los requisitos que no aparecen. Solo la lectura de la publicación/ATS oficial confirma antigüedad, vigencia, experiencia o elegibilidad.
- **Inteligencia de startups:** `strategic_intelligence.py` separa anuncios de financiación/expansión/producto de vacantes concretas. Cada señal lleva evidencia; una señal de crecimiento permanece como hipótesis de oportunidad laboral hasta encontrar una vacante o una declaración directa de contratación.
- **Networking y contenido:** contactos profesionales públicos y propuestas de contenido tienen carriles independientes. No se recopilan correos privados; mensajes y publicaciones quedan sin enviar/publicar hasta aprobación humana.

## Frecuencia de fuentes

`source-inventory.md` es la lista completa y operativa. Dos canales sociales de alta velocidad (LinkedIn Posts y X Latest) se pueden revisar varias veces al día con consultas breves y respetando bloqueos. Portales de empleo, UADE, ATS y Silver.dev se revisan a diario. Eventos, gig marketplaces, comunidades y portales de baja sensibilidad temporal se revisan semanalmente; quedan `not_due` en los demás días. `not_due` nunca se muestra como búsqueda completada o cero resultados.

## Flujo diario

1. `python scripts\source_coverage.py --init`
2. `python scripts\buscar_portales.py --scrape all --write`
3. `python scripts\opportunity_pipeline.py`
4. `python scripts\cafedev_audit.py`
5. Revisión manual de publicaciones originales y fuentes autenticadas según el checklist, marcando cada fuente con evidencia de cobertura.
6. Para señales de empresa, contactos o temas de contenido, importar JSON revisado con `scripts/strategic_intelligence.py`.
7. Preparar el reporte corto, actualizar el archivo de Notion y comprobar escrituras con lectura posterior.

## Estado de CafeDev 18/10/2026

El snapshot histórico local auditó 161 registros; la consulta del conector en vivo obtuvo 711 señales en 32 requests, conservadas en `radar/cafedev-live-v2-2026-10-18.tsv`. El informe correspondiente está en `radar/cafedev-live-audit-v2-2026-10-18.md`. Ninguna señaló fecha original en los campos recibidos y 704 no tenían descripción suficiente para determinar requisitos de experiencia. El sitio oficial de empleos/documentación y el endpoint consultado directamente desde el lector devolvieron error; el conector del proyecto, con sus headers y consultas limitadas, sí obtuvo la lista. La extracción solo confirma señales listadas por CafeDev: no confirma que sigan abiertas ni que se acepte postular desde Argentina. Se conservan como candidatas a investigar, nunca como vacantes frescas.

La búsqueda web encontró una referencia secundaria que describe `GET /v1/jobs`, `q`, `page`, `limit` (máximo 100), `GET /v1/jobs/:id` y `/v1/companies`, además de un límite de 120 solicitudes/minuto ([referencia secundaria](https://mcpservers.org/servers/cafedev-co-developers)); **ese límite y el contrato no se presentan como confirmados oficialmente**. El conector conservador usa `/v1/jobs` con consultas y páginas, tope local de 50 solicitudes y 1,05 s de intervalo. Se probó y se obtuvo el listado, pero no se implementó un fetcher de detalle porque el esquema oficial no pudo contrastarse.

Silver.dev se verificó en su [tablero público](https://silver.dev/jobs): el sitio mostraba 44 posiciones, con filtros de rol/tecnología/remoto, pero la mayor parte de los títulos visibles eran senior o requerían experiencia; no se dio por elegible ningún aviso sin leer su ficha. Speedrun está en el catálogo y sus filtros exponen categorías de Internship/New Grad y Remote; el tablero es amplio y muchas posiciones requieren ubicación específica. Ambas fuentes se usan para descubrimiento, no como prueba de elegibilidad en Argentina.

## Límites de la automatización

- Los filtros de título y overlap de skills son solo orden de inspección, no decisiones de contratación.
- “Remoto” no prueba elegibilidad laboral desde Argentina.
- Un post de recruiter sin enlace y vacante verificable permanece como contacto/señal.
- Las 38 fuentes pueden estar configuradas sin haber sido consultadas; reporte e inventario lo muestran por separado.
- Notion conserva la base existente de oportunidades. Contactos y calendario editorial no se duplican allí hasta que exista una base adecuada; se pueden dejar en los registros estructurados del repo como borradores.
