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

Las columnas se ubican por su TEXTO de encabezado, nunca por una posición
fija (ver resolver_columnas en roi_builder.py). Si el archivo ya existe y
le falta alguna columna (por ejemplo, porque se agregó en una versión
nueva del esquema), esa columna se agrega al final sin tocar nada de lo
que ya había. Bug real de QA: una versión anterior comparaba CANTIDAD de
columnas y, al agregar Tipo/Unidad a "Resumen por Evento", borró toda una
hoja llena de datos manuales reales de la usuaria porque la cantidad ya
no coincidía.

Hoja "ROI Resultados" (por campaña):
    Mes, Campaña e Inversión total se recalculan en cada corrida (así
    absorbe sola la revisión de los últimos 7 días que hace la
    automatización cada mañana). Nombre de evento, Tipo y Unidad son
    manuales — Sandy los completa a mano — así que esas celdas de una
    fila que ya existía NUNCA se leen ni se reescriben, solo se actualizan
    las columnas automáticas de esa fila (emparejando por "ID de
    campaña", no por posición). Las campañas nuevas se agregan al final,
    con las columnas manuales vacías para que Sandy las complete.

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

    El nombre de evento se compara con los espacios colapsados (ver
    _normalizar_nombre): un espacio de más al cargarlo a mano no debe
    partir un evento en dos filas. Bug real de QA: " Curso X" (con un
    espacio adelante) generó una fila nueva en vez de sumarse a la fila
    ya existente de "Curso X", repartiendo los resultados de un mismo
    evento en dos filas sin que se notara.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from marketing_analytics.reports.roi_builder import autoajustar_columnas, resolver_columnas

ENCABEZADOS = ["Mes", "Campaña", "ID de campaña", "Inversión total", "Nombre de evento", "Tipo", "Unidad"]
FORMATO_MONEDA = '"$"#,##0.00'
FORMATO_PORCENTAJE = "0.0%"

HOJA_CAMPANAS = "ROI Resultados"
HOJA_RESUMEN = "Resumen por Evento"
ENCABEZADOS_RESUMEN = [
    "Nombre de evento", "Tipo", "Unidad", "Inversión total", "Leads", "Subscribers", "Revenue",
    "Costo por lead", "% de conversión", "ROI",
]
SIN_ASIGNAR = "(Sin asignar)"


def _normalizar_nombre(texto: str) -> str:
    """Colapsa espacios para que un espacio de más no cree un evento
    duplicado. Bug real de QA: una campaña con "Nombre de evento" cargado
    con un espacio al principio (" Curso X" en vez de "Curso X") generó
    una fila nueva en "Resumen por Evento" en vez de sumarse a la fila ya
    existente — el evento quedó partido en dos filas sin que se notara."""
    return " ".join(texto.split())


def generar_roi_resultados(ruta_roi_campanas: str | Path, ruta_salida: str | Path) -> Path | None:
    ruta_roi_campanas = Path(ruta_roi_campanas)
    ruta_salida = Path(ruta_salida)

    if not ruta_roi_campanas.exists():
        return None

    campanas = _leer_campanas(ruta_roi_campanas)

    if ruta_salida.exists():
        wb = load_workbook(ruta_salida)
        # Por nombre, NUNCA por "hoja activa" (wb.active): Excel guarda como
        # "activa" la pestaña que estaba seleccionada la última vez que se
        # guardó el archivo a mano. Bug real de QA: si Sandy guardaba el
        # archivo con la pestaña "Resumen por Evento" abierta, wb.active
        # apuntaba a esa hoja en vez de a "ROI Resultados" — la corrida
        # terminaba leyendo y escribiendo en la hoja equivocada: "ROI
        # Resultados" se quedaba congelada con el monto viejo (nunca más se
        # tocaba) y "Resumen por Evento" se llenaba de columnas y filas de
        # campaña que no le correspondían.
        ws = wb[HOJA_CAMPANAS] if HOJA_CAMPANAS in wb.sheetnames else wb.create_sheet(HOJA_CAMPANAS)
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = HOJA_CAMPANAS

    cols = resolver_columnas(ws, ENCABEZADOS)

    fila_por_id: dict[str, int] = {}
    for fila_idx in range(2, ws.max_row + 1):
        id_celda = ws.cell(row=fila_idx, column=cols["ID de campaña"]).value
        if id_celda is not None:
            fila_por_id[id_celda] = fila_idx

    for id_campana, mes, campana, inversion in campanas:
        fila = fila_por_id.get(id_campana)
        if fila is None:
            fila = ws.max_row + 1
            fila_por_id[id_campana] = fila
            ws.cell(row=fila, column=cols["ID de campaña"], value=id_campana)

        # Automáticas: Mes, Campaña, Inversión total. Nombre de evento en
        # adelante (manuales) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=cols["Mes"], value=mes)
        ws.cell(row=fila, column=cols["Campaña"], value=campana)
        celda_inversion = ws.cell(row=fila, column=cols["Inversión total"], value=inversion)
        celda_inversion.number_format = FORMATO_MONEDA

    autoajustar_columnas(ws)
    _actualizar_resumen_por_evento(wb, ws, cols)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _actualizar_resumen_por_evento(wb: Workbook, ws_campanas: Worksheet, cols_campanas: dict[str, int]) -> None:
    col_evento = cols_campanas["Nombre de evento"]
    col_tipo = cols_campanas["Tipo"]
    col_unidad = cols_campanas["Unidad"]
    col_inversion = cols_campanas["Inversión total"]

    datos_por_evento: dict[str, dict] = {}
    for fila in ws_campanas.iter_rows(min_row=2, values_only=True):
        nombre_evento = _normalizar_nombre(fila[col_evento - 1]) if fila[col_evento - 1] else SIN_ASIGNAR
        datos = datos_por_evento.setdefault(nombre_evento, {"inversion": 0.0, "tipo": None, "unidad": None})
        datos["inversion"] += fila[col_inversion - 1] or 0
        if datos["tipo"] is None and fila[col_tipo - 1]:
            datos["tipo"] = fila[col_tipo - 1]
        if datos["unidad"] is None and fila[col_unidad - 1]:
            datos["unidad"] = fila[col_unidad - 1]

    ws = wb[HOJA_RESUMEN] if HOJA_RESUMEN in wb.sheetnames else wb.create_sheet(HOJA_RESUMEN)
    cols = resolver_columnas(ws, ENCABEZADOS_RESUMEN)
    col_r_nombre = cols["Nombre de evento"]
    col_r_leads = cols["Leads"]
    col_r_subscribers = cols["Subscribers"]
    col_r_revenue = cols["Revenue"]

    fila_por_nombre: dict[str, int] = {}
    for fila_idx in range(2, ws.max_row + 1):
        nombre_celda = ws.cell(row=fila_idx, column=col_r_nombre).value
        if nombre_celda is not None:
            fila_por_nombre[_normalizar_nombre(nombre_celda)] = fila_idx

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
            for columna in (col_r_leads, col_r_subscribers, col_r_revenue)
        )
    ]
    for fila in sorted(filas_a_eliminar, reverse=True):
        ws.delete_rows(fila, 1)

    if filas_a_eliminar:
        fila_por_nombre = {}
        for fila_idx in range(2, ws.max_row + 1):
            nombre_celda = ws.cell(row=fila_idx, column=col_r_nombre).value
            if nombre_celda is not None:
                fila_por_nombre[_normalizar_nombre(nombre_celda)] = fila_idx

    # Orden: primero los eventos que ya tenían fila, en el mismo orden en
    # que ya estaban (por fila, no alfabético); los eventos nuevos se
    # agregan al final, en el orden en que aparecen por primera vez entre
    # las campañas (datos_por_evento ya respeta ese orden porque viene de
    # recorrer "ROI Resultados" fila por fila).
    orden_existente = [nombre for nombre, _ in sorted(fila_por_nombre.items(), key=lambda par: par[1])]
    nombres_nuevos = [nombre for nombre in datos_por_evento if nombre not in fila_por_nombre]

    for nombre_evento in orden_existente + nombres_nuevos:
        # Datos de un evento huérfano con datos manuales (no se borró
        # arriba): ya no tiene campañas, así que inversión/tipo/unidad
        # quedan vacíos.
        datos = datos_por_evento.get(nombre_evento, {"inversion": 0.0, "tipo": None, "unidad": None})
        fila = fila_por_nombre.get(nombre_evento)
        if fila is None:
            fila = ws.max_row + 1
            fila_por_nombre[nombre_evento] = fila
            ws.cell(row=fila, column=col_r_nombre, value=nombre_evento)

        # Automáticas: Tipo, Unidad, Inversión total. Leads en adelante
        # (manuales) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=cols["Tipo"], value=datos["tipo"])
        ws.cell(row=fila, column=cols["Unidad"], value=datos["unidad"])
        celda_inversion = ws.cell(row=fila, column=cols["Inversión total"], value=datos["inversion"])
        celda_inversion.number_format = FORMATO_MONEDA
        _escribir_formulas_resumen(ws, fila, cols)

    autoajustar_columnas(ws)


