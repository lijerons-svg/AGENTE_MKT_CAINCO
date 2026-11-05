import datetime

from marketing_analytics.config.schema import CuentaPublicitaria
from marketing_analytics.connectors.meta_ads.mapper import mapear_fila_insight


def test_mapear_fila_insight_construye_registro_completo():
    cuenta = CuentaPublicitaria(id="123", nombre="Cuenta Principal", moneda="BOB")
    fila = {
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

    registro = mapear_fila_insight(fila, cuenta, {"camp_1": "OUTCOME_TRAFFIC"})

    assert registro.cuenta_publicitaria == "123"
    assert registro.perfil_unidad == "Cuenta Principal"
    assert registro.fecha_publicacion == datetime.date(2026, 7, 1)
    assert registro.objetivo == "OUTCOME_TRAFFIC"
    assert registro.moneda == "BOB"
    assert registro.importe_gastado == 10.5
    assert registro.resultados == 25
    assert registro.id_campana_origen == "camp_1"
    assert registro.pagina_origen_id == ""


def test_mapear_fila_insight_incluye_pagina_origen_cuando_se_resolvio():
    cuenta = CuentaPublicitaria(id="123", nombre="Cuenta Principal", moneda="BOB")
    fila = {
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

    registro = mapear_fila_insight(fila, cuenta, {}, {"camp_1": "111222333"})

    assert registro.pagina_origen_id == "111222333"


def test_mapear_fila_insight_incluye_conversaciones_y_fechas_de_campana():
    cuenta = CuentaPublicitaria(id="123", nombre="Cuenta Principal", moneda="BOB")
    fila = {
        "campaign_id": "camp_1",
        "campaign_name": "Campaña WhatsApp",
        "spend": "10.5",
        "reach": "1000",
        "impressions": "1500",
        "clicks": "30",
        "ctr": "2.0",
        "cpc": "0.35",
        "date_start": "2026-07-01",
        "date_stop": "2026-07-01",
        "publisher_platform": "facebook",
        "actions": [{"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "9"}],
    }

    registro = mapear_fila_insight(
        fila,
        cuenta,
        {"camp_1": "OUTCOME_TRAFFIC"},
        fechas_por_campana={"camp_1": ("2026-07-01T00:00:00-0400", "2026-07-31T23:59:00-0400")},
    )

    assert registro.conversaciones_iniciadas == 9
    assert registro.fecha_inicio_campana == datetime.date(2026, 7, 1)
    assert registro.fecha_fin_campana == datetime.date(2026, 7, 31)


def test_mapear_fila_insight_sin_fecha_fin_configurada_queda_en_none():
    """Una campaña sin fecha de fin (corre hasta que se la pause a mano) no
    manda `stop_time` — no hay que inventarle una fecha."""
    cuenta = CuentaPublicitaria(id="123", nombre="Cuenta Principal", moneda="BOB")
    fila = {
        "campaign_id": "camp_1",
        "campaign_name": "Campaña continua",
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

    registro = mapear_fila_insight(
        fila, cuenta, {}, fechas_por_campana={"camp_1": ("2026-07-01T00:00:00-0400", None)}
    )

    assert registro.fecha_inicio_campana == datetime.date(2026, 7, 1)
    assert registro.fecha_fin_campana is None
