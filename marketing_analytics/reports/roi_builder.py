"""Genera ROI_Campanas.xlsx: una fila por campaña de Meta Ads con su mes,
unidad, nombre, ID e inversión total (sumada a lo largo de toda la
campaña, todas las redes y todos los días).

Mes, Unidad, Campaña, ID de campaña e Inversión total son automáticos y se
recalculan en cada corrida. "Nombre_Producto" es manual — Sandy asigna a
mano a qué producto pertenece cada campaña (varias campañas pueden ser el
mismo producto/evento) — así que el archivo se abre y se edita EN SITIO si
ya existe: la celda de Nombre_Producto de una fila que ya existía nunca se
lee ni se reescribe, solo se actualizan las columnas automáticas de esa
fila. Las campañas nuevas se agregan al final, con Nombre_Producto vacío
para que Sandy lo complete.

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

_ENCABEZADOS = ["Mes", "Unidad", "Campaña", "ID de campaña", "Nombre_Producto", "Inversión total"]
_COL_MES = 1
_COL_UNIDAD = 2
_COL_CAMPANA = 3
_COL_ID_CAMPANA = 4
_COL_INVERSION = 6
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
            perfil_unidad,
            SUM(importe_gastado) AS inversion_total,
            COALESCE(MIN(fecha_inicio_campana), MIN(fecha_publicacion)) AS mes_referencia
        FROM meta_ads
        GROUP BY id_campana_origen
        ORDER BY mes_referencia, campana
        """
    ).fetchall()

    wb = load_workbook(ruta_salida) if ruta_salida.exists() else None
    ws = wb.active if wb is not None else None

    if ws is None or not _tiene_columnas_esperadas(ws):
        # Archivo nuevo, o de una versión anterior cuyas columnas no
        # coinciden con el esquema actual (por ejemplo, antes de agregar
        # Unidad/Nombre_Producto). Si siguiéramos editándolo en sitio, el
        # matcheo por ID buscaría en la columna equivocada y duplicaría
        # todo — más seguro reconstruirlo de cero. No hay nada manual que
        # perder: Nombre_Producto es la única columna manual y, si el
        # archivo tiene un esquema viejo, es porque esa columna todavía no
        # existía.
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

        # Automáticas: Mes, Unidad, Campaña, Inversión total. Nombre_Producto
        # (manual) jamás se lee ni se escribe acá.
        ws.cell(row=fila, column=_COL_MES, value=_mes_legible(campana["mes_referencia"]))
        ws.cell(row=fila, column=_COL_UNIDAD, value=campana["perfil_unidad"])
        ws.cell(row=fila, column=_COL_CAMPANA, value=campana["campana"])
        celda_inversion = ws.cell(row=fila, column=_COL_INVERSION, value=campana["inversion_total"])
        celda_inversion.number_format = _FORMATO_MONEDA

    _autoajustar_columnas(ws)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida


def _tiene_columnas_esperadas(ws: Worksheet) -> bool:
    # Compara por CANTIDAD de encabezados, no por texto — Sandy puede
    # renombrar columnas (por ejemplo "Nombre_Producto" a "Producto") y eso
    # no debe disparar una reconstrucción. Lo que sí importa es si el
    # archivo tiene la misma cantidad de columnas que el esquema actual;
    # si tiene menos (por ejemplo, de antes de agregar Unidad), el ID de
    # campaña ya no está en la posición que este código espera.
    encabezados_con_valor = sum(1 for celda in ws[1] if celda.value is not None)
    return encabezados_con_valor == len(_ENCABEZADOS)


def _mes_legible(fecha_texto: str | None) -> str:
    if not fecha_texto:
        return ""
    anio, mes, *_ = fecha_texto.split("-")
    return f"{_MESES[int(mes) - 1]} {anio}"


def _autoajustar_columnas(ws: Worksheet) -> None:
    for columna in ws.columns:
        longitud = max((len(str(c.value)) for c in columna if c.value is not None), default=10)
        ws.column_dimensions[columna[0].column_letter].width = min(longitud + 2, 60)
