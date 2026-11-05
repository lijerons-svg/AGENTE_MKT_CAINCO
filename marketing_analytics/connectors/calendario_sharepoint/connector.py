"""Conector del calendario de publicaciones (SharePoint): a diferencia de los
demás conectores, no es un feed histórico incremental — es una planificación
completa que el equipo edita libremente (fechas, estado, notas). Por eso
`fetch` ignora `desde`/`hasta` a propósito y siempre trae la hoja entera; el
dedupe por `uid` (basado en el ID propio de cada fila, ver models/records.py)
se encarga de que reprogramar o editar una fila actualice el registro
existente en vez de duplicarlo.
"""
from __future__ import annotations

import datetime
import sqlite3

from marketing_analytics.config.schema import CalendarioConfig
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.calendario_sharepoint.client import (
    CalendarioSharePointClient,
)
from marketing_analytics.connectors.calendario_sharepoint.mapper import mapear_fila
from marketing_analytics.database.repository import ResultadoUpsert, upsert_calendario_publicaciones
from marketing_analytics.models.records import CalendarioPublicacion


class CalendarioSharePointConnector(BaseConnector):
    nombre = "calendario_sharepoint"

    def __init__(
        self,
        config: CalendarioConfig,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        cliente: CalendarioSharePointClient | None = None,
    ):
        self._client = cliente or CalendarioSharePointClient(
            tenant_id,
            client_id,
            client_secret,
            config.sharepoint_hostname,
            config.site_path,
            config.file_name,
            config.sheet_name,
        )

    def fetch(
        self, desde: datetime.date, hasta: datetime.date
    ) -> list[CalendarioPublicacion]:
        filas = self._client.obtener_filas_calendario()
        return [mapear_fila(f) for f in filas]

    def upsert(
        self, conn: sqlite3.Connection, datos: list[CalendarioPublicacion]
    ) -> ResultadoUpsert:
        return upsert_calendario_publicaciones(conn, datos)
