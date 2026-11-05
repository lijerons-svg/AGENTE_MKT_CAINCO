"""Arma el Excel de control de gasto por actividad a partir de las filas
que devuelven los parsers de recibos (Meta, Mailchimp)."""
from __future__ import annotations

import io

from openpyxl import Workbook

from marketing_analytics.reports.excel_writer_utils import escribir_hoja

_ENCABEZADOS = [
    "Código - Número de referencia",
    "Identificador de la unidad",
    "Nombre de la actividad",
    "Monto invertido ($)",
    "Resultado obtenido",
    "Tipo de resultado",
    "Fuente",
]


def _fila_a_tupla(fila: dict) -> tuple:
    return (
        fila["codigo_referencia"],
        fila["identificador_unidad"],
        fila["nombre_actividad"],
        fila["monto_invertido"],
        fila["resultado_obtenido"],
        fila.get("resultado_tipo", ""),
        fila.get("fuente", ""),
    )


def construir_excel(filas: list[dict]) -> bytes:
    """Devuelve el contenido del .xlsx (bytes), listo para descargar."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Gasto por actividad"
    escribir_hoja(ws, _ENCABEZADOS, [_fila_a_tupla(f) for f in filas])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
