"""Solo prueba las partes puras de auth.py (sin cryptography) — firmar la
assertion de verdad requiere una clave privada real y una llamada real a
Google, así que _firmar_assertion/obtener_token no se testean acá (se
confía en la implementación, estándar de OAuth2 JWT Bearer); lo que sí se
puede probar sin tocar ninguna API externa es la codificación base64url."""
from marketing_analytics.connectors.ga4.auth import _base64url


def test_base64url_no_lleva_relleno_ni_caracteres_no_seguros_para_url():
    codificado = _base64url(b'{"alg":"RS256"}')

    assert "=" not in codificado
    assert "+" not in codificado
    assert "/" not in codificado
