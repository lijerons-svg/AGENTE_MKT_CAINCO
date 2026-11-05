"""Conector Meta Orgánico: recorre TODOS los perfiles de config.yaml (13 hoy,
los que sean mañana) sin ningún cambio de código al agregar uno nuevo.

Un perfil con un ID mal tipeado o un permiso faltante NO debe tumbar a los
demás: se procesan todos, se loguea claro cuál falló y por qué, y se
guarda igual lo que sí funcionó. Solo si TODOS los perfiles fallan se
considera la corrida del conector como fallida (para que el orquestador
lo marque como error real, no como éxito silencioso con cero datos).
"""
from __future__ import annotations

import datetime
import logging
import sqlite3

from marketing_analytics.config.schema import MetaOrganicoConfig, PerfilMetaOrganico, Red
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.meta_organico.client import MetaOrganicoClient
from marketing_analytics.connectors.meta_organico.mapper import (
    mapear_media_instagram,
    mapear_post_facebook,
)
from marketing_analytics.database.repository import ResultadoUpsert, upsert_meta_organico
from marketing_analytics.models.records import MetaOrganicoPost

logger = logging.getLogger(__name__)


class MetaOrganicoConnector(BaseConnector):
    nombre = "meta_organico"

    def __init__(
        self,
        config: MetaOrganicoConfig,
        access_token: str,
        api_version: str,
        cliente: MetaOrganicoClient | None = None,
    ):
        self._config = config
        self._client = cliente or MetaOrganicoClient(access_token, api_version)

    def fetch(self, desde: datetime.date, hasta: datetime.date) -> list[MetaOrganicoPost]:
        registros: list[MetaOrganicoPost] = []
        fallidos: list[str] = []

        for perfil in self._config.perfiles:
            try:
                if perfil.red == Red.FACEBOOK:
                    registros.extend(self._fetch_facebook(perfil, desde, hasta))
                else:
                    registros.extend(self._fetch_instagram(perfil, desde, hasta))
            except Exception as error:
                logger.warning("Perfil '%s' (%s) falló, se sigue con el resto: %s", perfil.nombre, perfil.id, error)
                fallidos.append(f"{perfil.nombre} ({perfil.id}): {error}")

        if fallidos:
            resumen = "; ".join(fallidos)
            if len(fallidos) == len(self._config.perfiles):
                raise RuntimeError(f"Todos los perfiles de Meta Orgánico fallaron: {resumen}")
            logger.warning(
                "%d de %d perfiles de Meta Orgánico fallaron (se guardó el resto): %s",
                len(fallidos), len(self._config.perfiles), resumen,
            )

        return registros

    def _fetch_facebook(
        self, perfil: PerfilMetaOrganico, desde: datetime.date, hasta: datetime.date
    ) -> list[MetaOrganicoPost]:
        nombre_pagina = self._client.obtener_nombre_pagina(perfil.page_id)
        token_pagina = self._client.obtener_token_de_pagina(perfil.page_id)
        posts = self._client.obtener_posts_pagina(perfil.page_id, desde, hasta, token=token_pagina)
        registros = []
        for post in posts:
            insights = self._client.obtener_insights_post(post["id"], token=token_pagina)
            registros.append(mapear_post_facebook(perfil, nombre_pagina, post, insights))
        return registros

    def _fetch_instagram(
        self, perfil: PerfilMetaOrganico, desde: datetime.date, hasta: datetime.date
    ) -> list[MetaOrganicoPost]:
        nombre_cuenta = self._client.obtener_nombre_cuenta_ig(perfil.ig_user_id)
        media = self._client.obtener_media_ig(perfil.ig_user_id, desde, hasta)
        registros = []
        for item in media:
            insights = self._client.obtener_insights_media(item["id"])
            registros.append(mapear_media_instagram(perfil, nombre_cuenta, item, insights))
        return registros

    def upsert(self, conn: sqlite3.Connection, datos: list[MetaOrganicoPost]) -> ResultadoUpsert:
        return upsert_meta_organico(conn, datos)
