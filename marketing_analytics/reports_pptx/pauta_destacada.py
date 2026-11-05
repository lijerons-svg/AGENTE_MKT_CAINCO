"""Top de anuncios individuales de Meta Ads para el reporte PPT — a nivel
de anuncio, no de campaña (el conector principal de meta_ads es a nivel de
campaña, ver connectors/meta_ads/client.py). Solo se usa acá, bajo demanda,
igual que competencia.py — no se integra al pipeline automático porque el
dashboard y el Excel histórico siguen funcionando a nivel de campaña.
"""
from __future__ import annotations

import datetime

from marketing_analytics.connectors.http_utils import solicitar

_CAMPOS_INSIGHTS_ANUNCIO = (
    "ad_id",
    "ad_name",
    "campaign_name",
    "impressions",
    "clicks",
    "spend",
    "actions",
)

# Si "post_engagement" está presente ya es un agregado (reacciones +
# comentarios + compartidos + algunos clics) — sumarlo junto a los otros
# tipos duplicaría el conteo, por eso se usa como preferido y excluyente.
_ACCIONES_ENGAGEMENT_FALLBACK = ("post_reaction", "comment", "post_share", "like")


def _engagement_de_acciones(actions: list[dict] | None) -> int:
    if not actions:
        return 0
    por_tipo = {a["action_type"]: a for a in actions}
    if "post_engagement" in por_tipo:
        return int(float(por_tipo["post_engagement"]["value"]))
    return sum(
        int(float(por_tipo[tipo]["value"])) for tipo in _ACCIONES_ENGAGEMENT_FALLBACK if tipo in por_tipo
    )


def obtener_insights_anuncios(
    ad_account_id: str, access_token: str, api_version: str, desde: datetime.date, hasta: datetime.date
) -> list[dict]:
    """Una fila por (anuncio, red), agregada para todo el período — no por
    día, porque acá solo se necesita el total para rankear, no una serie
    temporal."""
    filas: list[dict] = []
    url = f"https://graph.facebook.com/{api_version}/act_{ad_account_id}/insights"
    params = {
        "level": "ad",
        "fields": ",".join(_CAMPOS_INSIGHTS_ANUNCIO),
        "breakdowns": "publisher_platform",
        "time_range": f'{{"since":"{desde.isoformat()}","until":"{hasta.isoformat()}"}}',
        "limit": 200,
        "access_token": access_token,
    }
    while url:
        data = solicitar("GET", url, params=params)
        filas.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        params = None
    return filas


def obtener_creativo_anuncio(ad_id: str, access_token: str, api_version: str) -> dict:
    """Imagen y tipo del anuncio — una llamada aparte, solo para los
    anuncios que efectivamente entran al top (no para todos, para no gastar
    llamadas de más)."""
    data = solicitar(
        "GET",
        f"https://graph.facebook.com/{api_version}/{ad_id}",
        params={
            "fields": "creative{thumbnail_url,image_url,object_type}",
            "access_token": access_token,
        },
    )
    creative = data.get("creative", {})
    return {
        "imagen_url": creative.get("image_url") or creative.get("thumbnail_url") or "",
        "tipo": creative.get("object_type", "") or "",
    }


_TIPOS_CREATIVO = {
    "PHOTO": "Imagen",
    "VIDEO": "Video",
    "SHARE": "Enlace",
    "LINK": "Enlace",
    "CAROUSEL": "Carrusel",
}


def formato_creativo(tipo_crudo: str) -> str:
    return _TIPOS_CREATIVO.get((tipo_crudo or "").upper(), "Anuncio")


def top_anuncios_destacados(
    filas_insights: list[dict],
    access_token: str,
    api_version: str,
    cantidad: int = 4,
) -> list[dict]:
    """Rankea por engagement y solo pide la imagen para los que entran al
    top — evita gastar llamadas en anuncios que no se van a mostrar."""
    for fila in filas_insights:
        fila["_engagement"] = _engagement_de_acciones(fila.get("actions"))

    ordenados = sorted(filas_insights, key=lambda f: f["_engagement"], reverse=True)
    top = ordenados[:cantidad]

    imagenes_por_ad_id: dict[str, dict] = {}
    resultado = []
    for fila in top:
        ad_id = fila["ad_id"]
        if ad_id not in imagenes_por_ad_id:
            imagenes_por_ad_id[ad_id] = obtener_creativo_anuncio(ad_id, access_token, api_version)
        creativo = imagenes_por_ad_id[ad_id]
        resultado.append(
            {
                "ad_id": ad_id,
                "titulo": fila.get("ad_name", "(sin nombre)"),
                "red": fila.get("publisher_platform", ""),
                "tipo": formato_creativo(creativo["tipo"]),
                "imagen_url": creativo["imagen_url"],
                "impresiones": int(float(fila.get("impressions", 0))),
                "clics": int(float(fila.get("clicks", 0))),
                "engagement": fila["_engagement"],
                "inversion": float(fila.get("spend", 0)),
            }
        )
    return resultado
