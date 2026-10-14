# Búsqueda laboral — estado 14/10/2026

## Hecho en esta pasada
- UADE autenticado en Brave: filtro `--Búsquedas sin carrera específica--`; revisadas las cinco pasantías y cinco búsquedas laborales visibles, todas fechadas 14/10. La ficha 2026-2249 y los detalles completos de los diez avisos quedaron en Notion.
- Verificada en la página original de Bumeran la vacante Tandem Technology — Back Office: publicada 14/10, presencial, part-time 08:00–14:00; exige seis meses de procesamiento de datos e inglés Excel excluyente. CAPSA UADE/Bumeran conservado como una sola oportunidad.
- Corregido ranking para no usar texto del aviso como prueba de competencias del perfil y para exigir palabra completa al detectar AI/IA.
- Ranking recalculado: UADE Microinformática 2026-2249 3.3/5 (condicional); Tandem 3.5/5 (experiencia/Excel pendientes); CAPSA/CAPEX 2.4/5 (carrera/horario pendientes). Ninguna lista para postular.
- Notion actualizado: tres filas existentes; resumen y archivo muestran los nuevos scores y diez anuncios, sin postulaciones.
- Cobertura: 36 fuentes declaradas, 690 resultados/señales; 13 fuentes bloqueadas y 659 candidatos aún pendientes de enriquecimiento en el pipeline. No afirmar búsqueda exhaustiva.

## Revisión independiente y correcciones finales (14/10)
- Corregido: `status: verified` por sí solo ya no valida fecha original; los años deseables/ambiguos quedan para confirmar y un mínimo explícito o `N+ years` sí puede vetar; se añadieron límites de palabra en la detección de IT/IA.
- Corregido: comparación con Calendar conserva minutos exactos; URL canónica exacta une observaciones de fuentes distintas aunque coincidan los IDs numéricos, pero no fusiona dos requisiciones diferentes de la misma fuente; ranking conserva la descripción más completa y las observaciones fuente.
- Suite aislada de ranking/pipeline/deduplicación: 27 pruebas OK. `py_compile` y `git diff --check` OK.
- `unittest discover` ejecuta esas 27 pruebas, pero no puede importar `test_source_coverage`: falta `pytest` en el entorno; no se instaló.
- `source_coverage --check`: 36 fuentes, 690 señales, 13 bloqueadas; resultado parcial, no búsqueda integral. UADE autenticado cubrió el filtro sin carrera específica y los diez anuncios visibles del 14/10.

## Verificación
- `python -m unittest tests.test_opportunity_pipeline_unittest -v`: 27 pruebas OK.
- `python -m unittest discover -s tests -v`: 27 pruebas pasan y falla la importación de `test_source_coverage` porque el entorno no tiene `pytest`; no se instaló ninguna dependencia.
- `python -m py_compile scripts/opportunity_rank.py scripts/opportunity_pipeline.py scripts/opportunity_identity.py scripts/calendar_fit.py`: OK.
- `git diff --check`: OK.
- El reranking de 659 oportunidades no dejó ninguna de las 7 con publicación original verificada en los últimos tres días como elegible; las siete tienen brechas excluyentes o datos esenciales pendientes.
- `source_coverage --check`: pendientes 0, pero termina con código 1 porque 13 fuentes siguen bloqueadas (LinkedIn, LinkedIn Posts, X, Torre, Indeed, Jooble, Zonajobs, FirstJob, Wellfound, startups y otros portales). La fecha del sitio UADE visible no cubre todas las búsquedas por carrera.
- Notion `query_data_sources` alcanzó el límite de uso del espacio; el query no se ejecutó. Se actualizaron y releyeron páginas por ID conocido; no se intentó repetir el query.

## Pendiente
1. Confirmar en UADE 2026-2249 empresa, carrera/año, jornada, remuneración y vigencia antes de mover a Para postular.
2. Verificar con el perfil/evidencia si proyectos propios cubren los seis meses y el nivel de Excel de Tandem.
3. Preguntar a UADE si aceptan Gestión de TI en el track Comercial de CAPSA y confirmar jornada diaria/traslado.
4. Enriquecer señales del pipeline; no marcarlas aptas por fecha de captura.
5. Reanudar query de Notion cuando se restablezca la cuota, para verificar duplicados y estados de todo el datasource.
6. Mantener LinkedIn Jobs, LinkedIn Posts, X, portales startup, Wellfound, FirstJob y fuentes bloqueadas como pendientes; buscar desde navegador donde sea posible.
