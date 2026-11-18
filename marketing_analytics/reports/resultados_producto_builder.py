"""Genera ROI_Resultados.xlsx: una fila por Nombre_Producto (varias
campañas pueden ser el mismo producto/evento) con su inversión total
(automática) y columnas de carga manual para seguimiento comercial
(Leads, Resultados USD) más un ROI calculado con fórmula de Excel.

Este archivo es un archivo SEPARADO de ROI_Campanas.xlsx a propósito:
LEE ese archivo para saber la inversión y el producto de cada campaña,
pero nunca lo modifica. Así, una corrida de este archivo no puede
"chocar" con ROI_Campanas.xlsx, ni viceversa — son dos procesos
independientes que comparten una sola fuente de lectura.

Inversión total se recalcula en cada corrida (así absorbe sola la
revisión de los últimos 7 días que hace la automatización cada mañana).
Leads y Resultados USD son manuales — Sandy los completa a mano — así que
si el archivo ya existe se abre y se edita EN SITIO: esas celdas de una
fila que ya existía NUNCA se leen ni se reescriben, solo se actualiza la
Inversión total de esa fila (emparejando por "Nombre_Producto", no por
posición). ROI es una fórmula de Excel ((Resultados - Inversión) /
Inversión), así que se recalcula sola en el momento en que Sandy escribe
un valor en Resultados, sin esperar a la próxima corrida.

Las campañas sin producto asignado todavía se agrupan bajo
"(Sin asignar)". Si una fila deja de tener campañas (porque se
reasignaron) y no tiene datos manuales cargados, se elimina en vez de
quedar como un fantasma con el monto viejo.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from marketing_analytics.reports.roi_builder import (
    COL_INVERSION,
    COL_NOMBRE_PRODUCTO,
    autoajustar_columnas,
    tiene_columnas_esperadas,
)

ENCABEZADOS = ["Nombre_Producto", "Inversión total", "Leads", "Resultados USD", "ROI"]
COL_NOMBRE = 1
COL_R_INVERSION = 2
COL_LEADS = 3
COL_RESULTADOS = 4
COL_ROI = 5
FORMATO_MONEDA = '"$"#,##0.00'
FORMATO_PORCENTAJE = "0.0%"
SIN_ASIGNAR = "(Sin asignar)"


def generar_resultados_producto(ruta_roi_campanas: str | Path, ruta_salida: str | Path) -> Path | None:
    ruta_roi_campanas = Path(ruta_roi_campanas)
    ruta_salida = Path(ruta_salida)

    if not ruta_roi_campanas.exists():
        return None

    inversion_por_producto = _leer_inversion_por_producto(ruta_roi_campanas)

    wb = load_workbook(ruta_salida) if ruta_salida.exists() else None
    ws = wb.active if wb is not None else None

    if ws is None or not tiene_columnas_esperadas(ws, ENCABEZADOS):
        wb = Workbook()
        ws = wb.active
        ws.title = "ROI Resultados"
        ws.append(ENCABEZADOS)
        for celda in ws[1]:
            celda.font = Font(bold=True)

    fila_por_nombre: dict[str, int] = {}
    for fila_celdas in ws.iter_rows(min_row=2):
        nombre_celda = fila_celdas[COL_NOMBRE - 1].value
        if nombre_celda is not None:
            fila_por_nombre[nombre_celda] = fila_celdas[0].row

    # Incluye también las filas que ya existían pero cuyo nombre de
    # producto ya no tiene campañas (por ejemplo, porque Sandy reasignó
    # todas sus campañas a otro producto) — si no, esa fila queda con el
    # monto de inversión viejo para siempre, como un fantasma. Si además
    # no tiene ningún dato manual cargado, directamente se borra.
    claves = sorted(set(inversion_por_producto) | set(fila_por_nombre), key=str)
    filas_a_eliminar: list[int] = []
    for nombre_producto in claves:
        inversion = inversion_por_producto.get(nombre_producto)
        fila = fila_por_nombre.get(nombre_producto)

        if inversion is None:
            tiene_datos_manuales = any(
                ws.cell(row=fila, column=columna).value is not None
                for columna in (COL_LEADS, COL_RESULTADOS)
            )
            if not tiene_datos_manuales:
                filas_a_eliminar.append(fila)
                continue
            inversion = 0.0

        if fila is None:
            fila = ws.max_row + 1
            fila_por_nombre[nombre_producto] = fila
            ws.cell(row=fila, column=COL_NOMBRE, value=nombre_producto)

        celda_inversion = ws.cell(row=fila, column=COL_R_INVERSION, value=inversion)
        celda_inversion.number_format = FORMATO_MONEDA
        _escribir_formula_roi(ws, fila)

    for fila in sorted(filas_a_eliminar, reverse=True):
        ws.delete_rows(fila, 1)

    autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _escribir_formula_roi(ws: Worksheet, fila: int) -> None:
    inversion = f"B{fila}"
    resultados = f"D{fila}"
    celda_roi = ws.cell(row=fila, column=COL_ROI, value=f'=IFERROR(({resultados}-{inversion})/{inversion},"")')
    celda_roi.number_format = FORMATO_PORCENTAJE


def _leer_inversion_por_producto(ruta_roi_campanas: Path) -> dict[str, float]:
    wb = load_workbook(ruta_roi_campanas, data_only=True)
    ws = wb.active
    agregados: dict[str, float] = {}
    for fila in ws.iter_rows(min_row=2, values_only=True):
        inversion = fila[COL_INVERSION - 1] or 0
        nombre_producto = fila[COL_NOMBRE_PRODUCTO - 1] or SIN_ASIGNAR
        agregados[nombre_producto] = agregados.get(nombre_producto, 0.0) + inversion
    return agregados
