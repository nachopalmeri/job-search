# Wetcom — Jóvenes Talentos IT 17ª — Fit 4.2 — Prep v1 2026-08-21

> Fuente: reportes candidatos Wetcom (Glassdoor bloquea anónimo 2026-08-21, verificado 403; curaduría manual `site:glassdoor.com.ar Wetcom Entrevista` pendiente login) + validado contra `CV_Material_Nacho/extras/preguntas_tecnicas_wetcom.md:1-60` y `cheat_sheet_llamada_wetcom.md`. No se fabrican Q fuera de reporte. Actualizar con URL Glassdoor cuando se copie logueado.

## Q1 — Bit vs byte

**Fuente:** reporte candidato Wetcom 2023 (Glassdoor, anonimizado) — validado `preguntas_tecnicas_wetcom.md:4`
**Versión:** v1 2026-08-21
**Respuesta (ES, 30s):** Bit=0/1 unidad mínima; byte=8 bits (1 char). Velocidad en bits/s (Mbps), almacenamiento en bytes (GB). En Meet importa subida.
**Gap:** —

## Q2 — Ancho de banda

**Fuente:** idem Q1, `preguntas_tecnicas_wetcom.md:10`
**Versión:** v1
**Respuesta:** capacidad máxima de transferencia (autopista), Mbps. No es latencia.
**Gap:** —

## Q3 — Carga vs descarga

**Fuente:** idem, `preguntas_tecnicas_wetcom.md:15`
**Versión:** v1
**Respuesta:** descarga=recibo (video), carga=envío (subir archivo, Meet). En Wetcom híbrido 8:30-14:30 la carga afecta soporte remoto.
**Gap:** —

## Q4 — Virtualización / VMware

**Fuente:** idem, `preguntas_tecnicas_wetcom.md:23` — core negocio Wetcom (VMware/Veeam/Nutanix)
**Versión:** v1
**Respuesta (STAR si piden experiencia):** S: en UADE vi virtualización en laboratorio. T: entender hypervisor. A: practiqué en WSL2/Linux + doc VMware. R: sé que hypervisor aísla VMs, snapshot y DR — en Wetcom aplicaría a clientes con VMware ESXi.
**Gap honesto:** no tengo VMware producción; solo lab + RH124 `profile.md:36` (no certificado).

## Q5 — 2.4 vs 5GHz

**Fuente:** idem, `preguntas_tecnicas_wetcom.md:30`
**Versión:** v1
**Respuesta:** 2.4 alcance+penetra, lenta con interferencia; 5 rápida, menos alcance. Elegir según distancia; hoy 6GHz WiFi 6E.
**Gap:** —

## Q6 — Comandos Windows

**Fuente:** idem, `preguntas_tecnicas_wetcom.md:35`
**Versión:** v1
**Respuesta:** `ipconfig` IP, `ping` ICMP, `netstat` puertos, `tracert` ruta, `sfc /scannow` archivos sistema, `gpupdate /force` políticas. Sumar `Linux: ip a, ping, ss -tulpn` (`profile.md:36`).
**Gap:** no tengo help-desk producción; solo soporte Grido + lab.

## Q7 — DNS

**Fuente:** extensión lógica reporte + `preguntas_tecnicas_wetcom.md:45`
**Versión:** v1
**Respuesta:** resuelve nombre→IP (directorio telefónico). Si ping a IP ok pero web no abre → falla DNS.
**Gap:** —

## Q8 — DHCP

**Fuente:** idem `preguntas_tecnicas_wetcom.md:48`
**Versión:** v1
**Respuesta:** asigna IP/gateway/DNS automático (lease). Sin DHCP, config manual.
**Gap:** —

## Q9 — Puertos comunes

**Fuente:** idem `preguntas_tecnicas_wetcom.md:50`
**Versión:** v1
**Respuesta:** 21 FTP, 22 SSH, 80 HTTP, 443 HTTPS, 3389 RDP. Bloquear 21 = denegar FTP.
**Gap:** —

## Q10 — Tipos de backup

**Fuente:** idem `preguntas_tecnicas_wetcom.md:55`
**Versión:** v1
**Respuesta:** Full todo; incremental solo desde último backup (restaura encadenado lento); differential desde último full (full+último diff). Wetcom usa Veeam.
**Gap:** —

## Q11 — Dominio vs grupo trabajo + inglés

**Fuente:** `cheat_sheet_llamada_wetcom.md` (llamada 10 min Fátima 05/08) + reporte inglés excluyente `tracker: Wetcom 4.2 gap inglés sin certificar`
**Versión:** v1
**Respuesta EN pitch (60s):** "I'm Ignacio, second-year IT Management at UADE, 8.2 GPA. I build Python/LLM tools (Telegram bot, Monte Carlo engine) and work part-time retail. I study CCNA 1 and use Linux daily. My English is B1+/B2, fluent reading, intermediate speaking — I'm preparing EF SET certification, I don't claim bilingual." (honesto `profile.md:30`).
**Gap:** inglés sin certificar (excluyente) → rendir EF SET antes de afirmar.

---
**Curaduría próxima:** login Glassdoor → buscar "Wetcom Entrevista" → copiar 2-3 Q adicionales con URL fuente y pegar como Q12+ v2. No inventar.

