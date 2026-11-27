"""Cliente delgado sobre Google Analytics Data API (GA4), vía REST directo
(sin el SDK oficial de Google, pesado) — mismo patrón liviano que los demás
conectores.

Trae, por propiedad: el total diario (sesiones, usuarios totales, usuarios
nuevos), el desglose por página (las landings que arma CAINCO viven como
páginas del sitio principal, no como propiedades separadas — ver
GA4MetricaPagina), el desglose por canal de adquisición (de dónde viene
el tráfico: redes, búsqueda orgánica, directo, pago, referidos) y el
desglose por evento (clics, envíos de formulario, descargas, y cualquier
evento de "llamado a la acción" que ya esté instrumentado en el sitio —
ver GA4MetricaEvento).
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

    def obtener_metricas_por_pagina(
        self, property_id: str, desde: datetime.date, hasta: datetime.date
    ) -> list[dict]:
        """Devuelve una fila por día+página (sesiones, vistas de página,
        usuarios totales/nuevos), para el rango [desde, hasta] (inclusive)
        — permite aislar el tráfico de una landing puntual (ej.
        "/curso-emprendimiento") dentro del sitio principal, con las
        mismas métricas de KPI que el total del sitio, sin necesitar una
        propiedad de Analytics separada por landing."""
        body = {
            "dateRanges": [{"startDate": desde.isoformat(), "endDate": hasta.isoformat()}],
            "dimensions": [{"name": "date"}, {"name": "pagePath"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "screenPageViews"},
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
            pagina = fila["dimensionValues"][1]["value"]  # "/curso-emprendimiento"
            valores = fila["metricValues"]
            filas.append(
                {
                    "fecha": datetime.date(
                        int(fecha_ga4[0:4]), int(fecha_ga4[4:6]), int(fecha_ga4[6:8])
                    ),
                    "pagina": pagina,
                    "sesiones": int(valores[0]["value"]),
                    "vistas_pagina": int(valores[1]["value"]),
                    "usuarios_totales": int(valores[2]["value"]),
                    "usuarios_nuevos": int(valores[3]["value"]),
                }
            )
        return filas

    def obtener_metricas_por_canal(
        self, property_id: str, desde: datetime.date, hasta: datetime.date
    ) -> list[dict]:
        """Devuelve una fila por día+canal+página (sesiones) — de dónde
        viene el tráfico: Organic Social, Organic Search, Direct, Paid
        Social, Referral, etc. (agrupación estándar de GA4, "Default
        channel group"). Incluye la página para poder ver de dónde viene
        el tráfico de UNA landing puntual, no solo del sitio entero."""
        body = {
            "dateRanges": [{"startDate": desde.isoformat(), "endDate": hasta.isoformat()}],
            "dimensions": [{"name": "date"}, {"name": "sessionDefaultChannelGroup"}, {"name": "pagePath"}],
            "metrics": [{"name": "sessions"}],
        }
        data = solicitar(
            "POST",
            f"{_BASE_URL}/properties/{property_id}:runReport",
            headers=self._headers(),
            json=body,
        )

        filas = []
        for fila in data.get("rows", []):
            fecha_ga4 = fila["dimensionValues"][0]["value"]
            canal = fila["dimensionValues"][1]["value"]  # "Organic Social", "Direct", etc.
            pagina = fila["dimensionValues"][2]["value"]
            valores = fila["metricValues"]
            filas.append(
                {
                    "fecha": datetime.date(
                        int(fecha_ga4[0:4]), int(fecha_ga4[4:6]), int(fecha_ga4[6:8])
                    ),
                    "canal": canal,
                    "pagina": pagina,
                    "sesiones": int(valores[0]["value"]),
                }
            )
        return filas

    def obtener_metricas_por_evento(
        self, property_id: str, desde: datetime.date, hasta: datetime.date
    ) -> list[dict]:
        """Devuelve una fila por día+evento+página (cantidad) — todos los
        eventos que GA4 ya esté registrando (clics, envíos de formulario,
        descargas, y cualquier evento de "llamado a la acción" que un
        desarrollador haya instrumentado a mano, ej. "contact_link_click").
        No filtra a "conversiones" marcadas como tales en GA4 (eso requiere
        la Admin API, no la Data API que usa este cliente) — trae todos, el
        dashboard decide cuáles mostrar como relevantes. Incluye la página
        para poder ver las interacciones de UNA landing puntual."""
        body = {
            "dateRanges": [{"startDate": desde.isoformat(), "endDate": hasta.isoformat()}],
            "dimensions": [{"name": "date"}, {"name": "eventName"}, {"name": "pagePath"}],
            "metrics": [{"name": "eventCount"}],
        }
        data = solicitar(
            "POST",
            f"{_BASE_URL}/properties/{property_id}:runReport",
            headers=self._headers(),
            json=body,
        )

        filas = []
        for fila in data.get("rows", []):
            fecha_ga4 = fila["dimensionValues"][0]["value"]
            evento = fila["dimensionValues"][1]["value"]  # "contact_link_click", "click", etc.
            pagina = fila["dimensionValues"][2]["value"]
            valores = fila["metricValues"]
            filas.append(
                {
                    "fecha": datetime.date(
                        int(fecha_ga4[0:4]), int(fecha_ga4[4:6]), int(fecha_ga4[6:8])
                    ),
                    "evento": evento,
                    "pagina": pagina,
                    "conteo": int(valores[0]["value"]),
                }
            )
        return filas
