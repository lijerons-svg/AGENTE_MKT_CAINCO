# Caso ACIERTA by CAINCO — ejemplo resuelto

Caso técnico para **Subgerente de Marketing Estratégico** de CAINCO. Plan de marketing a 6 meses
para la unidad de servicios empresariales **ACIERTA**, resuelto con el sistema multi-agente
(ver [README raíz](../../README.md)).

## Contenido
- [`input/`](./input) — consigna original (PDF de ETIKA).
- [`_brief/`](./_brief) — cerebro compartido: `00-caso.md` (consigna destilada), `01`…`08`
  (salida de cada agente) y `storyline.md` (guion de las 10 slides).
- [`build.js`](./build.js) — genera el deck con `pptxgenjs`.
- [`output/`](./output) — `Plan_Marketing_Acierta_CAINCO.pptx` (10 slides).

## Regenerar el deck
```bash
npm install pptxgenjs react-icons react react-dom sharp
node build.js   # escribe en ./output/
```

## Nota
Las cifras de baseline (ej. "0 métricas", "25% de leads no-core") son supuestos de partida del caso.
Reemplazar por datos reales de Acierta al disponer de ellos.

*Confidencial — preparado para proceso de selección ETIKA SRL.*
