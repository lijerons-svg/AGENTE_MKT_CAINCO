"""Genera Historico_RRSS.xlsx con las 7 hojas requeridas: META ORGANICO,
CONTROL PERFILES, META ADS, MAILCHIMP, CALENDARIO, LINKEDIN, LOG. Siempre
leyendo desde la base histórica (SQLite) — el Excel es un reporte, nunca la
fuente de verdad.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from openpyxl import Workbook

from marketing_analytics.reports.sheets import (
    agregar_hoja_calendario,
    agregar_hoja_control_perfiles,
    agregar_hoja_linkedin,
    agregar_hoja_log,
    agregar_hoja_mailchimp,
    agregar_hoja_meta_ads,
    agregar_hoja_meta_organico,
)

if TYPE_CHECKING:
    from marketing_analytics.config.schema import AppConfig


def generar_historico_excel(
    conn: sqlite3.Connection, ruta_salida: str | Path, config: "AppConfig | None" = None
) -> Path:
    wb = Workbook()
    wb.remove(wb.active)  # quitar la hoja "Sheet" por defecto

    agregar_hoja_meta_organico(wb, conn)
    agregar_hoja_control_perfiles(wb, conn)
    agregar_hoja_meta_ads(wb, conn, config)
    agregar_hoja_mailchimp(wb, conn)
    agregar_hoja_calendario(wb, conn)
    agregar_hoja_linkedin(wb, conn)
    agregar_hoja_log(wb, conn)

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta_salida)
    return ruta_salida
