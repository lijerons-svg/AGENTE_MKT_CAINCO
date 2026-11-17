"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su mes,
nombre, ID e inversión total (sumada a lo largo de toda la campaña, todas
las redes y todos los días). Es una tabla simple de solo lectura, pensada
como fuente para que Sandy la referencie desde otra planilla (por ejemplo,
con BUSCARV/VLOOKUP por "ID de campaña") — no tiene columnas de carga
manual, así que se regenera entera en cada corrida sin que haya nada que
preservar.

El "Mes" es el de la fecha de inicio real de la campaña en Meta
(fecha_inicio_campana); si esa fecha no está disponible (campañas cargadas
antes de que el conector empezara a capturarla), se usa el mes de la
publicación de insights más antigua como respaldo.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

_ENCABEZADOS = ["Mes", "Campaña", "ID de campaña", "Inversión total"]
_FORMATO_MONEDA = '"$"#,##0.00'
_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def generar_roi_campanas(conn: sqlite3.Connection, ruta_salida: str | Path) -> Path:
    ruta_salida = Path(ruta_salida)

    campanas = conn.execute(
        """
        SELECT
            id_campana_origen,
            campana,
            SUM(importe_gastado) AS inversion_total,
            COALESCE(MIN(fecha_inicio_campana), MIN(fecha_publicacion)) AS mes_referencia
        FROM meta_ads
        GROUP BY id_campana_origen
        ORDER BY mes_referencia, campana
        """
    ).fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "ROI Campañas"
    ws.append(_ENCABEZADOS)
    for celda in ws[1]:
        celda.font = Font(bold=True)

    for campana in campanas:
        mes = _mes_legible(campana["mes_referencia"])
        ws.append([mes, campana["campana"], campana["id_campana_origen"], campana["inversion_total"]])
        ws.cell(row=ws.max_row, column=4).number_format = _FORMATO_MONEDA

    _autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _mes_legible(fecha_texto: str | None) -> str:
    if not fecha_texto:
        return ""
    anio, mes, *_ = fecha_texto.split("-")
    return f"{_MESES[int(mes) - 1]} {anio}"


def _autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
