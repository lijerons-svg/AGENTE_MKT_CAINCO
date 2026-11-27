"""Cliente delgado sobre Google Analytics Data API (GA4), vía REST directo
(sin el SDK oficial de Google, pesado) — mismo patrón liviano que los demás
conectores.

MVP: solo trae el total diario (sesiones, usuarios totales, usuarios
nuevos) por propiedad. Desglose por canal/página/evento queda para una
siguiente vuelta, reusando este mismo cliente.
"""
from __future__ import annotations

import datetime
from typing import Callable

from marketing_analytics.connectors.ga4.auth import obtener_token
from marketing_analytics.connectors.http_utils import solicitar

_BASE_URL = "https://analyticsdata.googleapis.com/v1beta"


class GA4Client:
    def __init__(
        self,
        ruta_credenciales: str,
        obtener_token_fn: Callable[[str], str] = obtener_token,
    ):
        self._ruta_credenciales = ruta_credenciales
        # Inyectable para tests: evita depender de una firma JWT real (y de
        # que `cryptography` esté instalada/funcionando en esa máquina)
        # solo para probar la forma de la consulta y el mapeo de la
        # respuesta.
        self._obtener_token_fn = obtener_token_fn

    def _headers(self) -> dict:
        token = self._obtener_token_fn(self._ruta_credenciales)
        return {"Authorization": f"Bearer {token}"}

    def obtener_metricas_diarias(
        self, property_id: str, desde: datetime.date, hasta: datetime.date
    ) -> list[dict]:
        """Devuelve una fila por día con sesiones/usuarios totales/usuarios
        nuevos, para el rango [desde, hasta] (inclusive)."""
        body = {
            "dateRanges": [{"startDate": desde.isoformat(), "endDate": hasta.isoformat()}],
            "dimensions": [{"name": "date"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "totalUsers"},
                {"name": "newUsers"},
            ],
        }
        data = solicitar(
            "POST",
            f"{_BASE_URL}/properties/{property_id}:runReport",
            headers=self._headers(),
            json=body,
        )

        filas = []
        for fila in data.get("rows", []):
            fecha_ga4 = fila["dimensionValues"][0]["value"]  # "20260115"
            valores = fila["metricValues"]
            filas.append(
                {
                    "fecha": datetime.date(
                        int(fecha_ga4[0:4]), int(fecha_ga4[4:6]), int(fecha_ga4[6:8])
                    ),
                    "sesiones": int(valores[0]["value"]),
                    "usuarios_totales": int(valores[1]["value"]),
                    "usuarios_nuevos": int(valores[2]["value"]),
                }
            )
        return filas
