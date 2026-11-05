"""Conector de Control de Perfiles: snapshot mensual de seguidores +
agregados de publicaciones, por cada perfil de Meta Orgánico.

A diferencia de los demás conectores, `fetch()` solo trae de la API el dato
que no se puede derivar de lo ya guardado (el conteo actual de seguidores);
el resto (agregados del mes, delta de seguidores vs. el mes anterior) se
resuelve en `upsert()`, que sí tiene acceso a la base histórica — por eso
usa el mismo `MetaOrganicoClient`, sin duplicar su lógica de HTTP.
"""
from __future__ import annotations

import datetime
import logging
import sqlite3

from marketing_analytics.config.schema import MetaOrganicoConfig, Red
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.control_perfiles.aggregator import (
    construir_snapshot_mensual,
)
from marketing_analytics.connectors.meta_organico.client import MetaOrganicoClient
from marketing_analytics.database.repository import ResultadoUpsert, upsert_control_perfiles

logger = logging.getLogger(__name__)


class ControlPerfilesConnector(BaseConnector):
    nombre = "control_perfiles"

    def __init__(
        self,
        config: MetaOrganicoConfig,
        access_token: str,
        api_version: str,
        cliente: MetaOrganicoClient | None = None,
    ):
        self._config = config
        self._client = cliente or MetaOrganicoClient(access_token, api_version)

    def fetch(self, desde: datetime.date, hasta: datetime.date) -> list[dict]:
        resultados: list[dict] = []
        fallos: list[str] = []
        for perfil in self._config.perfiles:
            try:
                if perfil.red == Red.FACEBOOK:
                    seguidores = self._client.obtener_seguidores_pagina(perfil.page_id)
                else:
                    seguidores = self._client.obtener_seguidores_ig(perfil.ig_user_id)
                resultados.append(
                    {"perfil": perfil.nombre, "red": perfil.red.value, "seguidores": seguidores}
                )
            except Exception as error:
                logger.warning("No se pudo leer seguidores de '%s': %s", perfil.nombre, error)
                fallos.append(f"{perfil.nombre}: {error}")

        if fallos and not resultados:
            raise RuntimeError(
                f"Todos los perfiles fallaron al leer seguidores: {'; '.join(fallos)}"
            )
        return resultados

    def upsert(self, conn: sqlite3.Connection, datos: list[dict]) -> ResultadoUpsert:
        registros = [
            construir_snapshot_mensual(conn, d["perfil"], d["red"], d["seguidores"])
            for d in datos
        ]
        return upsert_control_perfiles(conn, registros)
