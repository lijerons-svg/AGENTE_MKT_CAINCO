# Deck desde una fuente única (piloto)

Prueba de concepto: **un solo archivo de contenido** (`deck.json`) que se renderiza a
**dos formatos** sin reescribir el contenido:

- `output/deck.html` — slides 16:9 en HTML (de ahí sale el PDF: imprimir desde el navegador).
- `output/deck.pptx` — PowerPoint 100% editable (formas y texto nativos, sin imágenes).

Es **independiente** de los generadores existentes (`../build.js`, `../build_pptx.py`): no los
toca. Aquí el contenido vive separado del render.

```
deck/
  deck.json        ← ÚNICA FUENTE: contenido + tema (paleta INK=1A2238, ORANGE=E8732A)
  render_html.py   ← deck.json → output/deck.html   (solo stdlib, sin dependencias)
  render_pptx.py   ← deck.json → output/deck.pptx   (requiere python-pptx)
  output/
```

## Uso

```bash
# HTML (no necesita instalar nada)
python render_html.py

# PPTX editable
pip install python-pptx
python render_pptx.py
```

### PDF
Abre `output/deck.html` en el navegador → **Ctrl+P** → *Guardar como PDF*.
El CSS `@media print` deja **un slide por página** en horizontal (1280×720).

## Cómo editar el deck
Tocas **solo `deck.json`** y vuelves a correr los dos renderers. El contenido nunca se duplica:
HTML y PPTX leen el mismo JSON.

## Tipos de bloque soportados
Cada slide del JSON declara un `type`. Ambos renderers entienden los mismos:

| `type` | Uso | Campos clave |
|---|---|---|
| `cover` | Portada | `kicker`, `title`, `subtitle`, `meta` |
| `two-columns` | Comparar 2 listas (p.ej. fortalezas/debilidades) | `left`/`right` con `label`, `tone` (`good`/`bad`), `items[]` |
| `table` | Matriz comparativa + caja destacada | `headers[]`, `rows[][]`, `callout{label,text}` |
| `cards` | Rejilla de tarjetas (insights, pilares, quick wins) | `columns` (2/3), `cards[]{label,body}`, `facts[]` |
| `statement` | Frase grande + transición "de → a" | `quote`, `shift{from,to}`, `extra` |
| `objectives` | Objetivos SMART con KPIs | `items[]{tag,name,goal,kpis[]}` |
| `timeline` | Hitos mes a mes | `steps[]{when,what}` |
| `numbered` | Lista numerada (criterios) | `items[]{n,head,body}` |

Todos aceptan `title`, `subtitle` y `note` (nota de exposición oral, va al pie del slide).

## Por qué este enfoque
- **Una sola verdad**: el contenido no se desincroniza entre el PPTX y el HTML/PDF.
- **PPTX editable**: el cliente sigue ajustando a mano en PowerPoint.
- **HTML/PDF sin dependencias**: el HTML se genera con la librería estándar de Python.
- **Reutilizable**: para otro caso, copias `deck/`, reescribes `deck.json` y corres los renderers.

> Piloto sobre el caso CAINCO. Si convence, el siguiente paso es que `mkt-orquestador`
> emita el `deck.json` directamente desde `storyline.md`.
