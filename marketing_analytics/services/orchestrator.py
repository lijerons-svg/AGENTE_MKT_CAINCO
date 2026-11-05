"""Orquestador ETL: corre todos los conectores activos, uno por uno, sin que
la falla de uno tumbe a los demás; registra la ejecución completa en las
tablas `ejecuciones`/`logs` y devuelve un resumen para reportes.
"""
from __future__ import annotations

import datetime
import logging
import sqlite3
from dataclasses import dataclass, field

from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.database.ejecuciones import (
    finalizar_ejecucion,
    iniciar_ejecucion,
    registrar_log,
)
from marketing_analytics.database.repository import ResultadoUpsert

logger = logging.getLogger(__name__)


@dataclass
class ResumenConector:
    nombre: str
    resultado: ResultadoUpsert | None = None
    error: str | None = None


@dataclass
class ResumenEjecucion:
    ejecucion_id: int
    resultado_total: ResultadoUpsert = field(default_factory=ResultadoUpsert)
    por_conector: list[ResumenConector] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)

    @property
    def estado(self) -> str:
        if not self.errores:
            return "exitoso"
        if self.resultado_total.total > 0:
            return "parcial"
        return "fallido"


def ejecutar(
    conn: sqlite3.Connection,
    conectores: list[BaseConnector],
    desde: datetime.date,
    hasta: datetime.date,
) -> ResumenEjecucion:
    ejecucion_id = iniciar_ejecucion(conn)
    resumen = ResumenEjecucion(ejecucion_id=ejecucion_id)

    for conector in conectores:
        try:
            datos = conector.fetch(desde, hasta)
            resultado = conector.upsert(conn, datos)
            resumen.resultado_total += resultado
            resumen.por_conector.append(ResumenConector(conector.nombre, resultado=resultado))
            registrar_log(
                conn,
                ejecucion_id,
                "INFO",
                conector.nombre,
                f"nuevos={resultado.nuevos} actualizados={resultado.actualizados} "
                f"descartados={resultado.descartados}",
            )
        except Exception as error:
            # Un conector que falla no debe tumbar la corrida de los demás:
            # se registra el error y se sigue (requisito de manejo de errores).
            logger.exception("Fallo el conector %s", conector.nombre)
            mensaje = f"{conector.nombre}: {error}"
            resumen.errores.append(mensaje)
            resumen.por_conector.append(ResumenConector(conector.nombre, error=str(error)))
            registrar_log(conn, ejecucion_id, "ERROR", conector.nombre, str(error))

    finalizar_ejecucion(
        conn,
        ejecucion_id,
        resumen.resultado_total,
        resumen.estado,
        "; ".join(resumen.errores),
    )
    return resumen
