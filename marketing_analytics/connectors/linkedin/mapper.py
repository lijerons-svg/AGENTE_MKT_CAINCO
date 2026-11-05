"""Mapea posts de LinkedIn (+ sus estadísticas) a LinkedInOrganicoPost.

Nota honesta: el esquema de `estadisticas` (totalShareStatistics.*) sigue
la documentación de LinkedIn para esta API pero no se confirmó todavía
contra una respuesta real — cualquier campo ausente queda en 0, nunca se
inventa un valor (mismo criterio que meta_organico/mapper.py)."""
from __future__ import annotations

import datetime

from marketing_analytics.models.records import LinkedInOrganicoPost


def _fecha_post(post: dict) -> datetime.date:
    ms = post.get("publishedAt") or post.get("createdAt") or 0
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.timezone.utc).date()


def _tipo_post(post: dict) -> str:
    """El tipo de contenido viene codificado en el namespace del id del
    media adjunto (ej. "urn:li:video:...", "urn:li:image:...",
    "urn:li:document:..." — confirmado con datos reales), no en un campo
    propio como en Meta."""
    media = post.get("content", {}).get("media")
    if media and media.get("id"):
        partes = media["id"].split(":")
        if len(partes) >= 3:
            return partes[2]
    if post.get("content"):
        return "otro"
    return "texto"


def mapear_post(pagina: str, post: dict, estadisticas: dict) -> LinkedInOrganicoPost:
    total = estadisticas.get("totalShareStatistics", {})
    reacciones = int(total.get("likeCount", 0))
    comentarios = int(total.get("commentCount", 0))
    compartidos = int(total.get("shareCount", 0))

    return LinkedInOrganicoPost(
        pagina=pagina,
        fecha_publicacion=_fecha_post(post),
        tipo=_tipo_post(post),
        descripcion=post.get("commentary", "") or "",
        impresiones=int(total.get("impressionCount", 0)),
        alcance=int(total.get("uniqueImpressionsCount", 0)),
        clics=int(total.get("clickCount", 0)),
        reacciones=reacciones,
        comentarios=comentarios,
        compartidos=compartidos,
        interacciones=reacciones + comentarios + compartidos,
        id_publicacion_origen=post["id"],
    )
