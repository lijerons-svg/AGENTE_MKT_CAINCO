"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su mes,
nombre, ID e inversión total (sumada a lo largo de toda la campaña, todas
las redes y todos los días), más columnas de carga manual para hacer
seguimiento comercial de cada campaña.

Mes, Campaña, ID de campaña e Inversión total son automáticos y se
recalculan en cada corrida. Unidad, Tipo de campaña, Nombre_Producto,
Leads, Inscritos y Venta total USD son manuales — Sandy los completa a
mano — así que si el archivo ya existe se abre y se edita EN SITIO: esas
celdas de una fila que ya existía NUNCA se leen ni se reescriben, solo se
actualizan las columnas automáticas de esa fila (emparejando por "ID de
campaña", no por posición). Las campañas nuevas se agregan al final, con
las columnas manuales vacías para que Sandy las complete.

Si el archivo existente tiene una cantidad de columnas distinta a la
esperada (por ejemplo, de una versión anterior del esquema), se
reconstruye desde cero en vez de editarlo en sitio — evita que el
matcheo por ID busque en la columna equivocada y duplique todo.

Además arma una segunda hoja, "Resumen por Producto": agrupa por
Nombre_Producto (varias campañas pueden ser el mismo producto/evento) y
suma la Inversión total automáticamente, así absorbe sola la revisión de
los últimos 7 días que hace la automatización cada mañana. Ahí Leads,
Inscritos y Venta total USD también son manuales, protegidas por
Nombre_Producto (no por posición).

El "Mes" es el de la fecha de inicio real de la campaña en Meta
(fecha_inicio_campana); si esa fecha no está disponible (campañas cargadas
antes de que el conector empezara a capturarla), se usa el mes de la
publicación de insights más antigua como respaldo.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

_ENCABEZADOS = [
    "Mes",
    "Campaña",
    "ID de campaña",
    "Inversión total",
    "Unidad",
    "Tipo de campaña",
    "Nombre_Producto",
    "Leads",
    "Inscritos",
    "Venta total USD",
]
_COL_MES = 1
_COL_CAMPANA = 2
_COL_ID_CAMPANA = 3
_COL_INVERSION = 4
_COL_UNIDAD = 5
_COL_TIPO = 6
_COL_NOMBRE_PRODUCTO = 7
_FORMATO_MONEDA = '"$"#,##0.00'
_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

_HOJA_RESUMEN = "Resumen por Producto"
_ENCABEZADOS_RESUMEN = [
    "Nombre_Producto", "Unidad", "Tipo de campaña", "Inversión total",
    "Leads", "Inscritos", "Venta total USD",
]
_COL_R_NOMBRE = 1
_COL_R_UNIDAD = 2
_COL_R_TIPO = 3
_COL_R_INVERSION = 4
_COL_R_LEADS = 5
_COL_R_INSCRITOS = 6
_COL_R_VENTA = 7
_SIN_ASIGNAR = "(Sin asignar)"


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

    wb = load_workbook(ruta_salida) if ruta_salida.exists() else None
    ws = wb.active if wb is not None else None

    if ws is None or not _tiene_columnas_esperadas(ws, _ENCABEZADOS):
        wb = Workbook()
        ws = wb.active
        ws.title = "ROI Campañas"
        ws.append(_ENCABEZADOS)
        for celda in ws[1]:
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

        # Automáticas: Mes, Campaña, Inversión total. Las columnas manuales
        # (Unidad en adelante) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=_COL_MES, value=_mes_legible(campana["mes_referencia"]))
        ws.cell(row=fila, column=_COL_CAMPANA, value=campana["campana"])
        celda_inversion = ws.cell(row=fila, column=_COL_INVERSION, value=campana["inversion_total"])
        celda_inversion.number_format = _FORMATO_MONEDA

    _autoajustar_columnas(ws)
    _actualizar_resumen_por_producto(wb, ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _actualizar_resumen_por_producto(wb: Workbook, ws_campanas: Worksheet) -> None:
    """Agrupa la hoja de campañas por Nombre_Producto, sumando la
    inversión (así absorbe sola la revisión de los últimos 7 días que hace
    la automatización cada mañana). Leads/Inscritos/Venta total USD son
    manuales y se preservan igual que en la hoja de campañas: emparejadas
    por Nombre_Producto, nunca por posición. Las campañas sin producto
    asignado todavía se agrupan bajo "(Sin asignar)" para no perderlas de
    vista."""
    agregados: dict[str, dict] = {}
    for fila in ws_campanas.iter_rows(min_row=2, values_only=True):
        inversion = fila[_COL_INVERSION - 1] or 0
        unidad = fila[_COL_UNIDAD - 1]
        tipo = fila[_COL_TIPO - 1]
        nombre_producto = fila[_COL_NOMBRE_PRODUCTO - 1] or _SIN_ASIGNAR

        datos = agregados.setdefault(nombre_producto, {"inversion": 0.0, "unidad": None, "tipo": None})
        datos["inversion"] += inversion
        if datos["unidad"] is None and unidad:
            datos["unidad"] = unidad
        if datos["tipo"] is None and tipo:
            datos["tipo"] = tipo

    ws = wb[_HOJA_RESUMEN] if _HOJA_RESUMEN in wb.sheetnames else None
    if ws is not None and not _tiene_columnas_esperadas(ws, _ENCABEZADOS_RESUMEN):
        del wb[_HOJA_RESUMEN]
        ws = None
    if ws is None:
        ws = wb.create_sheet(_HOJA_RESUMEN)
        ws.append(_ENCABEZADOS_RESUMEN)
        for celda in ws[1]:
            celda.font = Font(bold=True)

    fila_por_nombre: dict[str, int] = {}
    for fila_celdas in ws.iter_rows(min_row=2):
        nombre_celda = fila_celdas[_COL_R_NOMBRE - 1].value
        if nombre_celda is not None:
            fila_por_nombre[nombre_celda] = fila_celdas[0].row

    # Incluye también las filas que ya existían pero cuyo nombre de
    # producto ya no tiene campañas (por ejemplo, porque Sandy reasignó
    # todas sus campañas a otro producto) — si no, esa fila queda con el
    # monto de inversión viejo para siempre, como un fantasma. Si además
    # no tiene ningún dato manual cargado, directamente se borra.
    claves = sorted(set(agregados) | set(fila_por_nombre), key=str)
    filas_a_eliminar: list[int] = []
    for nombre_producto in claves:
        datos = agregados.get(nombre_producto)
        fila = fila_por_nombre.get(nombre_producto)

        if datos is None:
            tiene_datos_manuales = any(
                ws.cell(row=fila, column=columna).value is not None
                for columna in (_COL_R_LEADS, _COL_R_INSCRITOS, _COL_R_VENTA)
            )
            if not tiene_datos_manuales:
                filas_a_eliminar.append(fila)
                continue
            datos = {"inversion": 0.0, "unidad": None, "tipo": None}

        if fila is None:
            fila = ws.max_row + 1
            fila_por_nombre[nombre_producto] = fila
            ws.cell(row=fila, column=_COL_R_NOMBRE, value=nombre_producto)

        # Automáticas: Unidad, Tipo de campaña, Inversión total. Leads en
        # adelante (manuales) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=_COL_R_UNIDAD, value=datos["unidad"])
        ws.cell(row=fila, column=_COL_R_TIPO, value=datos["tipo"])
        celda_inversion = ws.cell(row=fila, column=_COL_R_INVERSION, value=datos["inversion"])
        celda_inversion.number_format = _FORMATO_MONEDA

    for fila in sorted(filas_a_eliminar, reverse=True):
        ws.delete_rows(fila, 1)

    _autoajustar_columnas(ws)


def _tiene_columnas_esperadas(ws: Worksheet, encabezados_esperados: list[str]) -> bool:
    # Compara por CANTIDAD de encabezados, no por texto — Sandy puede
    # renombrar columnas y eso no debe disparar una reconstrucción. Lo que
    # importa es si tiene la misma cantidad de columnas que el esquema
    # actual; si tiene menos, alguna columna clave ya no está en la
    # posición que este código espera.
    encabezados_con_valor = sum(1 for celda in ws[1] if celda.value is not None)
    return encabezados_con_valor == len(encabezados_esperados)


def _mes_legible(fecha_texto: str | None) -> str:
    if not fecha_texto:
        return ""
    anio, mes, *_ = fecha_texto.split("-")
    return f"{_MESES[int(mes) - 1]} {anio}"


def _autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