def _escribir_formulas_resumen(ws: Worksheet, fila: int, cols: dict[str, int]) -> None:
    inversion = f"{ws.cell(row=fila, column=cols['Inversión total']).coordinate[:-len(str(fila))]}{fila}"
    leads = f"{ws.cell(row=fila, column=cols['Leads']).coordinate[:-len(str(fila))]}{fila}"
    subscribers = f"{ws.cell(row=fila, column=cols['Subscribers']).coordinate[:-len(str(fila))]}{fila}"
    revenue = f"{ws.cell(row=fila, column=cols['Revenue']).coordinate[:-len(str(fila))]}{fila}"

    celda_costo = ws.cell(row=fila, column=cols["Costo por lead"], value=f'=IFERROR({inversion}/{leads},"")')
    celda_costo.number_format = FORMATO_MONEDA

    celda_conv = ws.cell(
        row=fila, column=cols["% de conversión"], value=f'=IFERROR({subscribers}/{leads},"")'
    )
    celda_conv.number_format = FORMATO_PORCENTAJE

    celda_roi = ws.cell(
        row=fila, column=cols["ROI"], value=f'=IFERROR(({revenue}-{inversion})/{inversion},"")'
    )
    celda_roi.number_format = FORMATO_PORCENTAJE


def _leer_campanas(ruta_roi_campanas: Path) -> list[tuple[str, str, str, float]]:
    wb = load_workbook(ruta_roi_campanas, data_only=True)
    # Por nombre, no por "hoja activa" (ver el comentario en
    # generar_roi_resultados): ROI_Campanas.xlsx solo tiene una hoja real,
    # pero wb.active puede apuntar a otra cosa si el archivo se guardó con
    # otra pestaña seleccionada.
    ws = wb["ROI Campañas"] if "ROI Campañas" in wb.sheetnames else wb.worksheets[0]
    cols = resolver_columnas(ws, ["Mes", "Campaña", "ID de campaña", "Inversión total"])
    campanas = []
    for fila_idx in range(2, ws.max_row + 1):
        id_campana = ws.cell(row=fila_idx, column=cols["ID de campaña"]).value
        if id_campana is None:
            continue
        mes = ws.cell(row=fila_idx, column=cols["Mes"]).value
        campana = ws.cell(row=fila_idx, column=cols["Campaña"]).value
        inversion = ws.cell(row=fila_idx, column=cols["Inversión total"]).value or 0
        campanas.append((id_campana, mes, campana, inversion))
    return campanas
