"""Genera ROI_Resultados.xlsx: las mismas filas que ROI_Campanas.xlsx (una
por campaña), más columnas de carga manual para clasificar cada campaña
(Nombre de evento, Tipo, Unidad). Los resultados comerciales en sí (Leads,
Subscribers, Revenue) se cargan una sola vez por evento, en la segunda
hoja "Resumen por Evento" — no por campaña, porque son resultados del
evento en general, no de cada campaña individual.

Este archivo es un archivo SEPARADO de ROI_Campanas.xlsx a propósito: LEE
ese archivo para saber Mes/Campaña/Inversión de cada campaña, pero nunca
lo modifica. Así, una corrida de este archivo no puede "chocar" con
ROI_Campanas.xlsx, ni viceversa — son dos procesos independientes que
comparten una sola fuente de lectura.

Hoja "ROI Resultados" (por campaña):
    Mes, Campaña e Inversión total se recalculan en cada corrida (así
    absorbe sola la revisión de los últimos 7 días que hace la
    automatización cada mañana). Nombre de evento, Tipo y Unidad son
    manuales — Sandy los completa a mano — así que si el archivo ya
    existe se abre y se edita EN SITIO: esas celdas de una fila que ya
    existía NUNCA se leen ni se reescriben, solo se actualizan las
    columnas automáticas de esa fila (emparejando por "ID de campaña", no
    por posición). Las campañas nuevas se agregan al final, con las
    columnas manuales vacías para que Sandy las complete.

Hoja "Resumen por Evento" (por Nombre de evento):
    Inversión total se recalcula en cada corrida, sumando todas las
    campañas con ese nombre de evento. Tipo y Unidad también son
    automáticos acá (se toman de cualquiera de las campañas del evento en
    "ROI Resultados"). Leads, Subscribers y Revenue son manuales,
    protegidos igual que en la otra hoja pero emparejando por "Nombre de
    evento" en vez de por ID de campaña. Costo por lead, % de conversión y
    ROI son fórmulas de Excel, se recalculan solas al escribir:
        Costo por lead = Inversión total ÷ Leads
        % de conversión = Subscribers ÷ Leads
        ROI = (Revenue − Inversión total) ÷ Inversión total
    Las campañas sin evento asignado todavía se agrupan bajo
    "(Sin asignar)". Si un evento deja de tener campañas (porque se
    reasignaron) y no tiene datos manuales cargados, su fila se elimina en
    vez de quedar como un fantasma con el monto viejo.
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

ENCABEZADOS = ["Mes", "Campaña", "ID de campaña", "Inversión total", "Nombre de evento", "Tipo", "Unidad"]
COL_MES = 1
COL_CAMPANA = 2
COL_ID_CAMPANA = 3
COL_INVERSION = 4
COL_NOMBRE_EVENTO = 5
COL_TIPO = 6
COL_UNIDAD = 7
FORMATO_MONEDA = '"$"#,##0.00'
FORMATO_PORCENTAJE = "0.0%"

HOJA_RESUMEN = "Resumen por Evento"
ENCABEZADOS_RESUMEN = [
    "Nombre de evento", "Tipo", "Unidad", "Inversión total", "Leads", "Subscribers", "Revenue",
    "Costo por lead", "% de conversión", "ROI",
]
COL_R_NOMBRE = 1
COL_R_TIPO = 2
COL_R_UNIDAD = 3
COL_R_INVERSION = 4
COL_R_LEADS = 5
COL_R_SUBSCRIBERS = 6
COL_R_REVENUE = 7
COL_R_COSTO_POR_LEAD = 8
COL_R_PORCENTAJE_CONVERSION = 9
COL_R_ROI = 10
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

    autoajustar_columnas(ws)
    _actualizar_resumen_por_evento(wb, ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _actualizar_resumen_por_evento(wb: Workbook, ws_campanas: Worksheet) -> None:
    datos_por_evento: dict[str, dict] = {}
    for fila in ws_campanas.iter_rows(min_row=2, values_only=True):
        nombre_evento = fila[COL_NOMBRE_EVENTO - 1] or SIN_ASIGNAR
        datos = datos_por_evento.setdefault(nombre_evento, {"inversion": 0.0, "tipo": None, "unidad": None})
        datos["inversion"] += fila[COL_INVERSION - 1] or 0
        if datos["tipo"] is None and fila[COL_TIPO - 1]:
            datos["tipo"] = fila[COL_TIPO - 1]
        if datos["unidad"] is None and fila[COL_UNIDAD - 1]:
            datos["unidad"] = fila[COL_UNIDAD - 1]

    ws = wb[HOJA_RESUMEN] if HOJA_RESUMEN in wb.sheetnames else None
    if ws is not None and not tiene_columnas_esperadas(ws, ENCABEZADOS_RESUMEN):
        del wb[HOJA_RESUMEN]
        ws = None
    if ws is None:
        ws = wb.create_sheet(HOJA_RESUMEN)
        ws.append(ENCABEZADOS_RESUMEN)
        for celda in ws[1]:
            celda.font = Font(bold=True)

    fila_por_nombre: dict[str, int] = {}
    for fila_celdas in ws.iter_rows(min_row=2):
        nombre_celda = fila_celdas[COL_R_NOMBRE - 1].value
        if nombre_celda is not None:
            fila_por_nombre[nombre_celda] = fila_celdas[0].row

    # Filas que ya existían pero cuyo evento ya no tiene campañas (por
    # ejemplo, porque Sandy reasignó todas sus campañas a otro evento) y
    # no tienen ningún dato manual cargado: se borran de una, ANTES de
    # escribir nada más. Si se borraran al final, las filas que quedan más
    # abajo ya tendrían fórmulas escritas apuntando a su posición vieja
    # (antes del corrimiento) y quedarían apuntando a la fila equivocada.
    filas_a_eliminar = [
        fila
        for nombre_evento, fila in fila_por_nombre.items()
        if nombre_evento not in datos_por_evento
        and all(
            ws.cell(row=fila, column=columna).value is None
            for columna in (COL_R_LEADS, COL_R_SUBSCRIBERS, COL_R_REVENUE)
        )
    ]
    for fila in sorted(filas_a_eliminar, reverse=True):
        ws.delete_rows(fila, 1)

    if filas_a_eliminar:
        fila_por_nombre = {}
        for fila_celdas in ws.iter_rows(min_row=2):
            nombre_celda = fila_celdas[COL_R_NOMBRE - 1].value
            if nombre_celda is not None:
                fila_por_nombre[nombre_celda] = fila_celdas[0].row

    for nombre_evento in sorted(set(datos_por_evento) | set(fila_por_nombre), key=str):
        # Datos de un evento huérfano con datos manuales (no se borró
        # arriba): ya no tiene campañas, así que inversión/tipo/unidad
        # quedan vacíos.
        datos = datos_por_evento.get(nombre_evento, {"inversion": 0.0, "tipo": None, "unidad": None})
        fila = fila_por_nombre.get(nombre_evento)
        if fila is None:
            fila = ws.max_row + 1
            fila_por_nombre[nombre_evento] = fila
            ws.cell(row=fila, column=COL_R_NOMBRE, value=nombre_evento)

        # Automáticas: Tipo, Unidad, Inversión total. Leads en adelante
        # (manuales) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=COL_R_TIPO, value=datos["tipo"])
        ws.cell(row=fila, column=COL_R_UNIDAD, value=datos["unidad"])
        celda_inversion = ws.cell(row=fila, column=COL_R_INVERSION, value=datos["inversion"])
        celda_inversion.number_format = FORMATO_MONEDA
        _escribir_formulas_resumen(ws, fila)

    autoajustar_columnas(ws)


def _escribir_formulas_resumen(ws: Worksheet, fila: int) -> None:
    inversion = f"D{fila}"
    leads = f"E{fila}"
    subscribers = f"F{fila}"
    revenue = f"G{fila}"

    celda_costo = ws.cell(row=fila, column=COL_R_COSTO_POR_LEAD, value=f'=IFERROR({inversion}/{leads},"")')
    celda_costo.number_format = FORMATO_MONEDA

    celda_conv = ws.cell(
        row=fila, column=COL_R_PORCENTAJE_CONVERSION, value=f'=IFERROR({subscribers}/{leads},"")'
    )
    celda_conv.number_format = FORMATO_PORCENTAJE

    celda_roi = ws.cell(row=fila, column=COL_R_ROI, value=f'=IFERROR(({revenue}-{inversion})/{inversion},"")')
    celda_roi.number_format = FORMATO_PORCENTAJE


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
