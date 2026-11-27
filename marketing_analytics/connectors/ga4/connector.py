"""Conector Google Analytics 4: recorre TODAS las propiedades de
config.yaml (una por unidad, ver GA4Config) sin ningún cambio de código al
agregar una nueva.

Mismo criterio de tolerancia a fallos que Meta Orgánico: una propiedad con
un ID mal tipeado o sin acceso concedido a la cuenta de servicio no debe
tumbar a las demás — se procesan todas, se loguea claro cuál falló y por
qué, y se guarda igual lo que sí funcionó. Solo si TODAS fallan se
considera la corrida del conector como fallida.
"""
from __future__ import annotations

import datetime
import logging
import sqlite3

from marketing_analytics.config.schema import GA4Config
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.ga4.client import GA4Client
from marketing_analytics.connectors.ga4.mapper import mapear_fila
from marketing_analytics.database.repository import ResultadoUpsert, upsert_ga4_metricas_diarias
from marketing_analytics.models.records import GA4MetricaDiaria

logger = logging.getLogger(__name__)


class GA4Connector(BaseConnector):
    nombre = "ga4"

    def __init__(
        self,
        config: GA4Config,
        ruta_credenciales: str,
        cliente: GA4Client | None = None,
    ):
        self._config = config
        self._client = cliente or GA4Client(ruta_credenciales)

    def fetch(self, desde: datetime.date, hasta: datetime.date) -> list[GA4MetricaDiaria]:
        registros: list[GA4MetricaDiaria] = []
        fallidas: list[str] = []

        for propiedad in self._config.propiedades:
            try:
                filas = self._client.obtener_metricas_diarias(propiedad.property_id, desde, hasta)
                registros.extend(mapear_fila(propiedad, fila) for fila in filas)
            except Exception as error:
                logger.warning(
                    "Propiedad GA4 '%s' (%s) falló, se sigue con el resto: %s",
                    propiedad.unidad, propiedad.property_id, error,
                )
                fallidas.append(f"{propiedad.unidad} ({propiedad.property_id}): {error}")

        if fallidas:
            resumen = "; ".join(fallidas)
            if len(fallidas) == len(self._config.propiedades):
                raise RuntimeError(f"Todas las propiedades de GA4 fallaron: {resumen}")
            logger.warning(
                "%d de %d propiedades de GA4 fallaron (se guardó el resto): %s",
                len(fallidas), len(self._config.propiedades), resumen,
            )

        return registros

    def upsert(self, conn: sqlite3.Connection, datos: list[GA4MetricaDiaria]) -> ResultadoUpsert:
        return upsert_ga4_metricas_diarias(conn, datos)
