import datetime
from types import SimpleNamespace

from marketing_analytics.reports_pptx.main import (
    _anuncios_destacados_por_unidad,
    _mes_anterior,
    _resolver_unidades,
)


def test_mes_anterior_cruza_de_enero_a_diciembre_del_anio_previo():
    assert _mes_anterior(datetime.date(2027, 1, 15)) == (2026, 12)


def test_mes_anterior_caso_normal():
    assert _mes_anterior(datetime.date(2026, 9, 7)) == (2026, 8)


def test_mes_anterior_primer_dia_del_mes():
    assert _mes_anterior(datetime.date(2026, 3, 1)) == (2026, 2)


_DISPONIBLES = ["Academy Cainco", "Acierta CAINCO", "Copa Cainco", "GS1 Bolivia"]


def test_resolver_unidades_sin_filtros_devuelve_todas():
    validas, no_encontradas = _resolver_unidades((), [], _DISPONIBLES)
    assert validas == _DISPONIBLES
    assert no_encontradas == []


def test_resolver_unidades_usa_lista_de_config_si_no_hay_cli():
    validas, no_encontradas = _resolver_unidades((), ["Academy Cainco", "GS1 Bolivia"], _DISPONIBLES)
    assert validas == ["Academy Cainco", "GS1 Bolivia"]
    assert no_encontradas == []


def test_resolver_unidades_cli_tiene_prioridad_sobre_config():
    validas, _ = _resolver_unidades(("Copa Cainco",), ["Academy Cainco"], _DISPONIBLES)
    assert validas == ["Copa Cainco"]


def test_resolver_unidades_avisa_las_que_no_existen_sin_romper_las_demas():
    validas, no_encontradas = _resolver_unidades((), ["Academy Cainco", "Unidad Inventada"], _DISPONIBLES)
    assert validas == ["Academy Cainco"]
    assert no_encontradas == ["Unidad Inventada"]


def _config_falsa(cuentas, perfiles):
    return SimpleNamespace(
        meta=SimpleNamespace(
            api_version="v25.0",
            ads=SimpleNamespace(cuentas=cuentas),
            organico=SimpleNamespace(perfiles=perfiles),
        )
    )


def test_anuncios_destacados_por_unidad_sin_cuentas_no_llama_a_la_api(monkeypatch):
    llamado = False

    def _falla_si_se_llama(*args, **kwargs):
        nonlocal llamado
        llamado = True

    monkeypatch.setattr("marketing_analytics.reports_pptx.main.obtener_insights_anuncios", _falla_si_se_llama)
    config = _config_falsa(cuentas=[], perfiles=[])
    resultado = _anuncios_destacados_por_unidad(config, SimpleNamespace(meta_system_user_token="tok"), 2026, 8)
    assert resultado == {}
    assert llamado is False


def test_anuncios_destacados_por_unidad_agrupa_por_alias_pauta(monkeypatch):
    cuenta = SimpleNamespace(id="123", nombre="Cuenta compartida")
    perfil_academy = SimpleNamespace(alias_pauta="ACADEMY", unidad="Academy Cainco", alias_pauta_generico=False)
    perfil_acierta = SimpleNamespace(alias_pauta="ACIERTA", unidad="Acierta CAINCO", alias_pauta_generico=False)
    config = _config_falsa(cuentas=[cuenta], perfiles=[perfil_academy, perfil_acierta])

    filas = [
        {"ad_id": "1", "campaign_name": "ACADEMY - Lanzamiento", "publisher_platform": "facebook", "actions": []},
        {"ad_id": "2", "campaign_name": "ACIERTA - Webinar", "publisher_platform": "instagram", "actions": []},
        {"ad_id": "3", "campaign_name": "Campaña sin alias conocido", "publisher_platform": "facebook", "actions": []},
    ]
    monkeypatch.setattr(
        "marketing_analytics.reports_pptx.main.obtener_insights_anuncios", lambda *a, **k: filas
    )
    monkeypatch.setattr(
        "marketing_analytics.reports_pptx.main.top_anuncios_destacados",
        lambda filas_unidad, token, api_version, cantidad=4: [{"ad_id": f["ad_id"]} for f in filas_unidad],
    )

    resultado = _anuncios_destacados_por_unidad(config, SimpleNamespace(meta_system_user_token="tok"), 2026, 8)

    assert resultado == {
        "Academy Cainco": [{"ad_id": "1"}],
        "Acierta CAINCO": [{"ad_id": "2"}],
    }


def test_anuncios_destacados_por_unidad_avisa_y_sigue_si_una_cuenta_falla(monkeypatch, capsys):
    cuenta_mala = SimpleNamespace(id="1", nombre="Cuenta rota")
    cuenta_buena = SimpleNamespace(id="2", nombre="Cuenta ok")
    perfil = SimpleNamespace(alias_pauta="ACADEMY", unidad="Academy Cainco", alias_pauta_generico=False)
    config = _config_falsa(cuentas=[cuenta_mala, cuenta_buena], perfiles=[perfil])

    def _insights(ad_account_id, *a, **k):
        if ad_account_id == "1":
            raise RuntimeError("token vencido")
        return [{"ad_id": "9", "campaign_name": "ACADEMY - Test", "publisher_platform": "facebook", "actions": []}]

    monkeypatch.setattr("marketing_analytics.reports_pptx.main.obtener_insights_anuncios", _insights)
    monkeypatch.setattr(
        "marketing_analytics.reports_pptx.main.top_anuncios_destacados",
        lambda filas_unidad, token, api_version, cantidad=4: [{"ad_id": f["ad_id"]} for f in filas_unidad],
    )

    resultado = _anuncios_destacados_por_unidad(config, SimpleNamespace(meta_system_user_token="tok"), 2026, 8)

    assert resultado == {"Academy Cainco": [{"ad_id": "9"}]}
    assert "Cuenta rota" in capsys.readouterr().err
