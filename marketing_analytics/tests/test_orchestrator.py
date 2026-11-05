import datetime

from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.database.repository import ResultadoUpsert
from marketing_analytics.services.orchestrator import ejecutar

_DESDE = datetime.date(2026, 7, 1)
_HASTA = datetime.date(2026, 7, 31)


class _ConectorExitoso(BaseConnector):
    nombre = "falso_ok"

    def __init__(self, resultado: ResultadoUpsert):
        self._resultado = resultado

    def fetch(self, desde, hasta):
        return ["dato"] * self._resultado.total

    def upsert(self, conn, datos):
        return self._resultado


class _ConectorFallido(BaseConnector):
    nombre = "falso_error"

    def fetch(self, desde, hasta):
        raise RuntimeError("API caída")

    def upsert(self, conn, datos):
        raise AssertionError("no debería llamarse: fetch ya falló")


def test_todos_los_conectores_exitosos(conn):
    conectores = [
        _ConectorExitoso(ResultadoUpsert(nuevos=2, actualizados=1, descartados=0)),
        _ConectorExitoso(ResultadoUpsert(nuevos=0, actualizados=0, descartados=5)),
    ]

    resumen = ejecutar(conn, conectores, _DESDE, _HASTA)

    assert resumen.estado == "exitoso"
    assert resumen.errores == []
    assert resumen.resultado_total.nuevos == 2
    assert resumen.resultado_total.actualizados == 1
    assert resumen.resultado_total.descartados == 5

    fila = conn.execute(
        "SELECT * FROM ejecuciones WHERE id = ?", (resumen.ejecucion_id,)
    ).fetchone()
    assert fila["estado"] == "exitoso"
    assert fila["registros_descargados"] == 8
    assert fila["hora_fin"] is not None

    logs = conn.execute(
        "SELECT * FROM logs WHERE ejecucion_id = ?", (resumen.ejecucion_id,)
    ).fetchall()
    assert len(logs) == 2
    assert all(log["nivel"] == "INFO" for log in logs)


def test_un_conector_fallido_no_tumba_a_los_demas(conn):
    conectores = [
        _ConectorFallido(),
        _ConectorExitoso(ResultadoUpsert(nuevos=3, actualizados=0, descartados=0)),
    ]

    resumen = ejecutar(conn, conectores, _DESDE, _HASTA)

    assert resumen.estado == "parcial"
    assert len(resumen.errores) == 1
    assert "falso_error" in resumen.errores[0]
    assert resumen.resultado_total.nuevos == 3

    fila = conn.execute(
        "SELECT * FROM ejecuciones WHERE id = ?", (resumen.ejecucion_id,)
    ).fetchone()
    assert fila["estado"] == "parcial"

    logs = conn.execute(
        "SELECT * FROM logs WHERE ejecucion_id = ?", (resumen.ejecucion_id,)
    ).fetchall()
    niveles = {log["fuente"]: log["nivel"] for log in logs}
    assert niveles["falso_error"] == "ERROR"
    assert niveles["falso_ok"] == "INFO"


def test_todos_los_conectores_fallidos_da_estado_fallido(conn):
    conectores = [_ConectorFallido(), _ConectorFallido()]

    resumen = ejecutar(conn, conectores, _DESDE, _HASTA)

    assert resumen.estado == "fallido"
    assert resumen.resultado_total.total == 0
    assert len(resumen.errores) == 2
