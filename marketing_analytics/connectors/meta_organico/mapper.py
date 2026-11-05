"""Mapea posts de Facebook y media de Instagram a MetaOrganicoPost.

Nota honesta: Instagram Graph API no expone "clics totales" ni "clics a
enlace" a nivel de publicación orgánica (eso solo existe para contenido de
pauta) — quedan en 0 para IG, no se inventa un valor.
"""
from __future__ import annotations

import datetime

from marketing_analytics.config.schema import PerfilMetaOrganico
from marketing_analytics.models.records import MetaOrganicoPost

_TIPOS_FACEBOOK = {
    "photo": "imagen",
    "video": "video",
    "share": "enlace_compartido",
    "album": "album",
}


def _parsear_fecha(valor: str) -> datetime.date:
    return datetime.datetime.fromisoformat(valor.replace("Z", "+00:00")).date()


def mapear_post_facebook(
    perfil: PerfilMetaOrganico, pagina: str, post: dict, insights: dict
) -> MetaOrganicoPost:
    attachments = post.get("attachments", {}).get("data", [])
    media_type = attachments[0].get("media_type", "status") if attachments else "status"
    tipo = _TIPOS_FACEBOOK.get(media_type, media_type)

    clics_por_tipo = insights.get("post_clicks_by_type") or {}
    reacciones_por_tipo = insights.get("post_reactions_by_type_total") or {}
    reacciones = sum(int(v) for v in reacciones_por_tipo.values())
    comentarios = post.get("comments", {}).get("summary", {}).get("total_count", 0)
    compartidos = post.get("shares", {}).get("count", 0)

    return MetaOrganicoPost(
        perfil=perfil.nombre,
        pagina=pagina,
        red="facebook",
        fecha_publicacion=_parsear_fecha(post["created_time"]),
        tipo=tipo,
        descripcion=post.get("message", "") or "",
        # "post_total_media_view_unique" es el candidato encontrado en la
        # documentación oficial de Meta para reemplazar el alcance orgánico
        # (ver client.py) — si no responde, queda en 0 (no inventado).
        alcance=int(insights.get("post_total_media_view_unique") or 0),
        visualizaciones=int(insights.get("post_media_view", 0)),
        total_clics=int(insights.get("post_clicks", 0)),
        clics_enlace=int(clics_por_tipo.get("link clicks", 0)),
        reacciones=reacciones,
        comentarios=comentarios,
        compartidos=compartidos,
        total_interacciones=reacciones + comentarios + compartidos,
        id_publicacion_origen=post["id"],
        imagen_url=post.get("full_picture", "") or "",
        link=post.get("permalink_url", "") or "",
    )


def mapear_media_instagram(
    perfil: PerfilMetaOrganico, pagina: str, media: dict, insights: dict
) -> MetaOrganicoPost:
    tipo = media.get("media_product_type") or media.get("media_type", "")
    reacciones = media.get("like_count", 0)
    comentarios = media.get("comments_count", 0)
    compartidos = int(insights.get("shares", 0))
    total_interacciones = int(insights.get("total_interactions", reacciones + comentarios + compartidos))

    return MetaOrganicoPost(
        perfil=perfil.nombre,
        pagina=pagina,
        red="instagram",
        fecha_publicacion=_parsear_fecha(media["timestamp"]),
        tipo=tipo,
        descripcion=media.get("caption", "") or "",
        alcance=int(insights.get("reach", 0)),
        visualizaciones=int(insights.get("views", 0)),
        total_clics=0,
        clics_enlace=0,
        reacciones=reacciones,
        comentarios=comentarios,
        compartidos=compartidos,
        total_interacciones=total_interacciones,
        id_publicacion_origen=media["id"],
        imagen_url=media.get("media_url", "") or media.get("thumbnail_url", "") or "",
        link=media.get("permalink", "") or "",
    )
