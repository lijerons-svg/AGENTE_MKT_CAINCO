"""Mini herramienta web local: subís los PDF de recibos de Meta Ads (y, a
futuro, Mailchimp) y descargás un Excel de gasto por actividad.

Corre en tu propia máquina, no en internet — nadie más ve tus recibos.
Uso:
    python -m marketing_analytics.reportes_pauta.app_web
    (abrí http://127.0.0.1:5050 en el navegador)
"""
from __future__ import annotations

import io
from pathlib import Path

from flask import Flask, request, send_file, Response

from marketing_analytics.config.loader import load_config
from marketing_analytics.reportes_pauta.excel_salida import construir_excel
from marketing_analytics.reportes_pauta.parser_meta import es_recibo_meta, parsear_recibo_meta
from marketing_analytics.reportes_pauta.pdf_texto import extraer_texto

app = Flask(__name__)

_CONFIG_PATH = Path("config.yaml")

_PAGINA = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Gasto por actividad — Meta Ads / Mailchimp</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 560px; margin: 60px auto; color: #1a1a1a; }
  h1 { font-size: 1.3rem; }
  .caja { border: 2px dashed #ccc; border-radius: 10px; padding: 32px; text-align: center; margin-top: 24px; }
  input[type=file] { margin: 16px 0; }
  button { background: #003a70; color: white; border: none; padding: 10px 20px; border-radius: 6px;
           font-size: 1rem; cursor: pointer; }
  button:hover { background: #0a5aa0; }
  .error { color: #b00020; margin-top: 16px; }
  .nota { color: #666; font-size: 0.85rem; margin-top: 24px; }
</style>
</head>
<body>
  <h1>Recibos de pauta → Excel de gasto por actividad</h1>
  <p>Subí uno o más recibos en PDF (Meta Ads). El Excel se genera al toque, con
  una fila por campaña: número de referencia del pago, unidad, actividad,
  monto invertido y resultado.</p>
  <form class="caja" action="/procesar" method="post" enctype="multipart/form-data">
    <input type="file" name="pdfs" accept="application/pdf" multiple required>
    <br>
    <button type="submit">Generar Excel</button>
  </form>
  {error}
  <p class="nota">Corre localmente en tu máquina — los PDF no se suben a ningún lado más que a este mismo programa.</p>
</body>
</html>
"""


def _alias_a_unidad() -> dict[str, tuple[str, bool]]:
    try:
        config = load_config(_CONFIG_PATH)
    except FileNotFoundError:
        return {}
    return {
        p.alias_pauta: (p.unidad, p.alias_pauta_generico) for p in config.meta.organico.perfiles
    }


def _pagina(error: str = "") -> str:
    return _PAGINA.replace("{error}", error)


@app.get("/")
def inicio() -> str:
    return _pagina()


@app.post("/procesar")
def procesar() -> Response:
    archivos = request.files.getlist("pdfs")
    if not archivos:
        return _pagina('<p class="error">Subí al menos un PDF.</p>')

    alias_a_unidad = _alias_a_unidad()
    filas: list[dict] = []
    sin_reconocer: list[str] = []

    for archivo in archivos:
        texto = extraer_texto(archivo.read())
        if es_recibo_meta(texto):
            filas.extend(parsear_recibo_meta(texto, alias_a_unidad))
        else:
            # Mailchimp (u otro formato) todavía no tiene parser — se
            # avisa en vez de inventar filas.
            sin_reconocer.append(archivo.filename or "archivo sin nombre")

    if not filas:
        detalle = f" ({', '.join(sin_reconocer)})" if sin_reconocer else ""
        return _pagina(
            f'<p class="error">No se pudo reconocer ningún recibo de Meta Ads{detalle}. '
            "El parser de Mailchimp todavía no está listo.</p>"
        )

    excel_bytes = construir_excel(filas)
    nombre_salida = "Gasto_por_actividad.xlsx"
    return send_file(
        io.BytesIO(excel_bytes),
        as_attachment=True,
        download_name=nombre_salida,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
