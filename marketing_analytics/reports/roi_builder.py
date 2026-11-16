"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su
inversión total (sumada a lo largo de toda la campaña, todas las redes y
todos los días). Es una tabla simple de solo lectura, pensada como fuente
para que Sandy la referencie desde otra planilla (por ejemplo, con
BUSCARV/VLOOKUP por "ID de campaña") — no tiene columnas de carga manual,
así que se regenera entera en cada corrida sin que haya nada que preservar.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

_ENCABEZADOS = ["Campaña", "ID de campaña", "Inversión total"]
_FORMATO_MONEDA = '"$"#,##0.00'


def generar_roi_campanas(conn: sqlite3.Connection, ruta_salida: str | Path) -> Path:
    ruta_salida = Path(ruta_salida)

    campanas = conn.execute(
        """
        SELECT id_campana_origen, campana, SUM(importe_gastado) AS inversion_total
        FROM meta_ads
        GROUP BY id_campana_origen
        ORDER BY campana
        """
    ).fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "ROI Campañas"
    ws.append(_ENCABEZADOS)
    for celda in ws[1]:
        celda.font = Font(bold=True)

    for campana in campanas:
        ws.append([campana["campana"], campana["id_campana_origen"], campana["inversion_total"]])
        ws.cell(row=ws.max_row, column=3).number_format = _FORMATO_MONEDA

    _autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
