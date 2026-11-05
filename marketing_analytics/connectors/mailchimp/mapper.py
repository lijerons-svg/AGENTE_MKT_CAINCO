"""Mapea las respuestas crudas de Mailchimp a los modelos internos."""
from __future__ import annotations

import datetime

from marketing_analytics.models.records import MailchimpCampana, MailchimpEnlaceWhatsapp

_PATRON_WHATSAPP = "wa.me"


def mapear_campana(resumen: dict, reporte: dict) -> MailchimpCampana:
    bounces = reporte.get("bounces", {})
    opens = reporte.get("opens", {})
    clicks = reporte.get("clicks", {})

    emails_sent = reporte.get("emails_sent", 0)
    total_rebotes = (
        bounces.get("hard_bounces", 0)
        + bounces.get("soft_bounces", 0)
        + bounces.get("syntax_errors", 0)
    )
    entregas = max(emails_sent - total_rebotes, 0)
    tasa_rebote = (total_rebotes / emails_sent) if emails_sent else 0.0

    send_time = reporte.get("send_time") or resumen.get("send_time")
    fecha_envio = datetime.datetime.fromisoformat(send_time.replace("Z", "+00:00")).date()

    return MailchimpCampana(
        id_campana_origen=reporte["id"],
        nombre_campana=reporte.get("campaign_title", resumen.get("settings", {}).get("title", "")),
        fecha_envio=fecha_envio,
        destinatarios=emails_sent,
        entregas=entregas,
        tasa_apertura=opens.get("open_rate", 0.0),
        aperturas_unicas=opens.get("unique_opens", 0),
        aperturas_totales=opens.get("opens_total", 0),
        tasa_clics=clicks.get("click_rate", 0.0),
        clics_unicos=clicks.get("unique_clicks", 0),
        clics_totales=clicks.get("clicks_total", 0),
        tasa_rebote=tasa_rebote,
        rebotes=total_rebotes,
        bajas=reporte.get("unsubscribed", 0),
    )


def mapear_enlaces_whatsapp(
    campaign_id: str, detalle_clics: list[dict]
) -> list[MailchimpEnlaceWhatsapp]:
    """Filtra, de todos los enlaces trackeados de la campaña, los que apuntan
    a wa.me — puede haber más de uno, se devuelven todos."""
    return [
        MailchimpEnlaceWhatsapp(
            id_campana_origen=campaign_id,
            url=enlace["url"],
            clics=enlace.get("total_clicks", 0),
        )
        for enlace in detalle_clics
        if _PATRON_WHATSAPP in enlace.get("url", "")
    ]
