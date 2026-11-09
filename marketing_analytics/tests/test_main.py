from click.testing import CliRunner

import marketing_analytics.main as main_mod
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.database.connection import get_connection
from marketing_analytics.database.configuracion import obtener_ultima_fecha_hasta
from marketing_analytics.database.repository import ResultadoUpsert

_CONFIG_MINIMA = """
general:
  output_dir: "salida"
  database_path: "historico.db"
mailchimp:
  server_prefix: "us21"
  enabled: false
"""


class _ConectorFalso(BaseConnector):
    nombre = "falso"

    def fetch(self, desde, hasta):
        return ["dato"]

    def upsert(self, conn, datos):
        return ResultadoUpsert(nuevos=1, actualizados=0, descartados=0)


def _crear_config_y_env(tmp_path):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(_CONFIG_MINIMA, encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text("META_SYSTEM_USER_TOKEN=fake\nMAILCHIMP_API_KEY=fake\n", encoding="utf-8")
    return config_yaml, env_file


def _sin_publicacion_real(monkeypatch):
    """`publicar_github_pages` hace git add/commit/push sobre el repo real
    (resuelve su ruta desde __file__, no desde tmp_path). Sin este parche,
    cada test que corre main() termina empujando commits reales al repo —
    en la máquina de Sandy, eso significa pisar el dashboard público real
    con contenido de prueba. Bug real de QA detectado en el repo de
    desarrollo: una corrida completa de pytest generó 7 commits de ruido."""
    monkeypatch.setattr(main_mod, "publicar_github_pages", lambda ruta_html: None)


def test_main_genera_los_tres_archivos_y_sale_con_codigo_0(tmp_path, monkeypatch):
    config_yaml, env_file = _crear_config_y_env(tmp_path)
    monkeypatch.setattr(main_mod, "construir_conectores_activos", lambda config, secrets: [_ConectorFalso()])
    monkeypatch.chdir(tmp_path)
    _sin_publicacion_real(monkeypatch)

    runner = CliRunner()
    resultado = runner.invoke(
        main_mod.main,
        ["--config", str(config_yaml), "--env", str(env_file), "--desde", "2026-07-01", "--hasta", "2026-07-31"],
    )

    assert resultado.exit_code == 0, resultado.output
    assert (tmp_path / "salida" / "Historico_RRSS.xlsx").exists()
    assert (tmp_path / "salida" / "Dashboard.html").exists()
    assert (tmp_path / "salida" / "Log_Ejecucion.txt").exists()
    assert "Estado: exitoso" in resultado.output
    assert "Nuevos: 1" in resultado.output


def test_main_solo_mailchimp_configurado_no_exige_token_de_meta(tmp_path, monkeypatch):
    """Caso real de QA: activar solo Mailchimp (fase 1), sin META_SYSTEM_USER_TOKEN
    en el .env porque Meta todavía no se configuró — no debe fallar."""
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(
        'general:\n  output_dir: "salida"\n  database_path: "historico.db"\n'
        'mailchimp:\n  server_prefix: "us5"\n  enabled: true\n',
        encoding="utf-8",
    )
    env_file = tmp_path / ".env"
    env_file.write_text("MAILCHIMP_API_KEY=fake\n", encoding="utf-8")
    monkeypatch.setattr(main_mod, "construir_conectores_activos", lambda config, secrets: [_ConectorFalso()])
    monkeypatch.chdir(tmp_path)
    _sin_publicacion_real(monkeypatch)

    runner = CliRunner()
    resultado = runner.invoke(
        main_mod.main,
        ["--config", str(config_yaml), "--env", str(env_file), "--desde", "2026-07-01", "--hasta", "2026-07-31"],
    )

    assert resultado.exit_code == 0, resultado.output


def test_main_meta_configurado_sin_token_muestra_error_claro_sin_traceback(tmp_path):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(
        'general:\n  output_dir: "salida"\n  database_path: "historico.db"\n'
        'mailchimp:\n  server_prefix: "us21"\n  enabled: false\n'
        'meta:\n  ads:\n    cuentas:\n      - id: "123"\n        nombre: "Cuenta X"\n        moneda: "BOB"\n',
        encoding="utf-8",
    )
    env_file = tmp_path / ".env"
    env_file.write_text("MAILCHIMP_API_KEY=fake\n", encoding="utf-8")

    runner = CliRunner()
    resultado = runner.invoke(main_mod.main, ["--config", str(config_yaml), "--env", str(env_file)])

    assert resultado.exit_code == 1
    assert "Error de configuración" in resultado.output
    assert "META_SYSTEM_USER_TOKEN" in resultado.output
    assert "Traceback" not in resultado.output


def test_main_sin_conectores_activos_sale_con_codigo_1(tmp_path, monkeypatch):
    config_yaml, env_file = _crear_config_y_env(tmp_path)
    monkeypatch.setattr(main_mod, "construir_conectores_activos", lambda config, secrets: [])

    runner = CliRunner()
    resultado = runner.invoke(main_mod.main, ["--config", str(config_yaml), "--env", str(env_file)])

    assert resultado.exit_code == 1
    assert (tmp_path / "salida").exists() is False


class _ConectorQueFalla(BaseConnector):
    nombre = "falla"

    def fetch(self, desde, hasta):
        raise RuntimeError("API caída")

    def upsert(self, conn, datos):
        raise AssertionError("no debería llamarse")


def test_main_sin_fechas_continua_automaticamente_en_la_segunda_corrida(tmp_path, monkeypatch):
    """Caso real pedido por el usuario: correr sin --desde/--hasta debe
    "actualizar lo nuevo" solo, sin que el usuario tenga que pensar en
    rangos de fechas en cada corrida."""
    config_yaml, env_file = _crear_config_y_env(tmp_path)
    monkeypatch.setattr(main_mod, "construir_conectores_activos", lambda config, secrets: [_ConectorFalso()])
    monkeypatch.chdir(tmp_path)
    _sin_publicacion_real(monkeypatch)

    runner = CliRunner()
    primera = runner.invoke(main_mod.main, ["--config", str(config_yaml), "--env", str(env_file)])
    segunda = runner.invoke(main_mod.main, ["--config", str(config_yaml), "--env", str(env_file)])

    assert primera.exit_code == 0, primera.output
    assert segunda.exit_code == 0, segunda.output
    assert "Estado: exitoso" in segunda.output


def test_main_con_todo_fallido_sale_con_codigo_1_pero_igual_genera_reportes(tmp_path, monkeypatch):
    config_yaml, env_file = _crear_config_y_env(tmp_path)
    monkeypatch.setattr(main_mod, "construir_conectores_activos", lambda config, secrets: [_ConectorQueFalla()])
    monkeypatch.chdir(tmp_path)
    _sin_publicacion_real(monkeypatch)

    runner = CliRunner()
    resultado = runner.invoke(
        main_mod.main,
        ["--config", str(config_yaml), "--env", str(env_file), "--desde", "2026-07-01", "--hasta", "2026-07-31"],
    )

    assert resultado.exit_code == 1
    assert "Estado: fallido" in resultado.output
    assert (tmp_path / "salida" / "Log_Ejecucion.txt").exists()


def test_main_con_errores_no_avanza_el_checkpoint(tmp_path, monkeypatch):
    """Caso real de QA: durante un corte de token de Meta, cada corrida
    fallida igual avanzaba el checkpoint ("ultima_fecha_hasta") — la
    ventana de fechas nunca se volvía a pedir y esos datos se perdían para
    siempre, aunque el token se renovara después. Una corrida con errores
    no debe mover el checkpoint, para que la siguiente corrida reintente
    el mismo rango en vez de saltearlo."""
    config_yaml, env_file = _crear_config_y_env(tmp_path)
    monkeypatch.setattr(main_mod, "construir_conectores_activos", lambda config, secrets: [_ConectorQueFalla()])
    monkeypatch.chdir(tmp_path)
    _sin_publicacion_real(monkeypatch)

    runner = CliRunner()
    runner.invoke(
        main_mod.main,
        ["--config", str(config_yaml), "--env", str(env_file), "--desde", "2026-07-01", "--hasta", "2026-07-31"],
    )

    with get_connection(str(tmp_path / "historico.db")) as conn:
        assert obtener_ultima_fecha_hasta(conn) is None

    # Sin --desde/--hasta, la siguiente corrida automática debe seguir
    # pidiendo desde el arranque por defecto (no hay checkpoint que seguir).
    monkeypatch.setattr(main_mod, "construir_conectores_activos", lambda config, secrets: [_ConectorFalso()])
    segunda = runner.invoke(main_mod.main, ["--config", str(config_yaml), "--env", str(env_file)])
    assert segunda.exit_code == 0, segunda.output
    assert "Estado: exitoso" in segunda.output

    with get_connection(str(tmp_path / "historico.db")) as conn:
        assert obtener_ultima_fecha_hasta(conn) is not None
