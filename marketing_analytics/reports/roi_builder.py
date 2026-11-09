"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su
inversión total y columnas de carga manual (cierres, no cierres, monto) que
alimentan fórmulas de costo de cierre, ticket promedio, tasa de cierre y ROI.

A diferencia de Historico_RRSS.xlsx, este archivo SÍ tiene una fuente de
verdad que vive fuera de la base de datos: lo que Sandy carga a mano en las
columnas D/E/F. Por eso, antes de recrear el archivo, se lee el que ya existe
y esos valores se trasladan al nuevo (buscando por ID de campaña, columna C,
no por posición de fila — así una campaña nueva que se inserte en el medio no
desalinea los datos manuales de las demás).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

_ENCABEZADOS = [
    "Unidad",
    "Campaña",
    "ID de campaña",
    "Cantidad de cierres",
    "Cantidad de no cierres",
    "Monto total de cierre",
    "Inversión total",
    "Costo de cierre",
    "Ticket promedio",
    "Tasa de cierre",
    "ROI",
]

# Columnas de carga manual (1-based, coinciden con el orden de _ENCABEZADOS).
_COL_CIERRES = 4
_COL_NO_CIERRES = 5
_COL_MONTO_CIERRE = 6
_COL_INVERSION = 7
_COL_ID_CAMPANA = 3
_FORMATO_MONEDA = '"$"#,##0.00'
_FORMATO_PORCENTAJE = "0.0%"


def generar_roi_campanas(conn: sqlite3.Connection, ruta_salida: str | Path) -> Path:
    ruta_salida = Path(ruta_salida)
    datos_manuales = _leer_datos_manuales_existentes(ruta_salida)

    campanas = conn.execute(
        """
        SELECT id_campana_origen, perfil_unidad, campana, SUM(importe_gastado) AS inversion_total
        FROM meta_ads
        GROUP BY id_campana_origen
        ORDER BY perfil_unidad, campana
        """
    ).fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "ROI Campañas"
    ws.append(_ENCABEZADOS)
    for celda in ws[1]:
        celda.font = Font(bold=True)

    for campana in campanas:
        id_campana = campana["id_campana_origen"]
        cierres, no_cierres, monto_cierre = datos_manuales.get(id_campana, (None, None, None))
        fila = ws.max_row + 1
        ws.append(
            [
                campana["perfil_unidad"],
                campana["campana"],
                id_campana,
                cierres,
                no_cierres,
                monto_cierre,
                campana["inversion_total"],
            ]
        )
        _escribir_formulas(ws, fila)

    ws.column_dimensions["G"].hidden = True
    _autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _escribir_formulas(ws: Worksheet, fila: int) -> None:
    c = f"D{fila}"  # cierres
    nc = f"E{fila}"  # no cierres
    m = f"F{fila}"  # monto de cierre
    inv = f"G{fila}"  # inversión total

    celda_costo = ws.cell(row=fila, column=8, value=f'=IFERROR({inv}/{c},"")')
    celda_costo.number_format = _FORMATO_MONEDA

    celda_ticket = ws.cell(row=fila, column=9, value=f'=IFERROR({m}/{c},"")')
    celda_ticket.number_format = _FORMATO_MONEDA

    celda_tasa = ws.cell(row=fila, column=10, value=f'=IFERROR({c}/({c}+{nc}),"")')
    celda_tasa.number_format = _FORMATO_PORCENTAJE

    celda_roi = ws.cell(row=fila, column=11, value=f'=IFERROR(({m}-{inv})/{inv},"")')
    celda_roi.number_format = _FORMATO_PORCENTAJE

    ws.cell(row=fila, column=7).number_format = _FORMATO_MONEDA


def _leer_datos_manuales_existentes(
    ruta_salida: Path,
) -> dict[str, tuple[int | None, int | None, float | None]]:
    if not ruta_salida.exists():
        return {}
    wb = load_workbook(ruta_salida, data_only=False)
    ws = wb.active
    datos: dict[str, tuple[int | None, int | None, float | None]] = {}
    for fila in ws.iter_rows(min_row=2, values_only=True):
        id_campana = fila[_COL_ID_CAMPANA - 1]
        if id_campana is None:
            continue
        datos[id_campana] = (
            fila[_COL_CIERRES - 1],
            fila[_COL_NO_CIERRES - 1],
            fila[_COL_MONTO_CIERRE - 1],
        )
    return datos


def _autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
