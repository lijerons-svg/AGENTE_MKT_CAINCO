"""Cliente delgado sobre Graph API para contenido orgánico (Páginas FB + IG).

Metricas de Insights verificadas para la versión de API configurada
(meta.api_version). Meta deprecia/renombra métricas de Insights con cierta
frecuencia — por eso toda llamada pasa por `obtener_insights_con_fallback`,
que degrada métrica por métrica en vez de romper la corrida completa si
alguna dejó de existir en la versión usada.
"""
from __future__ import annotations

import datetime
import logging

from marketing_analytics.connectors.http_utils import ApiError, solicitar

logger = logging.getLogger(__name__)


def _hasta_exclusivo(hasta: datetime.date) -> str:
    """Meta exige `since < until` estricto (rechaza incluso since == until,
    caso real: corridas automáticas donde desde == hasta == hoy). Se manda
    `hasta + 1 día` para que el día `hasta` completo quede incluido sin
    violar esa condición."""
    return (hasta + datetime.timedelta(days=1)).isoformat()

_CAMPOS_POST_FACEBOOK = (
    "id,message,created_time,permalink_url,full_picture,attachments{media_type},"
    "comments.summary(true).limit(0),shares"
)
# "post_impressions" fue deprecada por Meta el 15/nov/2025 y reemplazada por
# "post_media_view" (confirmado en producción).
#
# "post_impressions_unique" (alcance orgánico total) queda CONFIRMADA como
# eliminada sin reemplazo — verificado en la documentación oficial de Meta
# ("Page Post Impressions", developers.facebook.com/docs/graph-api/reference/
# page-post/insights/), que marca "Obsoleto a partir de Graph API v25" a
# post_impressions_unique, post_impressions_fan_unique,
# post_impressions_organic_unique y post_impressions_nonviral_unique — es
# decir, TODAS las variantes de alcance total/orgánico de esa sección. Las
# únicas variantes "_unique" que siguen vigentes ahí son
# post_impressions_paid_unique (alcance solo de pauta) y
# post_impressions_viral_unique (alcance solo viral): ninguna equivale a
# "alcance orgánico total".
#
# Candidato real encontrado en la sección "Page Post Media View" de la
# misma documentación oficial: "post_total_media_view_unique" ("number of
# total unique media viewers for FB post"), sin marca de obsoleta. Se
# agrega como intento — el fallback de abajo hace esto seguro: si el
# nombre no responde, se degrada solo esa métrica a 0, no rompe la corrida.
_METRICAS_POST_FACEBOOK = (
    "post_media_view",
    "post_total_media_view_unique",
    "post_clicks",
    "post_clicks_by_type",
    "post_reactions_by_type_total",
)

_CAMPOS_MEDIA_INSTAGRAM = (
    "id,caption,media_type,media_product_type,timestamp,permalink,like_count,"
    "comments_count,media_url,thumbnail_url"
)
# "plays" fue deprecada por Meta el 21/abr/2025: se unificó junto con
# "impressions" y "video_views" en una única métrica "views", aplicable a
# todo tipo de contenido (no solo video/reels).
_METRICAS_MEDIA_INSTAGRAM = ("reach", "saved", "shares", "total_interactions", "views")


