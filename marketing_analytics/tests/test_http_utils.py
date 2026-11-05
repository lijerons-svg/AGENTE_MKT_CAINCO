import pytest
import responses

from marketing_analytics.connectors.http_utils import ApiError, solicitar

URL = "https://api.test/recurso"


@responses.activate
def test_reintenta_ante_error_temporal_y_luego_responde_ok(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda segundos: None)
    responses.add(responses.GET, URL, status=503)
    responses.add(responses.GET, URL, json={"ok": True}, status=200)

    resultado = solicitar("GET", URL)

    assert resultado == {"ok": True}
    assert len(responses.calls) == 2


@responses.activate
def test_agota_reintentos_y_lanza_apierror(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda segundos: None)
    for _ in range(5):
        responses.add(responses.GET, URL, status=500)

    with pytest.raises(ApiError):
        solicitar("GET", URL)

    assert len(responses.calls) == 5


@responses.activate
def test_error_no_reintentable_no_reintenta(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda segundos: None)
    responses.add(responses.GET, URL, status=404, json={"error": "not found"})

    with pytest.raises(ApiError):
        solicitar("GET", URL)

    assert len(responses.calls) == 1


@responses.activate
def test_respeta_retry_after_antes_de_reintentar(monkeypatch):
    esperas: list[float] = []
    monkeypatch.setattr("time.sleep", lambda segundos: esperas.append(segundos))
    responses.add(responses.GET, URL, status=429, headers={"Retry-After": "2"})
    responses.add(responses.GET, URL, json={"ok": True}, status=200)

    solicitar("GET", URL)

    assert 2.0 in esperas


@responses.activate
def test_avisa_por_log_cuando_espera_por_rate_limit(monkeypatch, caplog):
    """Caso real de QA: una espera larga por Retry-After sin ningún aviso
    en pantalla parece un cuelgue — se loguea para que quede claro por qué
    no hay actividad."""
    monkeypatch.setattr("time.sleep", lambda segundos: None)
    responses.add(responses.GET, URL, status=429, headers={"Retry-After": "1200"})
    responses.add(responses.GET, URL, json={"ok": True}, status=200)

    with caplog.at_level("WARNING"):
        solicitar("GET", URL)

    assert any("1200" in registro.getMessage() for registro in caplog.records)
