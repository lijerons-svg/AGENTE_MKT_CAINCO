"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su
inversión total y columnas de carga manual (leads, ventas, monto) que
alimentan fórmulas de costo por venta, ticket promedio, tasa de conversión
y ROI.

A diferencia de Historico_RRSS.xlsx, este archivo SÍ tiene una fuente de
verdad que vive fuera de la base de datos: lo que Sandy carga a mano en las
columnas D/E/F (Cantidad de leads, Cantidad de ventas, Monto total de
cierre). Por eso, si el archivo ya existe, se ABRE Y SE EDITA EN SITIO: las
celdas D/E/F y sus encabezados de una fila/columna que ya existía NUNCA se
leen ni se reescriben — solo se actualizan las columnas automáticas
(Unidad, Campaña, Inversión) y las fórmulas (columnas G en adelante,
incluidos sus encabezados). Las campañas nuevas se agregan al final. Esto
es más seguro que "leer todo a un diccionario y reconstruir el archivo de
cero": si una fila ya existe, sus columnas manuales simplemente no se
tocan, punto — ni el valor ni el título que Sandy le haya puesto.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

# Encabezados de las columnas manuales (A-F): solo se escriben una vez, al
# crear el archivo por primera vez. Después son de Sandy — puede
# renombrarlas y esos nombres se respetan para siempre.
_ENCABEZADOS_MANUALES = [
    "Unidad",
    "Campaña",
    "ID de campaña",
    "Cantidad de leads",
    "Cantidad de ventas",
    "Monto total de cierre",
]

# Encabezados de las columnas automáticas (G en adelante): se reescriben en
# cada corrida, para que si cambia la fórmula/criterio acá, el archivo de
# Sandy quede sincronizado sin que ella tenga que tocar nada.
_ENCABEZADOS_AUTOMATICOS = [
    "Inversión total",
    "Costo por venta",
    "Ticket promedio",
    "Tasa de conversión",
    "ROI",
]

_COL_UNIDAD = 1
_COL_CAMPANA = 2
_COL_ID_CAMPANA = 3
_COL_LEADS = 4
_COL_VENTAS = 5
_COL_MONTO_CIERRE = 6
_COL_INVERSION = 7
_FORMATO_MONEDA = '"$"#,##0.00'
_FORMATO_PORCENTAJE = "0.0%"


def generar_roi_campanas(conn: sqlite3.Connection, ruta_salida: str | Path) -> Path:
    ruta_salida = Path(ruta_salida)

    campanas = conn.execute(
        """
        SELECT id_campana_origen, perfil_unidad, campana, SUM(importe_gastado) AS inversion_total
        FROM meta_ads
        GROUP BY id_campana_origen
        ORDER BY perfil_unidad, campana
        """
    ).fetchall()

    if ruta_salida.exists():
        wb = load_workbook(ruta_salida)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "ROI Campañas"
        ws.append(_ENCABEZADOS_MANUALES)
        for celda in ws[1]:
            celda.font = Font(bold=True)

    for columna, texto in enumerate(_ENCABEZADOS_AUTOMATICOS, start=_COL_INVERSION):
        celda = ws.cell(row=1, column=columna, value=texto)
        celda.font = Font(bold=True)

    fila_por_id: dict[str, int] = {}
    for fila_celdas in ws.iter_rows(min_row=2):
        id_celda = fila_celdas[_COL_ID_CAMPANA - 1].value
        if id_celda is not None:
            fila_por_id[id_celda] = fila_celdas[0].row

    for campana in campanas:
        id_campana = campana["id_campana_origen"]
        fila = fila_por_id.get(id_campana)
        if fila is None:
            fila = ws.max_row + 1
            fila_por_id[id_campana] = fila
            ws.cell(row=fila, column=_COL_ID_CAMPANA, value=id_campana)

        # Solo columnas automáticas: A, B, G. D/E/F (manuales) jamás se tocan
        # cuando la fila ya existía.
        ws.cell(row=fila, column=_COL_UNIDAD, value=campana["perfil_unidad"])
        ws.cell(row=fila, column=_COL_CAMPANA, value=campana["campana"])
        celda_inversion = ws.cell(row=fila, column=_COL_INVERSION, value=campana["inversion_total"])
        celda_inversion.number_format = _FORMATO_MONEDA

        _escribir_formulas(ws, fila)

    ws.column_dimensions["G"].hidden = True
    _autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _escribir_formulas(ws: Worksheet, fila: int) -> None:
    leads = f"D{fila}"
    ventas = f"E{fila}"
    monto = f"F{fila}"
    inv = f"G{fila}"

    celda_costo = ws.cell(row=fila, column=8, value=f'=IFERROR({inv}/{ventas},"")')
    celda_costo.number_format = _FORMATO_MONEDA

    celda_ticket = ws.cell(row=fila, column=9, value=f'=IFERROR({monto}/{ventas},"")')
    celda_ticket.number_format = _FORMATO_MONEDA

    celda_tasa = ws.cell(row=fila, column=10, value=f'=IFERROR({ventas}/{leads},"")')
    celda_tasa.number_format = _FORMATO_PORCENTAJE

    celda_roi = ws.cell(row=fila, column=11, value=f'=IFERROR(({monto}-{inv})/{inv},"")')
    celda_roi.number_format = _FORMATO_PORCENTAJE


def _autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
