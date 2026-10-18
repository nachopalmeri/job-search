# Búsqueda laboral V2: evidencia, oportunidades y presencia profesional

## Qué agrega

- **Fuentes con frecuencia:** `scripts/source_inventory.py` construye un inventario de las 38 fuentes configuradas (la base previa tenía 37; ahora se suma Silver.dev) y cruza el último intento/éxito registrado. `source_coverage.py --init` lo actualiza. El campo `eligible_count` queda vacío mientras el pipeline no mida elegibilidad por fuente.
- **Dos colas laborales:** los avisos con fecha original verificada dentro de 4 días siguen en `recommendations-<fecha>.json`; señales prometedoras con fecha o requisitos pendientes van a `potential-review-<fecha>.json`. Ninguna fecha ausente se considera reciente ni se usa por sí sola para descartar.
- **CafeDev:** las búsquedas usan texto amplio y recorren páginas hasta un límite local de 50 solicitudes, pausando 1,05 s entre consultas. El listado devuelve resúmenes cortos; `cafedev_audit.py --enrich-live --detail-limit 30 --low-sample 10` consulta el endpoint de detalle para los 30 candidatos prioritarios, 10 de baja afinidad y las fichas históricas con resumen largo. El detalle amplía descripción/requisitos, pero no garantiza fecha original, vigencia ni URL del empleador. `first_seen_at` es indexación; `apply_url` se conserva como enlace de CafeDev y nunca se etiqueta como ATS directo sin verificarlo. El detalle queda guardado en `radar/cafedev-detail-enrichment-AAAA-MM-DD.json`.
- **Inteligencia de startups:** `strategic_intelligence.py` separa anuncios de financiación/expansión/producto de vacantes concretas. Cada señal lleva evidencia; una señal de crecimiento permanece como hipótesis de oportunidad laboral hasta encontrar una vacante o una declaración directa de contratación.
- **Networking y contenido:** contactos profesionales públicos y propuestas de contenido tienen carriles independientes. No se recopilan correos privados; mensajes y publicaciones quedan sin enviar/publicar hasta aprobación humana.

## Frecuencia de fuentes

`source-inventory.md` es la lista completa y operativa. Dos canales sociales de alta velocidad (LinkedIn Posts y X Latest) se pueden revisar varias veces al día con consultas breves y respetando bloqueos. Portales de empleo, UADE, ATS y Silver.dev se revisan a diario. Eventos, gig marketplaces, comunidades y portales de baja sensibilidad temporal se revisan semanalmente; quedan `not_due` en los demás días. `not_due` nunca se muestra como búsqueda completada o cero resultados.

## Flujo diario

1. `python scripts\source_coverage.py --init`
2. `python scripts\buscar_portales.py --scrape all --write`
3. `python scripts\opportunity_pipeline.py`
4. `python scripts\cafedev_audit.py --enrich-live --detail-limit 30 --low-sample 10`
5. Revisión manual de publicaciones originales y fuentes autenticadas según el checklist, marcando cada fuente con evidencia de cobertura.
6. Para señales de empresa, contactos o temas de contenido, importar JSON revisado con `scripts/strategic_intelligence.py`.
7. Preparar el reporte corto, actualizar el archivo de Notion y comprobar escrituras con lectura posterior.

## Estado de CafeDev 18/10/2026

El listado en vivo obtuvo 711 señales en 32 requests, conservadas en `radar/cafedev-live-v2-2026-10-18.tsv`. La auditoría acotada consultó 47 fichas: 30 candidatas principales, 10 de baja afinidad y las 7 fichas cuyo resumen superaba 500 caracteres. En las 47, el endpoint de detalle devolvió descripciones completas, pero `published_at` fue nulo; `first_seen_at` fue fecha de indexación. El detalle no expone estado abierto/cerrado ni una URL fuente distinta del proxy de CafeDev. El enlace original del ATS se pudo encontrar por separado para TrueML; el resto requiere verificación individual en páginas de empresa. No convertir ausencia de fecha en rechazo ni en aviso fresco.

La referencia pública consultada describe `GET /v1/jobs/:id` como endpoint de detalle ([referencia de la API](https://mcpservers.org/servers/cafedev-co-developers)); además se verificó directamente una respuesta completa. El listado debe tratarse como resumen. La API de detalle no presenta `published_at` ni URL de la fuente original en todas las fichas; por eso se guardan como desconocidos y se busca el aviso oficial antes de clasificarlo como fresco o listo para postular. El fetcher está limitado a 30 candidatas, 10 de muestra y los resúmenes históricos largos, con pausas entre solicitudes.

Silver.dev se verificó en su [tablero público](https://silver.dev/jobs): el sitio mostraba 44 posiciones, con filtros de rol/tecnología/remoto, pero la mayor parte de los títulos visibles eran senior o requerían experiencia; no se dio por elegible ningún aviso sin leer su ficha. Speedrun está en el catálogo y sus filtros exponen categorías de Internship/New Grad y Remote; el tablero es amplio y muchas posiciones requieren ubicación específica. Ambas fuentes se usan para descubrimiento, no como prueba de elegibilidad en Argentina.

## Límites de la automatización

- Los filtros de título y overlap de skills son solo orden de inspección, no decisiones de contratación.
- “Remoto” no prueba elegibilidad laboral desde Argentina.
- Un post de recruiter sin enlace y vacante verificable permanece como contacto/señal.
- Las 38 fuentes pueden estar configuradas sin haber sido consultadas; reporte e inventario lo muestran por separado.
- Notion conserva la base existente de oportunidades. Contactos y calendario editorial no se duplican allí hasta que exista una base adecuada; se pueden dejar en los registros estructurados del repo como borradores.
