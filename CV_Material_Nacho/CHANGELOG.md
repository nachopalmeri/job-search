# Changelog v2 — CV Maestro (ronda 2, ago 2026)

Regla rectora: **honestidad verificable**. En esta ronda se verificó cada claim contra fuentes reales (GitHub API, Vercel, web) antes de dejarlo en el CV.

## Hallazgos verificados online (ronda 2)

| Claim en CVs viejos | Veredicto | Fuente |
|---|---|---|
| JobBot = "bot personal sin pagos" | **Corregir**: el repo (81 commits) muestra dashboard + billing Stripe/MercadoPago en sandbox. Candidato confundió "no es SaaS terminado" con "no tiene capa de pagos". El CV nuevo lo describe como bot + dashboard con billing en prueba | github.com/nachopalmeri/jobbot |
| FranquiYA = prototipo | ✅ Confirmado (57 commits, auto-declara "prototype") | github.com/nachopalmeri/FranquiYA |
| Prode Estadístico (Poisson/MonteCarlo/Polymarket) | ✅ Real, es prode del Mundial 2026, no trading. Nombre honesto: "Motor estadístico de predicción deportiva" | github.com/nachopalmeri/prode-mundial-2026 |
| PISKU publicado en PyPI | ❌ **Refutado** (pypi.org/pypi/pisku = 404). Solo repo menor en GitHub. Se eliminó el claim. | pypi.org |
| DApp Solidity en Base Sepolia | ❌ **No atribuible** (ninguno de 28 repos la tiene; el proyecto que matchea es de otra persona). Eliminada. | GitHub scanner |
| Portfolio ignaciopalmeri.vercel.app | ✅ Activo y actualizado, con CV descargable y proyectos | vercel.app |
| LinkedIn principal | ✅ /in/ignaciopalmeri (94 followers, Grido, UADE, certs). ⚠️ El portfolio enlaza al perfil SECUNDARIO /in/ignacio-palmeri-64035b378 (~5 conns). **Unificar links hacia el principal.** | web |
| RachaApp, pisku-, pisku-labs, libroabierto | Repos "cascarón" o casi vacíos → no van al CV | GitHub |
| Bio GitHub vacía | El perfil no tiene bio (solo README). Recomendación: agregar bio técnica | GitHub |

## Cambios aplicados en el CV maestro (ES + EN)

1. **Header:** agregado portfolio `ignaciopalmeri.vercel.app`.
2. **Proyectos:** JobBot re-descripto (bot + dashboard + billing sandbox), con repo linkeado. FranquiYA con repo+demo linkeado. Agregado Prode Mundial 2026 con repo+demo (honesto: prode, no trading). PISKU sin PyPI. Agents System con repo.
3. **Nueva sección PORTFOLIO** con links verificados.
4. **Skills:** agregado Groq, Gemini; metodologías ágiles.
5. **Inglés:** aclarado que B1+/B2 es autoevaluado, sin certificación; sugerencia EF SET gratis.
6. **Eliminados:** DApp Solidity, claim PyPI, "deployado en producción" para JobBot.

## Pendientes de acción para el usuario (fuera de los archivos)

- [ ] Actualizar el portfolio `ignaciopalmeri.vercel.app`: cambiar link de LinkedIn del secundario (`/in/ignacio-palmeri-64035b378`) al principal (`/in/ignaciopalmeri`).
- [ ] Decidir con `portafolioignaciopalmeri.vercel.app` (viejo, posiciona "Web3 Architect/Backend"): redirigir al nuevo o eliminar.
- [ ] Agregar bio técnica al perfil de GitHub (hoy vacía, solo README).
- [ ] Sanear/hacer privados repos "cascarón" (RachaApp, pisku-, a, Cm, dom, porta) para no restarle peso al portfolio.
- [ ] Licencia del repo jobbot dice "Private - All rights reserved" pero es público: aclarar o hacer privado.