"""Script de un solo uso (manual): consigue el access token de LinkedIn.

A diferencia de Meta (token de sistema permanente) o SharePoint (client
credentials, sin login humano), la Community Management API de LinkedIn
solo da acceso a los datos de una organización mediante OAuth autorizado
por una persona administradora de esa página — no existe un modo
"aplicación sola" para esto. Por eso esto no es parte del pipeline
automático: se corre a mano, una vez, y de nuevo cada vez que el token
venza (~60 días, ver "Duración del token de acceso" en la app de LinkedIn).

Uso:
    python -m marketing_analytics.connectors.linkedin.obtener_token

Requiere en el .env:
    LINKEDIN_CLIENT_ID
    LINKEDIN_CLIENT_SECRET

Y que la URL de redireccionamiento de la app en LinkedIn Developers sea
exactamente la misma que REDIRECT_URI acá abajo.
"""
from __future__ import annotations

import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv, set_key

PUERTO = 8765
REDIRECT_URI = f"http://localhost:{PUERTO}/callback"
SCOPES = "r_organization_social rw_organization_admin"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"


class _ManejadorCallback(BaseHTTPRequestHandler):
    codigo: str | None = None
    state_esperado: str = ""

    def do_GET(self) -> None:  # noqa: N802 (nombre fijado por BaseHTTPRequestHandler)
        partes = urlparse(self.path)
        if partes.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(partes.query)
        error = params.get("error", [None])[0]
        state_recibido = params.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if error:
            mensaje = params.get("error_description", [error])[0]
            self.wfile.write(
                f"<h1>LinkedIn rechazó la autorización</h1><p>{mensaje}</p>"
                "<p>Podés cerrar esta pestaña y volver a la terminal.</p>".encode("utf-8")
            )
            return

        if state_recibido != _ManejadorCallback.state_esperado:
            self.wfile.write(
                "<h1>Respuesta inesperada</h1><p>El 'state' no coincide — por seguridad, "
                "no se continúa. Volvé a correr el script.</p>".encode("utf-8")
            )
            return

        _ManejadorCallback.codigo = params.get("code", [None])[0]
        self.wfile.write(
            "<h1>Listo</h1><p>Ya podés cerrar esta pestaña y volver a la terminal.</p>".encode(
                "utf-8"
            )
        )

    def log_message(self, format: str, *args) -> None:  # silencia el log por request del server
        pass


def main() -> None:
    env_path = Path(".env")
    load_dotenv(dotenv_path=env_path if env_path.exists() else None)

    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print(
            "Error: falta LINKEDIN_CLIENT_ID y/o LINKEDIN_CLIENT_SECRET en el .env "
            "(los sacás de la pestaña Autenticación de tu app en LinkedIn Developers).",
            file=sys.stderr,
        )
        sys.exit(1)

    state = secrets.token_urlsafe(16)
    _ManejadorCallback.state_esperado = state
    url_autorizacion = AUTH_URL + "?" + urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "state": state,
        }
    )

    servidor = HTTPServer(("localhost", PUERTO), _ManejadorCallback)
    hilo = threading.Thread(target=servidor.handle_request, daemon=True)
    hilo.start()

    print("Abriendo el navegador para que inicies sesión en LinkedIn y aceptes los permisos...")
    print(f"Si no se abre solo, pegá esta URL en el navegador:\n{url_autorizacion}\n")
    webbrowser.open(url_autorizacion)

    hilo.join(timeout=180)
    servidor.server_close()

    if not _ManejadorCallback.codigo:
        print(
            "No llegó ninguna autorización en 3 minutos (o falló). Volvé a correr el script.",
            file=sys.stderr,
        )
        sys.exit(1)

    respuesta = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _ManejadorCallback.codigo,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    if respuesta.status_code != 200:
        print(f"LinkedIn rechazó el canje del código: {respuesta.status_code} {respuesta.text}", file=sys.stderr)
        sys.exit(1)

    datos = respuesta.json()
    access_token = datos["access_token"]
    expira_en_dias = datos.get("expires_in", 0) // 86400
    refresh_token = datos.get("refresh_token")

    if env_path.exists():
        set_key(str(env_path), "LINKEDIN_ACCESS_TOKEN", access_token)
        if refresh_token:
            set_key(str(env_path), "LINKEDIN_REFRESH_TOKEN", refresh_token)
        print(f"Listo: LINKEDIN_ACCESS_TOKEN guardado en {env_path}.")
    else:
        print("No encontré un .env en esta carpeta — copiá esto a mano:")
        print(f"LINKEDIN_ACCESS_TOKEN={access_token}")
        if refresh_token:
            print(f"LINKEDIN_REFRESH_TOKEN={refresh_token}")

    print(f"Vence en ~{expira_en_dias} días. Volvé a correr este script antes de esa fecha.")
    if refresh_token:
        print(
            "Tu app también dio un refresh_token — más adelante lo podemos usar para "
            "renovar sin tener que iniciar sesión de nuevo cada vez."
        )


if __name__ == "__main__":
    main()
