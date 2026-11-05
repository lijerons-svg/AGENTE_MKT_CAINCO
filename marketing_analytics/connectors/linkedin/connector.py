"""Conector LinkedIn Orgánico: publicaciones y sus métricas de la página de
la organización configurada.

A diferencia de Meta Orgánico (una lista de perfiles), acá hay una sola
organización — la Community Management API autoriza de a una por vez, vía
OAuth a mano de una persona admin de esa página (ver obtener_token.py).

Un post cuyas estadísticas fallen no debe tumbar a los demás — mismo
criterio que meta_organico/connector.py: se seguir con el resto y se
loguea cuál falló."""
from __future__ import annotations

import datetime
import logging
import sqlite3

from marketing_analytics.config.schema import LinkedInConfig
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.linkedin.client import LinkedInClient
from marketing_analytics.connectors.linkedin.mapper import mapear_post
from marketing_analytics.database.repository import ResultadoUpsert, upsert_linkedin_organico
from marketing_analytics.models.records import LinkedInOrganicoPost

logger = logging.getLogger(__name__)


class LinkedInConnector(BaseConnector):
    nombre = "linkedin"

    def __init__(self, config: LinkedInConfig, access_token: str, cliente: LinkedInClient | None = None):
        self._config = config
        self._client = cliente or LinkedInClient(access_token)

    def fetch(self, desde: datetime.date, hasta: datetime.date) -> list[LinkedInOrganicoPost]:
        pagina = self._config.nombre or self._config.organization_id
        posts = self._client.obtener_posts(self._config.organization_id, desde, hasta)

        registros: list[LinkedInOrganicoPost] = []
        fallidos: list[str] = []
        for post in posts:
            post_id = post.get("id", "")
            try:
                estadisticas = self._client.obtener_estadisticas_post(self._config.organization_id, post_id)
                registros.append(mapear_post(pagina, post, estadisticas))
            except Exception as error:
                logger.warning("Post '%s' falló, se sigue con el resto: %s", post_id, error)
                fallidos.append(f"{post_id}: {error}")

        if fallidos and len(fallidos) == len(posts):
            raise RuntimeError(f"Todos los posts de LinkedIn fallaron: {'; '.join(fallidos)}")

        return registros

    def upsert(self, conn: sqlite3.Connection, datos: list[LinkedInOrganicoPost]) -> ResultadoUpsert:
        return upsert_linkedin_organico(conn, datos)
