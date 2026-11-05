import datetime

import pytest
import responses

from marketing_analytics.connectors.meta_ads.client import MetaAdsClient

BASE = "https://graph.facebook.com/v21.0"


@responses.activate
def test_obtener_objetivos_sigue_el_paging_next(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/act_123/campaigns",
        json={
            "data": [{"id": "camp_1", "objective": "OUTCOME_TRAFFIC"}],
            "paging": {"next": f"{BASE}/act_123/campaigns?after=cursor1"},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE}/act_123/campaigns",
        json={"data": [{"id": "camp_2", "objective": "OUTCOME_LEADS"}]},
        status=200,
    )

    objetivos = cliente.obtener_objetivos_campanas("123")

    assert objetivos == {"camp_1": "OUTCOME_TRAFFIC", "camp_2": "OUTCOME_LEADS"}


@responses.activate
def test_obtener_fechas_campanas_sigue_el_paging_next(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/act_123/campaigns",
        json={
            "data": [{"id": "camp_1", "start_time": "2026-07-01T00:00:00-0400", "stop_time": "2026-07-31T23:59:00-0400"}],
            "paging": {"next": f"{BASE}/act_123/campaigns?after=cursor1"},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE}/act_123/campaigns",
        json={"data": [{"id": "camp_2", "start_time": "2026-08-01T00:00:00-0400"}]},
        status=200,
    )

    fechas = cliente.obtener_fechas_campanas("123")

    assert fechas == {
        "camp_1": ("2026-07-01T00:00:00-0400", "2026-07-31T23:59:00-0400"),
        "camp_2": ("2026-08-01T00:00:00-0400", None),
    }


@responses.activate
def test_obtener_insights_devuelve_filas_mapeables(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/act_123/insights",
        json={
            "data": [
                {
                    "campaign_id": "camp_1",
                    "campaign_name": "Campaña Julio",
                    "spend": "10.5",
                    "reach": "1000",
                    "impressions": "1500",
                    "clicks": "30",
                    "ctr": "2.0",
                    "cpc": "0.35",
                    "date_start": "2026-07-01",
                    "date_stop": "2026-07-01",
                    "publisher_platform": "facebook",
                    "actions": [{"action_type": "link_click", "value": "25"}],
                }
            ]
        },
        status=200,
    )

    filas = cliente.obtener_insights_campana(
        "123", datetime.date(2026, 7, 1), datetime.date(2026, 7, 1)
    )

    assert len(filas) == 1
    assert filas[0]["campaign_id"] == "camp_1"


@responses.activate
def test_obtener_insights_reintenta_ante_limite_de_aplicacion_de_meta(monkeypatch):
    """Meta reporta el límite de peticiones de la app como un 400 con un
    código de error propio, no como un 429 — sin manejo especial, esto
    tumbaba el backfill entero a la primera vez que se topaba el límite."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/act_123/insights",
        json={"error": {"message": "Application request limit reached", "code": 4, "error_subcode": 1504022}},
        status=400,
    )
    responses.add(
        responses.GET,
        f"{BASE}/act_123/insights",
        json={
            "data": [
                {
                    "campaign_id": "camp_1",
                    "campaign_name": "Campaña Julio",
                    "spend": "10.5",
                    "reach": "1000",
                    "impressions": "1500",
                    "clicks": "30",
                    "ctr": "2.0",
                    "cpc": "0.35",
                    "date_start": "2026-07-01",
                    "date_stop": "2026-07-01",
                    "publisher_platform": "facebook",
                    "actions": [],
                }
            ]
        },
        status=200,
    )

    filas = cliente.obtener_insights_campana(
        "123", datetime.date(2026, 7, 1), datetime.date(2026, 7, 1)
    )

    assert len(filas) == 1
    assert filas[0]["campaign_id"] == "camp_1"


@responses.activate
def test_obtener_insights_no_reintenta_errores_que_no_son_de_limite(monkeypatch):
    """El reintento es específico al código de límite de Meta: un error real
    (parámetro inválido, token vencido) debe fallar de una, no reintentar
    5 veces algo que nunca se va a arreglar solo."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/act_123/insights",
        json={"error": {"message": "Invalid parameter", "code": 100}},
        status=400,
    )

    with pytest.raises(Exception):
        cliente.obtener_insights_campana("123", datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(responses.calls) == 1


@responses.activate
def test_obtener_pagina_origen_campana_extrae_el_page_id_del_story_id(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/camp_1/ads",
        json={"data": [{"creative": {"effective_object_story_id": "111222333_9988776655"}}]},
        status=200,
    )

    assert cliente.obtener_pagina_origen_campana("camp_1") == "111222333"


@responses.activate
def test_obtener_pagina_origen_campana_sin_story_id_devuelve_vacio(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/camp_2/ads",
        json={"data": [{"creative": {}}]},
        status=200,
    )

    assert cliente.obtener_pagina_origen_campana("camp_2") == ""


@responses.activate
def test_obtener_pagina_origen_campana_sin_anuncios_devuelve_vacio(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(responses.GET, f"{BASE}/camp_3/ads", json={"data": []}, status=200)

    assert cliente.obtener_pagina_origen_campana("camp_3") == ""


@responses.activate
def test_obtener_pagina_origen_campana_no_rompe_si_la_api_falla(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaAdsClient(access_token="fake-token", api_version="v21.0")

    responses.add(responses.GET, f"{BASE}/camp_4/ads", json={"error": "boom"}, status=500)
    responses.add(responses.GET, f"{BASE}/camp_4/ads", json={"error": "boom"}, status=500)
    responses.add(responses.GET, f"{BASE}/camp_4/ads", json={"error": "boom"}, status=500)
    responses.add(responses.GET, f"{BASE}/camp_4/ads", json={"error": "boom"}, status=500)
    responses.add(responses.GET, f"{BASE}/camp_4/ads", json={"error": "boom"}, status=500)

    assert cliente.obtener_pagina_origen_campana("camp_4") == ""
