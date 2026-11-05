"""Conector Meta Ads: implementa BaseConnector sobre la Marketing API oficial."""
from __future__ import annotations

import calendar
import datetime
import sqlite3

from marketing_analytics.config.schema import MetaAdsConfig
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.meta_ads.client import MetaAdsClient
from marketing_analytics.connectors.meta_ads.mapper import mapear_insights
from marketing_analytics.database.repository import ResultadoUpsert, upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro


def _dividir_por_mes(
    desde: datetime.date, hasta: datetime.date
) -> list[tuple[datetime.date, datetime.date]]:
    """Un backfill de varios meses pedido de un tirón topa el límite de
    peticiones de Meta más rápido que el mismo total partido en tramos: en
    un caso real, 9 meses de una sola vez falló entero y hubo que pedirlo a
    mano en trimestres. Se parte siempre por mes calendario para que nadie
    tenga que acordarse de hacerlo manualmente."""
    tramos: list[tuple[datetime.date, datetime.date]] = []
    inicio_mes = desde.replace(day=1)
    while inicio_mes <= hasta:
        ultimo_dia = calendar.monthrange(inicio_mes.year, inicio_mes.month)[1]
        fin_mes = inicio_mes.replace(day=ultimo_dia)
        tramos.append((max(inicio_mes, desde), min(fin_mes, hasta)))
        inicio_mes = fin_mes + datetime.timedelta(days=1)
    return tramos


class MetaAdsConnector(BaseConnector):
    nombre = "meta_ads"

    def __init__(
        self,
        config: MetaAdsConfig,
        access_token: str,
        api_version: str,
        cliente: MetaAdsClient | None = None,
    ):
        self._config = config
        self._client = cliente or MetaAdsClient(access_token, api_version)

    def fetch(self, desde: datetime.date, hasta: datetime.date) -> list[MetaAdsRegistro]:
        registros: list[MetaAdsRegistro] = []
        for cuenta in self._config.cuentas:
            objetivos = self._client.obtener_objetivos_campanas(cuenta.id)
            fechas_campanas = self._client.obtener_fechas_campanas(cuenta.id)
            filas: list[dict] = []
            for ini, fin in _dividir_por_mes(desde, hasta):
                filas.extend(self._client.obtener_insights_campana(cuenta.id, ini, fin))
            # Una consulta extra por campaña (no por fila/día) para resolver
            # de qué página es el post que promociona, cuando la campaña es
            # un "boost" directo — ver MetaAdsRegistro.pagina_origen_id.
            paginas_por_campana: dict[str, str] = {}
            for fila in filas:
                campaign_id = fila["campaign_id"]
                if campaign_id not in paginas_por_campana:
                    paginas_por_campana[campaign_id] = self._client.obtener_pagina_origen_campana(campaign_id)
            registros.extend(mapear_insights(cuenta, filas, objetivos, paginas_por_campana, fechas_campanas))
        return registros

    def upsert(self, conn: sqlite3.Connection, datos: list[MetaAdsRegistro]) -> ResultadoUpsert:
        return upsert_meta_ads(conn, datos)
