"""Cliente delgado sobre la Meta Marketing API (Graph API, oficial).

Endpoints usados:
- GET /act_{id}/campaigns  -> objetivo por campaña (no viene en insights)
- GET /act_{id}/insights   -> métricas diarias por campaña y plataforma
"""
from __future__ import annotations

import datetime
import json

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from marketing_analytics.connectors.http_utils import ApiError, solicitar

# Meta reporta el límite de peticiones de la aplicación ("Application
# request limit reached") como un error de negocio dentro del cuerpo JSON,
# con HTTP 400 — no como un 429. El retry genérico de `solicitar` solo mira
# el código HTTP, así que sin esto un backfill grande se corta entero la
# primera vez que se topa con el límite, en vez de esperar y seguir.
_CODIGOS_LIMITE_META = {4, 17, 32, 613}


def _es_limite_de_meta(excepcion: BaseException) -> bool:
    if not isinstance(excepcion, ApiError):
        return False
    try:
        codigo = json.loads(excepcion.payload)["error"]["code"]
    except (ValueError, KeyError, TypeError):
        return False
    return codigo in _CODIGOS_LIMITE_META


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=10, max=120),
    retry=retry_if_exception(_es_limite_de_meta),
)
def _solicitar(metodo: str, url: str, **kwargs) -> dict:
    return solicitar(metodo, url, **kwargs)


_CAMPOS_INSIGHTS = (
    "campaign_id",
    "campaign_name",
    "spend",
    "reach",
    "impressions",
    "clicks",
    "ctr",
    "cpc",
    "actions",
    "date_start",
    "date_stop",
)


class MetaAdsClient:
    def __init__(self, access_token: str, api_version: str):
        self._access_token = access_token
        self._base_url = f"https://graph.facebook.com/{api_version}"

    def obtener_objetivos_campanas(self, ad_account_id: str) -> dict[str, str]:
        objetivos: dict[str, str] = {}
        url = f"{self._base_url}/act_{ad_account_id}/campaigns"
        params = {"fields": "id,objective", "limit": 200, "access_token": self._access_token}

        while url:
            data = _solicitar("GET", url, params=params)
            for campana in data.get("data", []):
                objetivos[campana["id"]] = campana.get("objective", "")
            url = data.get("paging", {}).get("next")
            params = None  # la URL 'next' ya trae todos los query params
        return objetivos

    def obtener_fechas_campanas(self, ad_account_id: str) -> dict[str, tuple[str | None, str | None]]:
        """Fecha de inicio/fin real de cada campaña, tal cual se programó en
        Ads Manager — el endpoint de insights no las expone (solo trae
        `date_start`/`date_stop` del día puntual del insight). Devuelve las
        fechas crudas como las manda Meta (con hora y huso horario); el
        mapper las recorta a fecha. Sin `stop_time` para una campaña sin
        fecha de fin configurada (corre hasta que se la pause a mano)."""
        fechas: dict[str, tuple[str | None, str | None]] = {}
        url = f"{self._base_url}/act_{ad_account_id}/campaigns"
        params = {"fields": "id,start_time,stop_time", "limit": 200, "access_token": self._access_token}

        while url:
            data = _solicitar("GET", url, params=params)
            for campana in data.get("data", []):
                fechas[campana["id"]] = (campana.get("start_time"), campana.get("stop_time"))
            url = data.get("paging", {}).get("next")
            params = None
        return fechas

    def obtener_pagina_origen_campana(self, campaign_id: str) -> str:
        """Para campañas creadas con el botón "Promocionar" sobre un post ya
        existente (en vez de armadas a mano en Ads Manager), Meta le pone un
        nombre automático a la campaña que nunca menciona una unidad — el
        emparejamiento por texto no alcanza para ubicarlas. Acá se resuelve
        la página/cuenta de origen real del post promocionado a partir del
        primer anuncio de la campaña, para poder ubicarlas por página en vez
        de adivinar por nombre. Devuelve "" si la campaña no es un boost de
        un solo post, o si la consulta falla — nunca rompe la sincronización
        por un dato que es solo un dato de respaldo."""
        try:
            data = _solicitar(
                "GET",
                f"{self._base_url}/{campaign_id}/ads",
                params={
                    "fields": "creative{effective_object_story_id}",
                    "limit": 5,
                    "access_token": self._access_token,
                },
            )
        except Exception:
            return ""
        for anuncio in data.get("data", []):
            story_id = anuncio.get("creative", {}).get("effective_object_story_id", "")
            if story_id and "_" in story_id:
                return story_id.split("_")[0]
        return ""

    def obtener_insights_campana(
        self, ad_account_id: str, desde: datetime.date, hasta: datetime.date
    ) -> list[dict]:
        filas: list[dict] = []
        url = f"{self._base_url}/act_{ad_account_id}/insights"
        params = {
            "level": "campaign",
            "fields": ",".join(_CAMPOS_INSIGHTS),
            "breakdowns": "publisher_platform",
            "time_increment": 1,
            "time_range": f'{{"since":"{desde.isoformat()}","until":"{hasta.isoformat()}"}}',
            "limit": 200,
            "access_token": self._access_token,
        }

        while url:
            data = _solicitar("GET", url, params=params)
            filas.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = None
        return filas
