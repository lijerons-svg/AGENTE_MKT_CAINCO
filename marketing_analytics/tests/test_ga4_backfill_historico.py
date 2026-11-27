import datetime

from click.testing import CliRunner

import marketing_analytics.connectors.ga4.backfill_historico as backfill_mod
from marketing_analytics.database.repository import ResultadoUpsert

_CONFIG_GA4 = """
general:
  output_dir: "salida"
  database_path: "historico.db"
mailchimp:
  server_prefix: "us21"
  enabled: false
ga4:
  enabled: true
  propiedades:
    - unidad: "CAINCO Sitio Principal"
      property_id: "476689307"
"""

_CONFIG_SIN_GA4 = """
general:
  output_dir: "salida"
  database_path: "historico.db"
mailchimp:
  server_prefix: "us21"
  enabled: false
"""


def _crear_config_y_env(tmp_path, config_texto, con_credenciales=True):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(config_texto, encoding="utf-8")
    env_file = tmp_path / ".env"
    contenido = "GOOGLE_SERVICE_ACCOUNT_JSON_PATH=/ruta/falsa.json\n" if con_credenciales else ""
    env_file.write_text(contenido, encoding="utf-8")
    return config_yaml, env_file


class _GA4ConnectorFalso:
    llamadas_fetch = []

    def __init__(self, config, ruta_credenciales):
        self._config = config

    def fetch(self, desde, hasta):
        _GA4ConnectorFalso.llamadas_fetch.append((desde, hasta))
        return "datos-falsos"

    def upsert(self, conn, datos):
        return ResultadoUpsert(nuevos=3, actualizados=1, descartados=0)


def test_backfill_trae_el_rango_de_dias_pedido(tmp_path, monkeypatch):
    config_yaml, env_file = _crear_config_y_env(tmp_path, _CONFIG_GA4)
    monkeypatch.setattr(backfill_mod, "GA4Connector", _GA4ConnectorFalso)
    monkeypatch.chdir(tmp_path)
    _GA4ConnectorFalso.llamadas_fetch = []

    runner = CliRunner()
    resultado = runner.invoke(
        backfill_mod.backfill,
        ["--config", str(config_yaml), "--env", str(env_file), "--dias", "30"],
    )

    assert resultado.exit_code == 0, resultado.output
    assert "Nuevos: 3" in resultado.output
    assert len(_GA4ConnectorFalso.llamadas_fetch) == 1
    desde, hasta = _GA4ConnectorFalso.llamadas_fetch[0]
    assert hasta == datetime.date.today()
    assert desde == datetime.date.today() - datetime.timedelta(days=30)


def test_backfill_sin_ga4_habilitado_no_hace_nada(tmp_path, monkeypatch):
    config_yaml, env_file = _crear_config_y_env(tmp_path, _CONFIG_SIN_GA4)
    monkeypatch.setattr(backfill_mod, "GA4Connector", _GA4ConnectorFalso)
    monkeypatch.chdir(tmp_path)
    _GA4ConnectorFalso.llamadas_fetch = []

    runner = CliRunner()
    resultado = runner.invoke(
        backfill_mod.backfill, ["--config", str(config_yaml), "--env", str(env_file)]
    )

    assert resultado.exit_code == 0
    assert "no hay nada que traer" in resultado.output
    assert _GA4ConnectorFalso.llamadas_fetch == []


def test_backfill_sin_credenciales_avisa_claro(tmp_path, monkeypatch):
    config_yaml, env_file = _crear_config_y_env(tmp_path, _CONFIG_GA4, con_credenciales=False)
    monkeypatch.setattr(backfill_mod, "GA4Connector", _GA4ConnectorFalso)
    monkeypatch.chdir(tmp_path)
    _GA4ConnectorFalso.llamadas_fetch = []

    runner = CliRunner()
    resultado = runner.invoke(
        backfill_mod.backfill, ["--config", str(config_yaml), "--env", str(env_file)]
    )

    assert resultado.exit_code == 0
    assert "GOOGLE_SERVICE_ACCOUNT_JSON_PATH" in resultado.output
    assert _GA4ConnectorFalso.llamadas_fetch == []
