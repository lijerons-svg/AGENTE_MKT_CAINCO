"""Conector Mailchimp: implementa BaseConnector combinando campañas + enlaces
wa.me en un único fetch/upsert."""
from __future__ import annotations

import datetime
import sqlite3
from dataclasses import dataclass, field

from marketing_analytics.config.schema import MailchimpConfig
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.mailchimp.client import MailchimpClient
from marketing_analytics.connectors.mailchimp.mapper import (
    mapear_campana,
    mapear_enlaces_whatsapp,
)
from marketing_analytics.database.repository import (
    ResultadoUpsert,
    upsert_mailchimp_campanas,
    upsert_mailchimp_enlaces_whatsapp,
)
from marketing_analytics.models.records import MailchimpCampana, MailchimpEnlaceWhatsapp


@dataclass
class MailchimpFetchResult:
    campanas: list[MailchimpCampana] = field(default_factory=list)
    enlaces_whatsapp: list[MailchimpEnlaceWhatsapp] = field(default_factory=list)


class MailchimpConnector(BaseConnector):
    nombre = "mailchimp"

    def __init__(self, config: MailchimpConfig, api_key: str, cliente: MailchimpClient | None = None):
        self._config = config
        self._client = cliente or MailchimpClient(api_key, config.server_prefix)

    def fetch(self, desde: datetime.date, hasta: datetime.date) -> MailchimpFetchResult:
        resultado = MailchimpFetchResult()
        for resumen in self._client.listar_campanas_enviadas(desde, hasta):
            campaign_id = resumen["id"]
            reporte = self._client.obtener_reporte(campaign_id)
            resultado.campanas.append(mapear_campana(resumen, reporte))

            detalle_clics = self._client.obtener_detalle_clics(campaign_id)
            resultado.enlaces_whatsapp.extend(
                mapear_enlaces_whatsapp(campaign_id, detalle_clics)
            )
        return resultado

    def upsert(self, conn: sqlite3.Connection, datos: MailchimpFetchResult) -> ResultadoUpsert:
        resultado = upsert_mailchimp_campanas(conn, datos.campanas)
        resultado += upsert_mailchimp_enlaces_whatsapp(conn, datos.enlaces_whatsapp)
        return resultado
