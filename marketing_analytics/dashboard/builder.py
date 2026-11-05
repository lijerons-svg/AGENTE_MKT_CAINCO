"""Genera Dashboard.html: lee la base histórica, arma el JSON de datos y lo
inyecta en la plantilla estática (HTML5 + CSS + Plotly vía CDN, sin
Bootstrap). El HTML/CSS/JS fuente vive partido en varios archivos por
tamaño y legibilidad; el resultado es un único Dashboard.html portable.
"""
from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path

from marketing_analytics.dashboard.data_builder import construir_datos_dashboard

_MARCADOR_DATOS = "__DATOS_DASHBOARD_JSON__"
_MARCADOR_CSS = "__CSS_DASHBOARD__"
_MARCADOR_JS = "__JS_DASHBOARD__"
_DIR = Path(__file__).parent
_ARCHIVOS_JS = ("template_icons.js", "template_core.js", "template_render.js", "template_main.js")


def _ensamblar_js() -> str:
    return "\n\n".join((_DIR / nombre).read_text(encoding="utf-8") for nombre in _ARCHIVOS_JS)


def generar_dashboard(
    conn: sqlite3.Connection,
    ruta_salida: str | Path,
    generado_en: datetime.datetime | None = None,
) -> Path:
    datos = construir_datos_dashboard(conn)
    datos["generado_en"] = (generado_en or datetime.datetime.now()).isoformat()

    plantilla = (_DIR / "template.html").read_text(encoding="utf-8")
    css = (_DIR / "template.css").read_text(encoding="utf-8")
    js = _ensamblar_js()

    if _MARCADOR_DATOS not in js:
        raise ValueError(f"El JS ensamblado no contiene el marcador {_MARCADOR_DATOS}")
    if _MARCADOR_CSS not in plantilla or _MARCADOR_JS not in plantilla:
        raise ValueError("La plantilla no contiene los marcadores de CSS/JS esperados")

    js = js.replace(_MARCADOR_DATOS, json.dumps(datos, ensure_ascii=False))
    html = plantilla.replace(_MARCADOR_CSS, css).replace(_MARCADOR_JS, js)

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_salida.write_text(html, encoding="utf-8")
    return ruta_salida
