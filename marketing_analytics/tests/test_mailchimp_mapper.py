import datetime

from marketing_analytics.connectors.mailchimp.mapper import (
    mapear_campana,
    mapear_enlaces_whatsapp,
)


def test_mapear_campana_calcula_tasa_rebote_y_entregas():
    resumen = {
        "id": "camp_1",
        "settings": {"title": "Newsletter Julio"},
        "send_time": "2026-07-01T10:00:00+00:00",
    }
    reporte = {
        "id": "camp_1",
        "campaign_title": "Newsletter Julio",
        "send_time": "2026-07-01T10:00:00+00:00",
        "emails_sent": 1000,
        "bounces": {"hard_bounces": 5, "soft_bounces": 3, "syntax_errors": 0},
        "opens": {"open_rate": 0.35, "unique_opens": 300, "opens_total": 450},
        "clicks": {"click_rate": 0.05, "unique_clicks": 40, "clicks_total": 60},
        "unsubscribed": 2,
    }

    campana = mapear_campana(resumen, reporte)

    assert campana.fecha_envio == datetime.date(2026, 7, 1)
    assert campana.destinatarios == 1000
    assert campana.entregas == 992
    assert round(campana.tasa_rebote, 4) == round(8 / 1000, 4)
    assert campana.rebotes == 8
    assert campana.bajas == 2
    assert campana.uid.startswith("mailchimp|-|-|camp_1|2026-07-01")


def test_mapear_enlaces_whatsapp_filtra_solo_wa_me():
    detalle = [
        {"url": "https://wa.me/59171234567", "total_clicks": 12},
        {"url": "https://misitio.com/promo", "total_clicks": 5},
        {"url": "https://wa.me/59179876543?text=hola", "total_clicks": 3},
    ]

    enlaces = mapear_enlaces_whatsapp("camp_1", detalle)

    assert len(enlaces) == 2
    assert {e.url for e in enlaces} == {
        "https://wa.me/59171234567",
        "https://wa.me/59179876543?text=hola",
    }
    assert {e.clics for e in enlaces} == {12, 3}
