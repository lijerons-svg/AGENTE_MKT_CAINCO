"""Genera ROI_Resultados.xlsx: las mismas filas que ROI_Campanas.xlsx (una
por campaña), más columnas de carga manual para seguimiento comercial
(Nombre de evento, Tipo, Unidad, Leads, Subscribers, Revenue) y métricas
calculadas con fórmula de Excel (Costo por lead, % de conversión, ROI).
También arma una segunda hoja, "Resumen por Evento", que agrupa las
campañas por "Nombre de evento" (varias campañas pueden ser el mismo
evento) sumando Inversión/Leads/Subscribers/Revenue.

Este archivo es un archivo SEPARADO de ROI_Campanas.xlsx a propósito: LEE
ese archivo para saber Mes/Campaña/Inversión de cada campaña, pero nunca
lo modifica. Así, una corrida de este archivo no puede "chocar" con
ROI_Campanas.xlsx, ni viceversa — son dos procesos independientes que
comparten una sola fuente de lectura.

Mes, Campaña e Inversión total se recalculan en cada corrida (así absorbe
solo la revisión de los últimos 7 días que hace la automatización cada
mañana). Nombre de evento, Tipo, Unidad, Leads, Subscribers y Revenue son
manuales — Sandy los completa a mano — así que si el archivo ya existe se
abre y se edita EN SITIO: esas celdas de una fila que ya existía NUNCA se
leen ni se reescriben, solo se actualizan las columnas automáticas de esa
fila (emparejando por "ID de campaña", no por posición). Las campañas
nuevas se agregan al final, con las columnas manuales vacías para que
Sandy las complete.

Costo por lead, % de conversión y ROI son fórmulas de Excel (no valores
fijos), así que se recalculan solas en el momento en que Sandy escribe un
valor en Leads/Subscribers/Revenue, sin esperar a la próxima corrida:
    Costo por lead = Inversión total ÷ Leads
    % de conversión = Subscribers ÷ Leads
    ROI = (Revenue − Inversión total) ÷ Inversión total

La hoja "Resumen por Evento" no tiene ninguna columna manual propia — es
una suma de lo que Sandy ya cargó por campaña — así que se reconstruye
entera en cada corrida, sin nada que preservar ni riesgo de desalineación.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from marketing_analytics.reports.roi_builder import (
    COL_CAMPANA as _ROI_COL_CAMPANA,
    COL_ID_CAMPANA as _ROI_COL_ID_CAMPANA,
    COL_INVERSION as _ROI_COL_INVERSION,
    COL_MES as _ROI_COL_MES,
    autoajustar_columnas,
    tiene_columnas_esperadas,
)

ENCABEZADOS = [
    "Mes",
    "Campaña",
    "ID de campaña",
    "Inversión total",
    "Nombre de evento",
    "Tipo",
    "Unidad",
    "Leads",
    "Subscribers",
    "Revenue",
    "Costo por lead",
    "% de conversión",
    "ROI",
]
COL_MES = 1
COL_CAMPANA = 2
COL_ID_CAMPANA = 3
COL_INVERSION = 4
COL_NOMBRE_EVENTO = 5
COL_TIPO = 6
COL_UNIDAD = 7
COL_LEADS = 8
COL_SUBSCRIBERS = 9
COL_REVENUE = 10
COL_COSTO_POR_LEAD = 11
COL_PORCENTAJE_CONVERSION = 12
COL_ROI = 13
FORMATO_MONEDA = '"$"#,##0.00'
FORMATO_PORCENTAJE = "0.0%"

HOJA_RESUMEN = "Resumen por Evento"
ENCABEZADOS_RESUMEN = [
    "Nombre de evento", "Inversión total", "Leads", "Subscribers", "Revenue",
    "Costo por lead", "% de conversión", "ROI",
]
SIN_ASIGNAR = "(Sin asignar)"


def generar_roi_resultados(ruta_roi_campanas: str | Path, ruta_salida: str | Path) -> Path | None:
    ruta_roi_campanas = Path(ruta_roi_campanas)
    ruta_salida = Path(ruta_salida)

    if not ruta_roi_campanas.exists():
        return None

    campanas = _leer_campanas(ruta_roi_campanas)

    wb = load_workbook(ruta_salida) if ruta_salida.exists() else None
    ws = wb.active if wb is not None else None

    if ws is None or not tiene_columnas_esperadas(ws, ENCABEZADOS):
        wb = Workbook()
        ws = wb.active
        ws.title = "ROI Resultados"
        ws.append(ENCABEZADOS)
        for celda in ws[1]:
            celda.font = Font(bold=True)

    fila_por_id: dict[str, int] = {}
    for fila_celdas in ws.iter_rows(min_row=2):
        id_celda = fila_celdas[COL_ID_CAMPANA - 1].value
        if id_celda is not None:
            fila_por_id[id_celda] = fila_celdas[0].row

    for id_campana, mes, campana, inversion in campanas:
        fila = fila_por_id.get(id_campana)
        if fila is None:
            fila = ws.max_row + 1
            fila_por_id[id_campana] = fila
            ws.cell(row=fila, column=COL_ID_CAMPANA, value=id_campana)

        # Automáticas: Mes, Campaña, Inversión total. Nombre de evento en
        # adelante (manuales) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=COL_MES, value=mes)
        ws.cell(row=fila, column=COL_CAMPANA, value=campana)
        celda_inversion = ws.cell(row=fila, column=COL_INVERSION, value=inversion)
        celda_inversion.number_format = FORMATO_MONEDA

        _escribir_formulas(ws, fila)

    autoajustar_columnas(ws)
    _actualizar_resumen_por_evento(wb, ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _escribir_formulas(ws: Worksheet, fila: int) -> None:
    inversion = f"D{fila}"
    leads = f"H{fila}"
    subscribers = f"I{fila}"
    revenue = f"J{fila}"

    celda_costo = ws.cell(row=fila, column=COL_COSTO_POR_LEAD, value=f'=IFERROR({inversion}/{leads},"")')
    celda_costo.number_format = FORMATO_MONEDA

    celda_conversion = ws.cell(
        row=fila, column=COL_PORCENTAJE_CONVERSION, value=f'=IFERROR({subscribers}/{leads},"")'
    )
    celda_conversion.number_format = FORMATO_PORCENTAJE

    celda_roi = ws.cell(row=fila, column=COL_ROI, value=f'=IFERROR(({revenue}-{inversion})/{inversion},"")')
    celda_roi.number_format = FORMATO_PORCENTAJE


def _actualizar_resumen_por_evento(wb: Workbook, ws_campanas: Worksheet) -> None:
    """Suma Inversión/Leads/Subscribers/Revenue por Nombre de evento. No
    tiene ninguna columna manual propia, así que se reconstruye entera
    cada vez — nada que preservar."""
    agregados: dict[str, dict] = {}
    for fila in ws_campanas.iter_rows(min_row=2, values_only=True):
        nombre_evento = fila[COL_NOMBRE_EVENTO - 1] or SIN_ASIGNAR
        datos = agregados.setdefault(nombre_evento, {"inversion": 0.0, "leads": 0.0, "subscribers": 0.0, "revenue": 0.0})
        datos["inversion"] += fila[COL_INVERSION - 1] or 0
        datos["leads"] += fila[COL_LEADS - 1] or 0
        datos["subscribers"] += fila[COL_SUBSCRIBERS - 1] or 0
        datos["revenue"] += fila[COL_REVENUE - 1] or 0

    if HOJA_RESUMEN in wb.sheetnames:
        del wb[HOJA_RESUMEN]
    ws = wb.create_sheet(HOJA_RESUMEN)
    ws.append(ENCABEZADOS_RESUMEN)
    for celda in ws[1]:
        celda.font = Font(bold=True)

    for nombre_evento in sorted(agregados, key=str):
        datos = agregados[nombre_evento]
        fila = ws.max_row + 1
        ws.cell(row=fila, column=1, value=nombre_evento)
        celda_inv = ws.cell(row=fila, column=2, value=datos["inversion"])
        celda_inv.number_format = FORMATO_MONEDA
        ws.cell(row=fila, column=3, value=datos["leads"])
        ws.cell(row=fila, column=4, value=datos["subscribers"])
        celda_rev = ws.cell(row=fila, column=5, value=datos["revenue"])
        celda_rev.number_format = FORMATO_MONEDA

        inversion = f"B{fila}"
        leads = f"C{fila}"
        subscribers = f"D{fila}"
        revenue = f"E{fila}"
        celda_costo = ws.cell(row=fila, column=6, value=f'=IFERROR({inversion}/{leads},"")')
        celda_costo.number_format = FORMATO_MONEDA
        celda_conv = ws.cell(row=fila, column=7, value=f'=IFERROR({subscribers}/{leads},"")')
        celda_conv.number_format = FORMATO_PORCENTAJE
        celda_roi = ws.cell(row=fila, column=8, value=f'=IFERROR(({revenue}-{inversion})/{inversion},"")')
        celda_roi.number_format = FORMATO_PORCENTAJE

    autoajustar_columnas(ws)


def _leer_campanas(ruta_roi_campanas: Path) -> list[tuple[str, str, str, float]]:
    wb = load_workbook(ruta_roi_campanas, data_only=True)
    ws = wb.active
    campanas = []
    for fila in ws.iter_rows(min_row=2, values_only=True):
        id_campana = fila[_ROI_COL_ID_CAMPANA - 1]
        if id_campana is None:
            continue
        mes = fila[_ROI_COL_MES - 1]
        campana = fila[_ROI_COL_CAMPANA - 1]
        inversion = fila[_ROI_COL_INVERSION - 1] or 0
        campanas.append((id_campana, mes, campana, inversion))
    return campanas