class MetaOrganicoClient:
    def __init__(self, access_token: str, api_version: str):
        self._access_token = access_token
        self._base_url = f"https://graph.facebook.com/{api_version}"

    # ---------- identidad del perfil (una llamada por perfil, no por post) ----------

    def obtener_nombre_pagina(self, page_id: str) -> str:
        data = solicitar(
            "GET",
            f"{self._base_url}/{page_id}",
            params={"fields": "name", "access_token": self._access_token},
        )
        return data.get("name", page_id)

    def obtener_token_de_pagina(self, page_id: str) -> str | None:
        """Intercambia el token del Usuario del Sistema por el token propio
        de la Página. Meta lo exige para leer /posts (y sus insights) bajo
        la "nueva experiencia para páginas" — el token del Usuario del
        Sistema directo ya no alcanza para esas llamadas puntuales, aunque
        sí sirve para leer el nombre de la Página."""
        data = solicitar(
            "GET",
            f"{self._base_url}/{page_id}",
            params={"fields": "access_token", "access_token": self._access_token},
        )
        return data.get("access_token")

    def obtener_nombre_cuenta_ig(self, ig_user_id: str) -> str:
        data = solicitar(
            "GET",
            f"{self._base_url}/{ig_user_id}",
            params={"fields": "username", "access_token": self._access_token},
        )
        return data.get("username", ig_user_id)

    def obtener_seguidores_pagina(self, page_id: str) -> int:
        data = solicitar(
            "GET",
            f"{self._base_url}/{page_id}",
            params={"fields": "fan_count", "access_token": self._access_token},
        )
        return int(data.get("fan_count", 0))

    def obtener_seguidores_ig(self, ig_user_id: str) -> int:
        data = solicitar(
            "GET",
            f"{self._base_url}/{ig_user_id}",
            params={"fields": "followers_count", "access_token": self._access_token},
        )
        return int(data.get("followers_count", 0))

    # ---------- Facebook ----------

    def obtener_posts_pagina(
        self,
        page_id: str,
        desde: datetime.date,
        hasta: datetime.date,
        token: str | None = None,
    ) -> list[dict]:
        posts: list[dict] = []
        url = f"{self._base_url}/{page_id}/posts"
        params = {
            "fields": _CAMPOS_POST_FACEBOOK,
            "since": desde.isoformat(),
            "until": _hasta_exclusivo(hasta),
            "limit": 100,
            "access_token": token or self._access_token,
        }
        while url:
            data = solicitar("GET", url, params=params)
            posts.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = None
        return posts

    def obtener_insights_post(self, post_id: str, token: str | None = None) -> dict:
        return self.obtener_insights_con_fallback(post_id, _METRICAS_POST_FACEBOOK, token=token)

    # ---------- Instagram ----------

    def obtener_media_ig(
        self, ig_user_id: str, desde: datetime.date, hasta: datetime.date
    ) -> list[dict]:
        media: list[dict] = []
        url = f"{self._base_url}/{ig_user_id}/media"
        params = {
            "fields": _CAMPOS_MEDIA_INSTAGRAM,
            "since": desde.isoformat(),
            "until": _hasta_exclusivo(hasta),
            "limit": 100,
            "access_token": self._access_token,
        }
        while url:
            data = solicitar("GET", url, params=params)
            media.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = None
        return media

    def obtener_insights_media(self, media_id: str) -> dict:
        return self.obtener_insights_con_fallback(media_id, _METRICAS_MEDIA_INSTAGRAM)

    # ---------- compartido ----------

    def obtener_insights_con_fallback(
        self, object_id: str, metricas: tuple[str, ...], token: str | None = None
    ) -> dict:
        params_base = {"access_token": token or self._access_token}
        try:
            data = solicitar(
                "GET",
                f"{self._base_url}/{object_id}/insights",
                params={**params_base, "metric": ",".join(metricas)},
            )
            resultado = _aplanar_insights(data)
            if not resultado:
                # Meta puede responder 200 con "data": [] (sin error HTTP) en vez
                # de fallar cuando el token no tiene el permiso read_insights para
                # ese objeto, o cuando ya no hay datos disponibles — sin este log
                # esto queda indistinguible de "0 interacciones reales".
                logger.warning(
                    "Insights vacíos (sin error HTTP) para %s con métricas %s — "
                    "revisar permiso read_insights del token usado",
                    object_id,
                    metricas,
                )
            return resultado
        except ApiError as error:
            logger.warning(
                "Fallo el batch de métricas %s para %s (%s); reintentando una por una",
                metricas,
                object_id,
                error,
            )
            resultado: dict = {}
            for metrica in metricas:
                try:
                    data = solicitar(
                        "GET",
                        f"{self._base_url}/{object_id}/insights",
                        params={**params_base, "metric": metrica},
                    )
                    resultado.update(_aplanar_insights(data))
                except ApiError:
                    logger.warning(
                        "Métrica '%s' no disponible para %s en esta versión de API; "
                        "se registra como 0",
                        metrica,
                        object_id,
                    )
            return resultado


def _aplanar_insights(data: dict) -> dict:
    resultado = {}
    for fila in data.get("data", []):
        valores = fila.get("values", [])
        resultado[fila["name"]] = valores[0].get("value", 0) if valores else 0
    return resultado
