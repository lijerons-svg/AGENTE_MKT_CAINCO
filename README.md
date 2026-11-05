# Sistema multi-agente para casos de marketing estratégico

Resuelve un caso de marketing (diagnóstico → estrategia → hoja de ruta → deck) con un
**orquestador + 8 agentes especializados** de Claude Code que comparten un *brief vivo* y
producen una presentación defendible con datos.

Probado con el caso **ACIERTA by CAINCO** (ver [`casos/cainco/`](./casos/cainco)) — incluido como
ejemplo resuelto de punta a punta.

---

## Concepto

```
input/ (consigna)
      │
      ▼
[orquestador: destila la consigna] ──► _brief/00-caso.md
      │
      ▼  diagnóstico (en paralelo)
   ┌──────────────┬───────────────────┬──────────────┐
   │ 01 Auditoría │ 02 Inteligencia   │ 03 Contexto  │   ← búsqueda web REAL
   │   digital    │    competitiva    │    macro     │
   └──────────────┴───────────────────┴──────────────┘
      │
      ▼  estrategia (secuencial)
   04 Arquitectura de marca → 05 Plan SMART → 06 Contenidos → 07 Quick wins + roadmap
      │
      ▼
   08 Crítico / panel exigente (red-team + Q&A)
      │
      ▼
[orquestador: resuelve contradicciones + ensambla] ──► _brief/storyline.md
      │
      ▼
   build.js  ──►  output/<deck>.pptx
```

**Regla de oro:** nada entra al deck si no es defendible con un dato o con lógica explícita.

Cada agente escribe **su propio archivo** en `_brief/` (no un único archivo compartido), de modo que
los agentes de diagnóstico (01, 02, 03) pueden correr en paralelo sin pisarse.

---

## Estructura del repo

```
.claude/agents/        Los 9 subagentes (el MÉTODO, reutilizable entre casos)
  mkt-orquestador.md
  mkt-01-auditoria-digital.md      (web)
  mkt-02-inteligencia-competitiva.md (web)
  mkt-03-contexto-macro.md         (web)
  mkt-04-arquitectura-marca.md
  mkt-05-plan-marketing.md
  mkt-06-contenidos.md
  mkt-07-quickwins-roadmap.md
  mkt-08-critico.md
  pres-01-optimizador-presentaciones.md   (diseño/contenido de slides + guion oral)

casos/<caso>/          Un caso concreto (los DATOS)
  input/               Consigna original (PDF, brief del cliente)
  _brief/              Cerebro compartido: 00-caso.md, 01..08, storyline.md
  build.js             Generador de deck en Node (pptxgenjs)
  build_pptx.py        Generador de deck en Python (python-pptx)
  output/              Entregable final (.pptx)

plantillas/            Guía y skeleton para arrancar un caso nuevo
```

---

## Cómo resolver un caso nuevo

1. **Crea la carpeta del caso** y mete la consigna:
   ```
   casos/<mi-caso>/input/<consigna>.pdf
   ```
   (Puedes copiar la estructura de `plantillas/`.)

2. **Pídele a Claude que lo resuelva.** En el chat, algo como:
   > "Resuelve el caso `casos/<mi-caso>`. Empieza por el orquestador para destilar la consigna,
   > luego corre los agentes de diagnóstico en paralelo, después estrategia, crítico y cierre."

   El hilo principal conduce el flujo invocando a los subagentes en orden:
   - `mkt-orquestador` (modo inicio) → escribe `_brief/00-caso.md`
   - `mkt-01`, `mkt-02`, `mkt-03` **en paralelo**
   - `mkt-04` → `mkt-05` → `mkt-06` → `mkt-07` (secuencial)
   - `mkt-08` (crítico)
   - `mkt-orquestador` (modo cierre) → escribe `_brief/storyline.md`

3. **Construye el deck.** Adapta `build.js` al `storyline.md` del caso (puedes partir del de
   `casos/cainco/build.js` como referencia de sistema de diseño) y ejecútalo:
   ```bash
   npm install pptxgenjs react-icons react react-dom sharp
   node casos/<mi-caso>/build.js
   ```
   El deck queda en `casos/<mi-caso>/output/`.

> **Nota sobre orquestación:** los subagentes de Claude Code no se invocan entre sí; es el hilo
> principal el que actúa de director siguiendo el orden de arriba. El agente `mkt-orquestador`
> se encarga de destilar (inicio) y de sintetizar el storyline (cierre).

---

## Agente de presentación (`pres-01-optimizador-presentaciones`)

Agente complementario que NO investiga: **optimiza el contenido y el diseño** del deck. Trabaja sobre
el `storyline.md` y los briefs, en cuatro modos:

1. **Revisar** un deck existente (títulos con verbo, densidad ≤3 bloques/slide, evidencia, jerarquía).
2. **Reescribir** slides con un formato fijo (título-afirmación, bloques, nota de exposición, nota de diseño).
3. **Diseñar plantillas** de infografía (timeline, matriz 2×2, funnel, FODA, buyer persona, KPIs…).
4. **Guion de exposición oral** slide a slide, con énfasis y Q&A del panel.

Encaja entre el `storyline.md` (orquestador) y la generación del deck: pule el contenido antes de renderizar.

---

## Generación del deck: dos vías

El deck `.pptx` se puede construir de dos formas, ambas presentes en `casos/cainco/`:

| Vía | Stack | Fortaleza | Cuándo usarla |
|---|---|---|---|
| `build.js` | Node + `pptxgenjs` + `react-icons`/`sharp` | Sistema de diseño pulido, íconos PNG reales, layouts ricos | Deck "de impacto" para presentar |
| `build_pptx.py` | Python + `python-pptx` | Formas y texto nativos 100% editables en PowerPoint, sin dependencias gráficas | Deck que el cliente seguirá editando a mano |

Ambas escriben en `casos/<caso>/output/`. Hoy las dos son **bespoke por caso**: el contenido va escrito
en el script sobre helpers reutilizables.

```bash
# Vía Node
npm install pptxgenjs react-icons react react-dom sharp
node casos/<mi-caso>/build.js

# Vía Python
pip install python-pptx
python casos/<mi-caso>/build_pptx.py
```

### Vía 3 (piloto): fuente única → HTML/PDF + PPTX

En [`casos/cainco/deck/`](./casos/cainco/deck) hay una prueba de concepto que separa el **contenido**
del **render**: un solo `deck.json` genera **ambos** formatos sin duplicar el contenido.

| Archivo | Hace |
|---|---|
| `deck.json` | Única fuente: contenido + tema (paleta del caso) |
| `render_html.py` | `deck.json` → `output/deck.html` (solo stdlib; PDF al imprimir desde el navegador) |
| `render_pptx.py` | `deck.json` → `output/deck.pptx` (editable, `python-pptx`) |

```bash
python casos/cainco/deck/render_html.py     # sin dependencias
pip install python-pptx
python casos/cainco/deck/render_pptx.py
```

Tipos de bloque compartidos por ambos renderers: `cover`, `two-columns`, `table`, `cards`,
`statement`, `objectives`, `timeline`, `numbered`. No toca `build.js` ni `build_pptx.py`.

*Siguiente paso si convence:* que `mkt-orquestador` emita el `deck.json` directamente desde
`storyline.md`, para no escribir el contenido a mano en cada caso.
