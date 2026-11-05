"""Utilidades compartidas para escribir hojas de Excel con openpyxl."""
from __future__ import annotations

from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

_ENCABEZADO_FONT = Font(bold=True)


def escribir_hoja(
    ws: Worksheet, encabezados: list[str], filas: list[tuple], columnas_porcentaje: set[int] | None = None
) -> None:
    """`columnas_porcentaje`: índices (0-based) de columnas cuyo valor ya
    viene como fracción (0-1), no como número entero de %. Se les aplica el
    formato de Excel en vez de multiplicar por 100 al escribir — así el
    valor sigue siendo correcto para fórmulas y Excel lo muestra como
    "45.23%" en vez de "0.4523", que a simple vista se lee como 0.45%."""
    ws.append(encabezados)
    for celda in ws[1]:
        celda.font = _ENCABEZADO_FONT
    columnas_porcentaje = columnas_porcentaje or set()
    for fila in filas:
        ws.append(fila)
        if columnas_porcentaje:
            fila_ws = ws[ws.max_row]
            for indice in columnas_porcentaje:
                fila_ws[indice].number_format = "0.00%"
    _autoajustar_columnas(ws)


def _autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
