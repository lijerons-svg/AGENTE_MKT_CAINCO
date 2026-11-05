import datetime
from unittest.mock import MagicMock

from marketing_analytics.config.schema import CuentaPublicitaria, MetaAdsConfig
from marketing_analytics.connectors.meta_ads.connector import MetaAdsConnector


def test_fetch_resuelve_pagina_origen_una_sola_vez_por_campana():
    """Varias filas diarias de la misma campaña no deben disparar una
    consulta de página de origen por cada una — solo una por campaña."""
    cuenta = CuentaPublicitaria(id="123", nombre="Cuenta Principal", moneda="BOB")
    config = MetaAdsConfig(cuentas=[cuenta])

    filas = [
        {
            "campaign_id": "camp_1", "campaign_name": "Boost automático", "spend": "5", "reach": "100",
            "impressions": "200", "clicks": "3", "ctr": "1.5", "cpc": "1.6",
            "date_start": "2026-07-01", "date_stop": "2026-07-01", "publisher_platform": "facebook", "actions": [],
        },
        {
            "campaign_id": "camp_1", "campaign_name": "Boost automático", "spend": "5", "reach": "100",
            "impressions": "200", "clicks": "3", "ctr": "1.5", "cpc": "1.6",
            "date_start": "2026-07-02", "date_stop": "2026-07-02", "publisher_platform": "facebook", "actions": [],
        },
    ]

    cliente = MagicMock()
    cliente.obtener_objetivos_campanas.return_value = {}
    cliente.obtener_fechas_campanas.return_value = {}
    cliente.obtener_insights_campana.return_value = filas
    cliente.obtener_pagina_origen_campana.return_value = "111222333"

    conector = MetaAdsConnector(config, access_token="tok", api_version="v21.0", cliente=cliente)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 2))

    assert cliente.obtener_pagina_origen_campana.call_count == 1
    assert all(r.pagina_origen_id == "111222333" for r in registros)


def test_fetch_propaga_fechas_de_campana_a_cada_fila():
    cuenta = CuentaPublicitaria(id="123", nombre="Cuenta Principal", moneda="BOB")
    config = MetaAdsConfig(cuentas=[cuenta])

    filas = [
        {
            "campaign_id": "camp_1", "campaign_name": "Campaña Julio", "spend": "5", "reach": "100",
            "impressions": "200", "clicks": "3", "ctr": "1.5", "cpc": "1.6",
            "date_start": "2026-07-01", "date_stop": "2026-07-01", "publisher_platform": "facebook", "actions": [],
        },
    ]

    cliente = MagicMock()
    cliente.obtener_objetivos_campanas.return_value = {}
    cliente.obtener_fechas_campanas.return_value = {
        "camp_1": ("2026-07-01T00:00:00-0400", "2026-07-31T23:59:00-0400"),
    }
    cliente.obtener_insights_campana.return_value = filas
    cliente.obtener_pagina_origen_campana.return_value = ""

    conector = MetaAdsConnector(config, access_token="tok", api_version="v21.0", cliente=cliente)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert registros[0].fecha_inicio_campana == datetime.date(2026, 7, 1)
    assert registros[0].fecha_fin_campana == datetime.date(2026, 7, 31)


def test_fetch_parte_el_rango_en_meses_calendario():
    """Un backfill de varios meses no debe ir en una sola consulta de
    insights: fue justo lo que tumbó un backfill real por el límite de
    peticiones de Meta. Se pide mes por mes, sin que quien lo corra tenga
    que partir el rango a mano."""
    cuenta = CuentaPublicitaria(id="123", nombre="Cuenta Principal", moneda="BOB")
    config = MetaAdsConfig(cuentas=[cuenta])

    cliente = MagicMock()
    cliente.obtener_objetivos_campanas.return_value = {}
    cliente.obtener_fechas_campanas.return_value = {}
    cliente.obtener_insights_campana.return_value = []
    cliente.obtener_pagina_origen_campana.return_value = ""

    conector = MetaAdsConnector(config, access_token="tok", api_version="v21.0", cliente=cliente)
    conector.fetch(datetime.date(2026, 1, 15), datetime.date(2026, 3, 10))

    tramos = [llamada.args[1:] for llamada in cliente.obtener_insights_campana.call_args_list]
    assert tramos == [
        (datetime.date(2026, 1, 15), datetime.date(2026, 1, 31)),
        (datetime.date(2026, 2, 1), datetime.date(2026, 2, 28)),
        (datetime.date(2026, 3, 1), datetime.date(2026, 3, 10)),
    ]
