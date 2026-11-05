import datetime

import responses

from marketing_analytics.connectors.mailchimp.client import MailchimpClient

BASE = "https://us21.api.mailchimp.com/3.0"


@responses.activate
def test_listar_campanas_sigue_paginando_hasta_agotar(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MailchimpClient(api_key="fake-key", server_prefix="us21")

    pagina_1 = {"campaigns": [{"id": f"camp_{i}"} for i in range(100)]}
    pagina_2 = {"campaigns": [{"id": "camp_100"}]}
    responses.add(responses.GET, f"{BASE}/campaigns", json=pagina_1, status=200)
    responses.add(responses.GET, f"{BASE}/campaigns", json=pagina_2, status=200)

    campanas = cliente.listar_campanas_enviadas(
        datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
    )

    assert len(campanas) == 101


@responses.activate
def test_obtener_reporte(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MailchimpClient(api_key="fake-key", server_prefix="us21")
    responses.add(
        responses.GET,
        f"{BASE}/reports/camp_1",
        json={"id": "camp_1", "emails_sent": 500},
        status=200,
    )

    reporte = cliente.obtener_reporte("camp_1")
    assert reporte["emails_sent"] == 500


@responses.activate
def test_obtener_detalle_clics_pagina_correctamente(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MailchimpClient(api_key="fake-key", server_prefix="us21")
    responses.add(
        responses.GET,
        f"{BASE}/reports/camp_1/click-details",
        json={"urls_clicked": [{"url": "https://wa.me/59171234567", "total_clicks": 12}]},
        status=200,
    )

    detalle = cliente.obtener_detalle_clics("camp_1")
    assert detalle[0]["total_clicks"] == 12
