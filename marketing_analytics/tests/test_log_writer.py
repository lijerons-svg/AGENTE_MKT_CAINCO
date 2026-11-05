import datetime

from marketing_analytics.database.repository import ResultadoUpsert
from marketing_analytics.services.log_writer import escribir_log_ejecucion
from marketing_analytics.services.orchestrator import ejecutar
from marketing_analytics.tests.test_orchestrator import _ConectorExitoso, _ConectorFallido

_DESDE = datetime.date(2026, 7, 1)
_HASTA = datetime.date(2026, 7, 31)


def test_escribe_log_ejecucion_con_totales_y_por_conector(conn, tmp_path):
    conectores = [
        _ConectorExitoso(ResultadoUpsert(nuevos=2, actualizados=1, descartados=0)),
        _ConectorFallido(),
    ]
    resumen = ejecutar(conn, conectores, _DESDE, _HASTA)

    ruta = escribir_log_ejecucion(conn, resumen, tmp_path / "Log_Ejecucion.txt")

    contenido = ruta.read_text(encoding="utf-8")
    assert "Estado: parcial" in contenido
    assert "Registros nuevos: 2" in contenido
    assert "[OK] falso_ok" in contenido
    assert "[ERROR] falso_error" in contenido
    assert "--- Errores ---" in contenido
