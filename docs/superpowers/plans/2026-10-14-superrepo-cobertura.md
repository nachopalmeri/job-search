# Integración del recorrido diario en job-search

## Objetivo

Dejar `nachopalmeri/job-search` como repositorio canónico de la búsqueda laboral, con cobertura auditable de todas las fuentes acordadas y una pasada diaria que no confunda fuentes automáticas, fuentes manuales, tareas de IA y eventos. Integrar en `master` luego de verificar.

## Decisiones y límites

- Las ramas remotas actuales ya son ancestros de `origin/master`; no se rehacen merges vacíos.
- No copiar el código de JobBot: es otra aplicación. Portar solo la taxonomía, fuentes y reglas de cobertura que falten.
- Ningún resultado se considera vacante apta sin anuncio original, fecha y elegibilidad desde Argentina verificadas.
- Las sesiones autenticadas y Notion se usan solo con los accesos disponibles; un bloqueo queda explícito.
- No enviar postulaciones ni mensajes externos. El usuario autorizó el merge y push al repositorio correcto.

## Orden de trabajo

1. Auditar ramas, fuentes y pruebas actuales; identificar ausencias y errores reproducibles.
2. Crear un catálogo de fuentes único y una verificación de cobertura por fuente, con pruebas pequeñas de casos reales.
3. Actualizar el flujo y la documentación de `job-search`, incluidas rutas ejecutables en este checkout y cierre en Notion.
4. Ejecutar tests, validación estática y una pasada de humo de los comandos principales; documentar límites de red o sesión.
5. Revisar diff/secretos, commitear, mergear en `master`, verificar otra vez y pushear. Confirmar que no queden ramas sin integrar.

## Criterios de aceptación

- Todas las fuentes acordadas tienen ID, URL, carril y modo de acceso, o una explicación explícita de exclusión.
- La cobertura del día distingue consultada con/sin resultados, bloqueada y pendiente; ninguna pendiente se declara completa.
- El flujo diario usa este repositorio y registra el cierre en Notion; evita credenciales y acciones de postulación.
- `python -m pytest -q`, `python -m compileall -q scripts` y los comandos de humo terminan sin errores atribuibles al código.
- `git branch -r --no-merged origin/master` está vacío tras el push; `master` remoto apunta al commit integrado.

## Condiciones de pausa

- No mergear si la suite está roja por un defecto sin resolver o si un cambio de rama pisa trabajo ajeno.
- No inventar resultados ni declarar completa una fuente cuyo acceso no se pudo comprobar.
