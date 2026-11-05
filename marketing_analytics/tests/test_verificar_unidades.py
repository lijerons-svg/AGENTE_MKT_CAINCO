import datetime

from click.testing import CliRunner

import marketing_analytics.verificar_unidades as verificar_mod
from marketing_analytics.database.connection import get_connection
from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro

_CONFIG = """
general:
  database_path: "{db_path}"
mailchimp:
  server_prefix: "us21"
  enabled: false
meta:
  organico:
    perfiles:
      - id: "p1"
        nombre: "Academy Cainco"
        unidad: "ACADEMY"
        red: "facebook"
        page_id: "123"
"""


def test_verificar_unidades_reporta_match_y_sin_match(tmp_path):
    db_path = tmp_path / "historico.db"
    with get_connection(str(db_path)) as conn:
        upsert_meta_ads(
            conn,
            [
                MetaAdsRegistro(
                    cuenta_publicitaria="act_1",
                    perfil_unidad="Cuenta X",
                    red="facebook",
                    campana="ENERO 2026 - ACADEMY - PRODUCTIVIDAD",
                    fecha_publicacion=datetime.date(2026, 1, 1),
                    objetivo="TRAFFIC",
                    moneda="BOB",
                    id_campana_origen="camp_1",
                ),
                MetaAdsRegistro(
                    cuenta_publicitaria="act_1",
                    perfil_unidad="Cuenta X",
                    red="facebook",
                    campana="CAMPAÑA SIN MARCA RECONOCIBLE",
                    fecha_publicacion=datetime.date(2026, 1, 2),
                    objetivo="TRAFFIC",
                    moneda="BOB",
                    id_campana_origen="camp_2",
                ),
            ],
        )

    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(
        _CONFIG.format(db_path=str(db_path).replace("\\", "/")), encoding="utf-8"
    )

    runner = CliRunner()
    resultado = runner.invoke(verificar_mod.main, ["--config", str(config_yaml)])

    assert resultado.exit_code == 0, resultado.output
    assert "ACADEMY:" in resultado.output
    assert "Academy Cainco (facebook)" in resultado.output
    assert "ENERO 2026 - ACADEMY - PRODUCTIVIDAD -> ACADEMY" in resultado.output
    assert "[SIN MATCH] CAMPAÑA SIN MARCA RECONOCIBLE" in resultado.output


def test_verificar_unidades_sin_campanas_no_falla(tmp_path):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(
        _CONFIG.format(db_path=str(tmp_path / "vacia.db").replace("\\", "/")), encoding="utf-8"
    )

    runner = CliRunner()
    resultado = runner.invoke(verificar_mod.main, ["--config", str(config_yaml)])

    assert resultado.exit_code == 0, resultado.output
    assert "no hay campañas" in resultado.output
