"""Resuelve la métrica "Resultados" de una fila de insights de Meta Ads.

Meta NO expone un campo único "results" en la Insights API: en el propio
Ads Manager, la columna "Resultados" depende del objetivo de la campaña
(un link_click para tráfico, un lead para generación de leads, etc.), y esa
resolución vive del lado de la UI, no de un endpoint. Este mapeo reproduce
esa misma lógica de forma explícita y configurable: si el equipo optimiza
campañas hacia una acción distinta de la esperada por objetivo, hay que
ajustar esta tabla — no hay endpoint oficial que lo resuelva por nosotros.
"""
from __future__ import annotations

# Acción de Meta para un clic en "Enviar mensaje" que abre una conversación
# de WhatsApp/Messenger/Instagram Direct — se usa tanto para "Resultados" en
# campañas de objetivo MESSAGES como para la columna propia "Conversación
# iniciada", visible en cualquier campaña, tenga o no ese objetivo.
ACCION_CONVERSACION_INICIADA = "onsite_conversion.messaging_conversation_started_7d"

ACCION_POR_OBJETIVO: dict[str, tuple[str, ...]] = {
    "OUTCOME_TRAFFIC": ("link_click",),
    "LINK_CLICKS": ("link_click",),
    "OUTCOME_LEADS": ("lead", "onsite_conversion.lead_grouped"),
    "LEAD_GENERATION": ("lead",),
    "OUTCOME_SALES": ("purchase", "offsite_conversion.fb_pixel_purchase"),
    "CONVERSIONS": ("purchase", "offsite_conversion.fb_pixel_purchase"),
    "OUTCOME_ENGAGEMENT": ("post_engagement",),
    "POST_ENGAGEMENT": ("post_engagement",),
    "MESSAGES": (ACCION_CONVERSACION_INICIADA,),
}

# Mismo conjunto que usan el dashboard (esObjetivoDeAlcance en
# template_analisis.js) y el reporte PPT (_es_objetivo_de_alcance en
# reports_pptx/agregacion.py) — si un objetivo falta acá pero está en esos
# otros dos, la campaña se muestra como "de alcance" (conversión = n/a) y
# a la vez su "Resultados" queda en 0 en vez del alcance real, un
# contrasentido silencioso.
_OBJETIVOS_DE_ALCANCE = ("OUTCOME_AWARENESS", "BRAND_AWARENESS", "REACH")


def resolver_resultados(objetivo: str, actions: list[dict] | None, reach: int = 0) -> int:
    if objetivo in _OBJETIVOS_DE_ALCANCE:
        return reach

    if not actions:
        return 0

    acciones_por_tipo = {a["action_type"]: a for a in actions}
    for tipo_preferido in ACCION_POR_OBJETIVO.get(objetivo, ()):
        if tipo_preferido in acciones_por_tipo:
            return int(float(acciones_por_tipo[tipo_preferido]["value"]))

    return 0


def resolver_conversaciones_iniciadas(actions: list[dict] | None) -> int:
    if not actions:
        return 0
    for accion in actions:
        if accion["action_type"] == ACCION_CONVERSACION_INICIADA:
            return int(float(accion["value"]))
    return 0
