"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su mes,
nombre, ID e inversión total (sumada a lo largo de toda la campaña, todas
las redes y todos los días), más Unidad/Tipo de campaña/Nombre_Producto
para que Sandy asigne a mano a qué evento o producto pertenece cada
campaña (varias campañas pueden ser el mismo producto/evento).

El seguimiento comercial (Leads, Resultados, ROI) vive en un archivo
separado, ROI_Resultados.xlsx (ver roi_resultados_builder.py), que lee
este archivo pero nunca lo modifica — así una corrida de uno no puede
"chocar" con el otro.

Mes, Campaña, ID de campaña e Inversión total son automáticos y se
recalculan en cada corrida. Unidad, Tipo de campaña y Nombre_Producto son
manuales — Sandy los completa a mano — así que si el archivo ya existe se
abre y se edita EN SITIO: esas celdas de una fila que ya existía NUNCA se
leen ni se reescriben, solo se actualizan las columnas automáticas de esa
fila (emparejando por "ID de campaña", no por posición). Las campañas
nuevas se agregan al final, con las columnas manuales vacías para que
Sandy las complete.

Las columnas se ubican por su TEXTO de encabezado (fila 1), nunca por una
posición fija. Si el archivo ya existe y le falta alguna columna (por
ejemplo, porque se agregó en una versión nueva del esquema), esa columna
se agrega al final sin tocar nada de lo que ya había — nunca se reconstruye
ni se borra una hoja completa por un cambio de esquema. Bug real de QA:
una versión anterior comparaba CANTIDAD de columnas y, ante cualquier
diferencia, reconstruía la hoja entera desde cero — eso borró datos
manuales reales de una usuaria cuando se agregó una columna nueva.

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

    if ruta_salida.exists():
        wb = load_workbook(ruta_salida)
        # Por nombre, no por "hoja activa" (wb.active): esa es la pestaña
        # que estaba seleccionada la última vez que Excel guardó el
        # archivo, no necesariamente la hoja de datos. Bug real de QA en
        # ROI_Resultados.xlsx (que sí tiene más de una hoja): confiar en
        # wb.active hacía que una corrida leyera/escribiera la hoja
        # equivocada apenas la usuaria guardaba con otra pestaña abierta.
        ws = wb["ROI Campañas"] if "ROI Campañas" in wb.sheetnames else wb.worksheets[0]
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "ROI Campañas"

    cols = resolver_columnas(ws, ENCABEZADOS)

    fila_por_id: dict[str, int] = {}
    for fila_idx in range(2, ws.max_row + 1):
        id_celda = ws.cell(row=fila_idx, column=cols["ID de campaña"]).value
        if id_celda is not None:
            fila_por_id[id_celda] = fila_idx

    for campana in campanas:
        id_campana = campana["id_campana_origen"]
        fila = fila_por_id.get(id_campana)
        if fila is None:
            fila = ws.max_row + 1
            fila_por_id[id_campana] = fila
            ws.cell(row=fila, column=cols["ID de campaña"], value=id_campana)

        # Automáticas: Mes, Campaña, Inversión total. Las columnas manuales
        # (Unidad en adelante) jamás se leen ni se escriben acá.
        ws.cell(row=fila, column=cols["Mes"], value=_mes_legible(campana["mes_referencia"]))
        ws.cell(row=fila, column=cols["Campaña"], value=campana["campana"])
        celda_inversion = ws.cell(row=fila, column=cols["Inversión total"], value=campana["inversion_total"])
        celda_inversion.number_format = FORMATO_MONEDA

    autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def resolver_columnas(ws: Worksheet, encabezados_requeridos: list[str]) -> dict[str, int]:
    """Devuelve {texto_de_encabezado: columna} buscando en la fila 1 por
    TEXTO, no por posición fija. Cualquier encabezado de
    `encabezados_requeridos` que todavía no exista en la hoja (por
    ejemplo, una columna agregada en una versión nueva del esquema) se
    crea al final — nunca se borra ni se reconstruye nada de lo que ya
    había. Si Sandy renombra una columna existente (de las que no están en
    `encabezados_requeridos`, como una manual), esa columna no se toca."""
    columnas: dict[str, int] = {}
    for celda in ws[1]:
        if celda.value is not None:
            columnas[celda.value] = celda.column
    for nombre in encabezados_requeridos:
        if nombre not in columnas:
            nueva_columna = (max(columnas.values()) if columnas else 0) + 1
            celda = ws.cell(row=1, column=nueva_columna, value=nombre)
            celda.font = Font(bold=True)
            columnas[nombre] = nueva_columna
    return columnas


def _mes_legible(fecha_texto: str | None) -> str:
    if not fecha_texto:
        return ""
    anio, mes, *_ = fecha_texto.split("-")
    return f"{_MESES[int(mes) - 1]} {anio}"


def autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
