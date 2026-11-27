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
from dataclasses import dataclass, field

from marketing_analytics.config.schema import GA4Config
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.ga4.client import GA4Client
from marketing_analytics.connectors.ga4.mapper import mapear_fila, mapear_fila_pagina
from marketing_analytics.database.repository import (
    ResultadoUpsert,
    upsert_ga4_metricas_diarias,
    upsert_ga4_metricas_paginas,
)
from marketing_analytics.models.records import GA4MetricaDiaria, GA4MetricaPagina

logger = logging.getLogger(__name__)


@dataclass
class GA4FetchResult:
    metricas_diarias: list[GA4MetricaDiaria] = field(default_factory=list)
    metricas_paginas: list[GA4MetricaPagina] = field(default_factory=list)


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

    def fetch(self, desde: datetime.date, hasta: datetime.date) -> GA4FetchResult:
        resultado = GA4FetchResult()
        fallidas: list[str] = []

        for propiedad in self._config.propiedades:
            try:
                filas_diarias = self._client.obtener_metricas_diarias(
                    propiedad.property_id, desde, hasta
                )
                resultado.metricas_diarias.extend(
                    mapear_fila(propiedad, fila) for fila in filas_diarias
                )

                filas_paginas = self._client.obtener_metricas_por_pagina(
                    propiedad.property_id, desde, hasta
                )
                resultado.metricas_paginas.extend(
                    mapear_fila_pagina(propiedad, fila) for fila in filas_paginas
                )
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

        return resultado

    def upsert(self, conn: sqlite3.Connection, datos: GA4FetchResult) -> ResultadoUpsert:
        resultado = upsert_ga4_metricas_diarias(conn, datos.metricas_diarias)
        resultado += upsert_ga4_metricas_paginas(conn, datos.metricas_paginas)
        return resultado
