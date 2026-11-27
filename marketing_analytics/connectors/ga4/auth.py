"""Autenticación con Google vía cuenta de servicio (OAuth2 JWT Bearer),
sin el SDK oficial de Google (pesado) — mismo patrón liviano que el resto
de los conectores (ver http_utils.solicitar).

El import de `cryptography` está DENTRO de `_firmar_assertion`, a propósito:
así, un entorno con esa librería ausente o rota solo falla cuando de verdad
se intenta autenticar contra Google, no con solo importar este módulo (o
`client.py`/`connector.py`, que lo importan a su vez) — permite, por
ejemplo, testear el resto del conector inyectando un `obtener_token_fn`
falso sin necesitar `cryptography` funcionando en esa máquina.
"""
from __future__ import annotations

import base64
import json
import time

from marketing_analytics.connectors.http_utils import solicitar

TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"


def _base64url(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _firmar_assertion(cuenta_servicio: dict) -> str:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    ahora = int(time.time())
    encabezado = {"alg": "RS256", "typ": "JWT"}
    cuerpo = {
        "iss": cuenta_servicio["client_email"],
        "scope": _SCOPE,
        "aud": TOKEN_URL,
        "iat": ahora,
        "exp": ahora + 3600,
    }
    segmento = (
        _base64url(json.dumps(encabezado, separators=(",", ":")).encode("utf-8"))
        + "."
        + _base64url(json.dumps(cuerpo, separators=(",", ":")).encode("utf-8"))
    )
    clave_privada = serialization.load_pem_private_key(
        cuenta_servicio["private_key"].encode("utf-8"), password=None
    )
    firma = clave_privada.sign(segmento.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    return f"{segmento}.{_base64url(firma)}"


def obtener_token(ruta_credenciales: str) -> str:
    """Pide un access_token de corta duración (1 hora) a Google, a partir
    del archivo .json de la cuenta de servicio descargado desde Google
    Cloud Console. No vale la pena cachear ese token: cada corrida de la
    automatización es un proceso nuevo, así que de todas formas hay que
    pedir uno al arrancar."""
    with open(ruta_credenciales, encoding="utf-8") as f:
        cuenta_servicio = json.load(f)

    assertion = _firmar_assertion(cuenta_servicio)
    data = solicitar(
        "POST",
        TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
    )
    return data["access_token"]
