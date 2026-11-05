# Guía — arrancar un caso nuevo

1. Crea la carpeta del caso copiando esta estructura:
   ```
   casos/<mi-caso>/
     input/        ← mete aquí la consigna (PDF / brief del cliente)
     _brief/       ← se llena solo al correr los agentes
     output/       ← deck final
   ```
   En PowerShell:
   ```powershell
   $c = "casos\mi-caso"
   New-Item -ItemType Directory -Force "$c\input","$c\_brief","$c\output" | Out-Null
   # copia tu consigna a $c\input\
   ```

2. Pídele a Claude:
   > "Resuelve el caso `casos/mi-caso` con el sistema multi-agente."

   Orden que sigue el hilo principal:
   - `mkt-orquestador` (inicio) → `_brief/00-caso.md`
   - `mkt-01`, `mkt-02`, `mkt-03` en paralelo (diagnóstico, con búsqueda web)
   - `mkt-04` → `mkt-05` → `mkt-06` → `mkt-07` (estrategia, secuencial)
   - `mkt-08` (crítico / panel)
   - `mkt-orquestador` (cierre) → `_brief/storyline.md`

3. Construye el deck: adapta un `build.js` (referencia: `casos/cainco/build.js`) al `storyline.md`
   y ejecuta `node casos/mi-caso/build.js`.

## Convención de archivos en `_brief/`
| Archivo | Lo escribe | Contenido |
|---|---|---|
| `00-caso.md` | orquestador (inicio) | consigna destilada + reglas del juego |
| `01-auditoria-digital.md` | agente 1 | 3 fortalezas / 3 debilidades digitales (evidencia real) |
| `02-competencia.md` | agente 2 | matriz competitiva + "el hueco" |
| `03-contexto-macro.md` | agente 3 | hechos macro + 4 insights accionables |
| `04-arquitectura-marca.md` | agente 4 | modelo de marca + propuesta de valor |
| `05-plan-marketing.md` | agente 5 | objetivos SMART + KPIs |
| `06-contenidos.md` | agente 6 | pilares + frecuencia + segmentación |
| `07-quickwins-roadmap.md` | agente 7 | 3 quick wins + cronograma + criterios de éxito |
| `08-critico.md` | agente 8 | riesgos + Q&A del panel + correcciones |
| `storyline.md` | orquestador (cierre) | guion del deck + cobertura de consignas |

Cada agente escribe **solo su archivo**. Así los de diagnóstico (01-03) corren en paralelo sin pisarse.
