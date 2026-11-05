"""Cliente delgado sobre la Mailchimp Marketing API v3 (oficial, documentada).

Endpoints usados:
- GET /campaigns                       -> listar campañas
- GET /reports/{campaign_id}            -> métricas de la campaña
- GET /reports/{campaign_id}/click-details -> clics por enlace (incluye wa.me)
"""
from __future__ import annotations

import datetime

from marketing_analytics.connectors.http_utils import solicitar

_PAGE_SIZE = 100


class MailchimpClient:
    def __init__(self, api_key: str, server_prefix: str):
        self._api_key = api_key
        self._base_url = f"https://{server_prefix}.api.mailchimp.com/3.0"

    def _auth(self) -> tuple[str, str]:
        return ("anystring", self._api_key)

    def listar_campanas_enviadas(
        self, desde: datetime.date, hasta: datetime.date
    ) -> list[dict]:
        """Devuelve el resumen de campañas de tipo 'sent' enviadas en el rango."""
        campanas: list[dict] = []
        offset = 0
        while True:
            data = solicitar(
                "GET",
                f"{self._base_url}/campaigns",
                auth=self._auth(),
                params={
                    "status": "sent",
                    "since_send_time": f"{desde.isoformat()}T00:00:00+00:00",
                    "before_send_time": f"{hasta.isoformat()}T23:59:59+00:00",
                    "count": _PAGE_SIZE,
                    "offset": offset,
                    "sort_field": "send_time",
                    "sort_dir": "ASC",
                },
            )
            lote = data.get("campaigns", [])
            campanas.extend(lote)
            if len(lote) < _PAGE_SIZE:
                break
            offset += _PAGE_SIZE
        return campanas

    def obtener_reporte(self, campaign_id: str) -> dict:
        return solicitar(
            "GET", f"{self._base_url}/reports/{campaign_id}", auth=self._auth()
        )

    def obtener_detalle_clics(self, campaign_id: str) -> list[dict]:
        """Devuelve, por enlace tracked de la campaña, id/url/clics — usado
        para extraer todos los enlaces wa.me con su conteo real de clics."""
        enlaces: list[dict] = []
        offset = 0
        while True:
            data = solicitar(
                "GET",
                f"{self._base_url}/reports/{campaign_id}/click-details",
                auth=self._auth(),
                params={"count": _PAGE_SIZE, "offset": offset},
            )
            lote = data.get("urls_clicked", [])
            enlaces.extend(lote)
            if len(lote) < _PAGE_SIZE:
                break
            offset += _PAGE_SIZE
        return enlaces
