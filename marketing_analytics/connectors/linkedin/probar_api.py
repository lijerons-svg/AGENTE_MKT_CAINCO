"""Script de diagnóstico (manual, un solo uso): prueba contra la API real
de LinkedIn para ver el formato exacto de las respuestas antes de construir
el conector de verdad. No escribe nada en la base histórica ni en el Excel.

Uso:
    python -m marketing_analytics.connectors.linkedin.probar_api

Requiere LINKEDIN_ACCESS_TOKEN en el .env (lo pone obtener_token.py).
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

BASE = "https://api.linkedin.com"


def _generar_versiones_candidatas(meses: int = 24) -> tuple[str, ...]:
    """YYYYMM de los últimos `meses`, del más nuevo al más viejo. LinkedIn
    retira versiones viejas de los endpoints /rest/ (da 426
    NONEXISTENT_VERSION) sin avisar cuál es la vigente — se arma la lista a
    partir de la fecha de hoy en vez de dejarla fija, para no tener que
    actualizar este número a mano cada vez que pasan los meses."""
    hoy = datetime.date.today()
    versiones = []
    for i in range(meses):
        total = (hoy.year * 12 + hoy.month - 1) - i
        anio, mes = divmod(total, 12)
        versiones.append(f"{anio}{mes + 1:02d}")
    return tuple(versiones)


_VERSIONES_CANDIDATAS = _generar_versiones_candidatas()
_version_activa: str | None = None


def _headers(version: str) -> dict:
    return {
        "Authorization": f"Bearer {os.environ['LINKEDIN_ACCESS_TOKEN']}",
        "LinkedIn-Version": version,
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _resolver_version() -> str:
    """Prueba una llamada liviana a /rest/ con cada versión candidata hasta
    encontrar una que LinkedIn acepte (sea cual sea la respuesta: 200, 403,
    404... lo único descalificante es el 426 de versión retirada)."""
    global _version_activa
    if _version_activa:
        return _version_activa
    for version in _VERSIONES_CANDIDATAS:
        try:
            resp = requests.get(
                f"{BASE}/rest/posts",
                headers=_headers(version),
                params={"q": "author", "author": "urn:li:organization:1", "count": 1},
                timeout=30,
            )
        except requests.exceptions.RequestException:
            continue
        if resp.status_code != 426:
            print(f"(Usando LinkedIn-Version: {version})")
            _version_activa = version
            return version
    print(
        "Ninguna de las versiones probadas funcionó (todas dieron 426) — hay que sumar "
        "meses más nuevos a _VERSIONES_CANDIDATAS en este script."
    )
    _version_activa = _VERSIONES_CANDIDATAS[0]
    return _version_activa


def _get(path: str, params: dict | str | None = None) -> dict | None:
    version = _resolver_version() if path.startswith("/rest/") else "2.0.0"  # /v2/ no usa LinkedIn-Version
    headers = _headers(version) if path.startswith("/rest/") else {
        "Authorization": f"Bearer {os.environ['LINKEDIN_ACCESS_TOKEN']}"
    }
    print(f"\n{'=' * 70}\nGET {path} params={params}")
    try:
        # Cuando params es un string ya armado a mano (para la sintaxis de
        # listas de Rest.li 2.0.0, "campo=List(valor)", que requests
        # codificaría mal si se le pasa como dict) se manda tal cual.
        resp = requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=30)
        print(f"Status: {resp.status_code}")
        try:
            cuerpo = resp.json()
        except ValueError:
            print(resp.text[:2000])
            return None
        print(json.dumps(cuerpo, indent=2, ensure_ascii=False)[:12000])
        return cuerpo
    except requests.exceptions.RequestException as error:
        print(f"Error de red: {error}")
        return None


def main() -> None:
    # Mismo criterio que obtener_token.py: el .env de la carpeta desde la
    # que se corre el comando — así los dos scripts siempre miran el mismo
    # archivo, sin depender de la búsqueda automática de python-dotenv
    # (que busca a partir de la ubicación del script, no de la terminal).
    env_path = Path(".env")
    load_dotenv(dotenv_path=env_path if env_path.exists() else None)
    if not os.environ.get("LINKEDIN_ACCESS_TOKEN"):
        print(
            f"Falta LINKEDIN_ACCESS_TOKEN. Busqué el .env en: {env_path.resolve()} "
            "— ¿corriste obtener_token.py desde esta misma carpeta? Si no, corré primero "
            "obtener_token.py acá, o volvé a correr este script desde la carpeta donde está tu .env.",
            file=sys.stderr,
        )
        sys.exit(1)

    org_id = sys.argv[1] if len(sys.argv) > 1 else "1592889"  # CAINCO, visto en el dashboard de admin
    org_urn = f"urn:li:organization:{org_id}"

    print("1) Organizaciones que administra esta cuenta (para confirmar el ID real de CAINCO):")
    _get("/v2/organizationAcls", {"q": "roleAssignee", "role": "ADMINISTRATOR", "state": "APPROVED"})

    print("\n2) Últimos posts de la organización:")
    posts = _get("/rest/posts", {"author": org_urn, "q": "author", "count": 5})

    print("\n3) Estadísticas de seguidores:")
    _get("/rest/organizationalEntityFollowerStatistics", {"q": "organizationalEntity", "organizationalEntity": org_urn})

    print("\n4) Estadísticas de la página (vistas/visitantes):")
    _get("/rest/organizationPageStatistics", {"q": "organization", "organization": org_urn})

    # Ninguna de las dos llamadas de arriba trae métricas POR publicación
    # (me gusta, comentarios, compartidos, impresiones de CADA post) — para
    # eso hace falta apuntar a un post puntual. LinkedIn devuelve posts con
    # dos tipos de id distintos ("urn:li:share:..." y "urn:li:ugcPost:..."),
    # y la respuesta anterior sugiere que el parámetro "shares" solo acepta
    # el primero — se prueban los dos tipos, cada uno con el nombre de
    # parámetro que le corresponde.
    elementos = (posts or {}).get("elements", []) if posts else []
    post_share = next((e["id"] for e in elementos if e.get("id", "").startswith("urn:li:share:")), None)
    post_ugc = next((e["id"] for e in elementos if e.get("id", "").startswith("urn:li:ugcPost:")), None)

    def _probar_estadisticas_post(etiqueta: str, campo: str, post_id: str) -> None:
        # Rest.li 2.0.0 (header de arriba) codifica listas como
        # "campo=List(valor1,valor2)", con los paréntesis SIN codificar —
        # pasado como dict, requests codificaría también los paréntesis y
        # LinkedIn no lo reconocería como lista. Se arma la query a mano.
        query = (
            f"q=organizationalEntity&organizationalEntity={quote(org_urn, safe='')}"
            f"&{campo}=List({quote(post_id, safe='')})"
        )
        print(f"\n{etiqueta} (post {post_id}, parámetro '{campo}'):")
        _get("/rest/organizationalEntityShareStatistics", query)

    if post_share:
        _probar_estadisticas_post("5a) Estadísticas de un post tipo 'share'", "shares", post_share)
    if post_ugc:
        _probar_estadisticas_post("5b) Estadísticas de un post tipo 'ugcPost'", "ugcPosts", post_ugc)
    if not post_share and not post_ugc:
        print("\n(No se pudo sacar ningún post_id de la llamada 2 para probar las estadísticas por post.)")


if __name__ == "__main__":
    main()
