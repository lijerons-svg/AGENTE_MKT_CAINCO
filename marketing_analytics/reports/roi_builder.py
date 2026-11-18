"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su mes,
nombre, ID e inversión total (sumada a lo largo de toda la campaña, todas
las redes y todos los días), más Unidad/Tipo de campaña/Nombre_Producto
para que Sandy asigne a mano a qué evento o producto pertenece cada
campaña (varias campañas pueden ser el mismo producto/evento).

El seguimiento comercial (Leads, Resultados, ROI) vive en un archivo
separado, ROI_Resultados.xlsx (ver resultados_producto_builder.py), que
lee este archivo pero nunca lo modifica — así una corrida de uno no puede
"chocar" con el otro.

Mes, Campaña, ID de campaña e Inversión total son automáticos y se
recalculan en cada corrida. Unidad, Tipo de campaña y Nombre_Producto son
manuales — Sandy los completa a mano — así que si el archivo ya existe se
abre y se edita EN SITIO: esas celdas de una fila que ya existía NUNCA se
leen ni se reescriben, solo se actualizan las columnas automáticas de esa
fila (emparejando por "ID de campaña", no por posición). Las campañas
nuevas se agregan al final, con las columnas manuales vacías para que
Sandy las complete.

Si el archivo existente tiene una cantidad de columnas distinta a la
esperada (por ejemplo, de una versión anterior del esquema), se
reconstruye desde cero en vez de editarlo en sitio — evita que el
matcheo por ID busque en la columna equivocada y duplique todo.

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

ENCABEZADOS = [
    "Mes",
    "Campaña",
    "ID de campaña",
    "Inversión total",
    "Unidad",
    "Tipo de campaña",
    "Nombre_Producto",
]
COL_MES = 1
COL_CAMPANA = 2
COL_ID_CAMPANA = 3
COL_INVERSION = 4
COL_UNIDAD = 5
COL_TIPO = 6
COL_NOMBRE_PRODUCTO = 7
FORMATO_MONEDA = '"$"#,##0.00'
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

    wb = load_workbook(ruta_salida) if ruta_salida.exists() else None
    ws = wb.active if wb is not None else None

    if ws is None or not tiene_columnas_esperadas(ws, ENCABEZADOS):
        wb = Workbook()
        ws = wb.active
        ws.title = "ROI Campañas"
        ws.append(ENCABEZADOS)
        for celda in ws[1]:
            celda.font = Font(bold=True)

    fila_por_id: dict[str, int] = {}
    for fila_celdas in ws.iter_rows(min_row=2):
        id_celda = fila_celdas[COL_ID_CAMPANA - 1].value
        if id_celda is not None:
            fila_por_id[id_celda] = fila_celdas[0].row

    for campana in campanas:
        id_campana = campana["id_campana_origen"]
        fila = fila_por_id.get(id_campana)
        if fila is None:
            fila = ws.max_row + 1
            fila_por_id[id_campana] = fila
            ws.cell(row=fila, column=COL_ID_CAMPANA, value=id_campana)

        # Automáticas: Mes, Campaña, Inversión total. Las columnas manuales
        # (Unidad en adelante) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=COL_MES, value=_mes_legible(campana["mes_referencia"]))
        ws.cell(row=fila, column=COL_CAMPANA, value=campana["campana"])
        celda_inversion = ws.cell(row=fila, column=COL_INVERSION, value=campana["inversion_total"])
        celda_inversion.number_format = FORMATO_MONEDA

    autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def tiene_columnas_esperadas(ws: Worksheet, encabezados_esperados: list[str]) -> bool:
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


def autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
