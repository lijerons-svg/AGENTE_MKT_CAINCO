"""Datos públicos de páginas de Facebook de la competencia — solo lo que
Meta expone sin necesitar administrar la página: seguidores y texto de
publicaciones. Instagram y LinkedIn no tienen equivalente público, por
eso `PerfilCompetidor` (config/schema.py) solo modela Facebook.
"""
from __future__ import annotations

import datetime

from marketing_analytics.connectors.http_utils import solicitar


def _hasta_exclusivo(hasta: datetime.date) -> str:
    return (hasta + datetime.timedelta(days=1)).isoformat()


def obtener_competidor(
    alias: str,
    access_token: str,
    api_version: str,
    desde: datetime.date,
    hasta: datetime.date,
) -> dict:
    """Devuelve {seguidores, publicaciones: [texto, ...]} para una página
    pública de Facebook. No requiere token de la página — `fan_count` y los
    posts públicos se leen con cualquier token válido de la app."""
    base = f"https://graph.facebook.com/{api_version}/{alias}"

    perfil = solicitar(
        "GET", base, params={"fields": "name,fan_count", "access_token": access_token}
    )

    posts: list[dict] = []
    url = f"{base}/posts"
    params = {
        "fields": "message,created_time",
        "since": desde.isoformat(),
        "until": _hasta_exclusivo(hasta),
        "limit": 100,
        "access_token": access_token,
    }
    while url:
        data = solicitar("GET", url, params=params)
        posts.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        params = None

    textos = [p["message"] for p in posts if p.get("message")]
    return {
        "nombre": perfil.get("name", alias),
        "seguidores": perfil.get("fan_count", 0),
        "cantidad_publicaciones": len(posts),
        "publicaciones": textos,
    }
