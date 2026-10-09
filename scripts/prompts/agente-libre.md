# Búsqueda laboral complementaria

Usá este prompt después del scraper. No repitas las fuentes automáticas sin motivo.

## Objetivo

Encontrar oportunidades reales para estudiante de segundo año de Gestión de TI en UADE, con experiencia de atención/caja y proyectos propios en automatización, Python, APIs y datos. Preferencias y capacidades exactas: `profile.md`; reglas de ajuste: `rubric-fit.md`. Inglés B1, autoevaluado y sin certificar. No inventes competencias.

**Vigencia estricta:** solo avisos cuya publicación original tenga como máximo 3 días de antigüedad al `{fecha}`. No uses la fecha del buscador, del repost ni del scrapeo como publicación. Si la fecha no se puede confirmar, sepáralo como **fecha no verificada** y no lo cuentes como activo ni le asignes fit.

## Antes de buscar

1. Lee `radar/daily-{fecha}.tsv`, `tracker/postulaciones.csv` y el reporte más reciente.
2. No vuelvas a proponer lo que esté en `PARA_POSTULAR`, `REGISTRADA` o `DESCARTADA`; si corresponde, di “ya está en el tracker”.
3. El scraper cubre LinkedIn guest, Cosign, Startups Argentina, YC, Speedrun, Get on Board, Torre, Computrabajo, BecasIT, EmpleosIT y los boards ATS oficiales listados en `scripts/ats_boards.json`. Investiga manualmente solo resultados que no pueda validar y fuentes adicionales; no repitas catálogos completos.

## Búsqueda manual

- **LinkedIn:** consultas separadas por familia, no un booleano largo: `pasantía IT Argentina`, `pasante sistemas`, `trainee tecnología`, `analista de datos junior`, `soporte IT junior`, `internship Argentina`, `business/product operations intern`. Usa filtro “últimas 24 horas” o “última semana” para descubrir; después confirma la fecha original. Si LinkedIn limita, para y registra el error; no repitas consultas equivalentes.
- **UADE Jobs:** revisar “sin carrera específica” y las carreras relacionadas (Gestión de TI, Informática, Ciencia de Datos/IA y Desarrollo de Software). Solo lectura; registrar número, fecha, requisitos, modalidad, jornada y enlace.
- **X:** abrir cada búsqueda corta por separado en “Latest”: `pasantía IT Argentina`, `pasante sistemas Argentina`, `trainee tecnología Argentina`, `pasantía datos Argentina`, `buscamos pasante soporte` y `#EmpleoIT pasante`. Agrega `since:{fecha-3-dias}` y `until:{fecha+1}`. Solo cuenta un post que enlace a una búsqueda concreta o a una postulación oficial; conversaciones, chistes, cursos y reposts sin origen no son oportunidades.
- **Empresas y startups:** complementa los boards Greenhouse/Lever del radar con páginas oficiales nuevas. Usa `first_published` (Greenhouse) o `createdAt` (Lever) como fecha original; confirma país y vigencia en el aviso. No releas el catálogo completo de una fuente ya procesada.
- **Si una fuente falla:** intenta una vez con el navegador del usuario si está disponible. Si vuelve a fallar o pide autenticación vencida, reporta cobertura parcial y sigue con las demás. Nunca automatices login, envío ni postulación.

## Evaluación y honestidad

Para cada aviso candidato guarda evidencia de: título y empresa; fecha original y URL; país elegible; requisitos de experiencia/estudio/idioma; tareas y stack; ubicación, modalidad y horario; sueldo si figura. Puntúa con `rubric-fit.md`, explica el gap principal y descarta avisos vencidos, cerrados, engañosos, de ubicación imposible o con requisitos excluyentes incumplidos. Full-time se evalúa y se marca contra la cursada; no es veto automático.

No abras adjuntos ni ejecutes pruebas. Descarta pedidos de pago, datos bancarios antes de entrevista, software de acceso remoto o contacto exclusivamente por mensajería. No postules, aceptes términos ni envíes mensajes.

## Salida breve

Escribe `radar/discoveries-{fecha}.md` con:

1. **Matches nuevos**, por fit: máximo 10, con fecha, enlace, modalidad/jornada, requisitos clave y gap.
2. **Descartes concretos** y motivo en una línea.
3. **Cobertura por fuente:** revisada con resultados, revisada sin resultados, parcial/error o fecha no verificable. No afirmes “búsqueda completa” si una fuente relevante falló.
4. **Próxima acción #1**.

Mantén el resumen de Notion corto y accionable; el reporte local guarda detalle y evidencia. La búsqueda de contactos/outbound es otra tarea y solo se ejecuta cuando Nacho la pide.
