"""Cliente delgado sobre Microsoft Graph API (oficial) para leer el Excel del
calendario de publicaciones desde SharePoint, sin necesitar Excel instalado.

Flujo: token (client credentials) -> resolver site -> resolver archivo ->
leer el rango usado de la hoja como filas ya emparejadas con su encabezado.
"""
from __future__ import annotations

import re

from marketing_analytics.connectors.http_utils import ApiError, solicitar

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _normalizar_encabezado(valor: str) -> str:
    texto = valor.strip().lower().replace("/", " ")
    texto = re.sub(r"[^a-z0-9áéíóúñ ]", "", texto)
    return re.sub(r"\s+", "_", texto).strip("_")


def _encontrar_fila_encabezados(valores: list[list]) -> int:
    """`usedRange` puede incluir filas por encima del encabezado real (título,
    banner, filas en blanco con formato aplicado) — se busca la fila cuya
    primera celda sea "id" en vez de asumir que es siempre la fila 0; si
    ninguna calza, se cae de vuelta a esa fila 0 (caso simple sin banner)."""
    for indice, fila in enumerate(valores):
        primera_celda = str(fila[0]).strip().lower() if fila else ""
        if primera_celda == "id":
            return indice
    return 0


class CalendarioSharePointClient:
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        sharepoint_hostname: str,
        site_path: str,
        file_name: str,
        sheet_name: str,
    ):
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._hostname = sharepoint_hostname
        self._site_path = site_path
        self._file_name = file_name
        self._sheet_name = sheet_name

    def _obtener_token(self) -> str:
        data = solicitar(
            "POST",
            f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
        )
        return data["access_token"]

    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def _resolver_site_id(self, token: str) -> str:
        data = solicitar(
            "GET",
            f"{_GRAPH_BASE}/sites/{self._hostname}:{self._site_path}",
            headers=self._headers(token),
        )
        return data["id"]

    def _resolver_item_id(self, token: str, site_id: str) -> str:
        """No asume que el archivo está en la raíz de la biblioteca por
        defecto (caso real: `drive/root:/{nombre}` devolvió 404 porque el
        archivo vive en una subcarpeta, ej. "Documentos compartidos") — lo
        busca por nombre en todo el drive, que sí encuentra subcarpetas."""
        data = solicitar(
            "GET",
            f"{_GRAPH_BASE}/sites/{site_id}/drive/root/search(q='{self._file_name}')",
            headers=self._headers(token),
        )
        for item in data.get("value", []):
            if item.get("name") == self._file_name:
                return item["id"]
        raise ApiError(
            f"No se encontró '{self._file_name}' en el drive del sitio de SharePoint"
        )

    def obtener_filas_calendario(self) -> list[dict]:
        """Devuelve cada fila de la hoja como dict {encabezado_normalizado: valor},
        salteando la fila de encabezados."""
        token = self._obtener_token()
        site_id = self._resolver_site_id(token)
        item_id = self._resolver_item_id(token, site_id)

        # `usedRange` a secas revienta con "RangeExceedsLimit" en hojas donde
        # se aplicó formato (relleno, bordes) a filas/columnas enteras muy
        # por fuera de los datos reales — Graph cuenta esas celdas vacías
        # con formato como parte del rango. `valuesOnly=true` le pide a
        # Graph que achique el rango a las celdas que realmente tienen
        # contenido, evitando el límite sin perder ninguna fila de datos.
        data = solicitar(
            "GET",
            f"{_GRAPH_BASE}/sites/{site_id}/drive/items/{item_id}"
            f"/workbook/worksheets('{self._sheet_name}')/usedRange(valuesOnly=true)",
            headers=self._headers(token),
        )
        valores = data.get("values", [])
        if not valores:
            return []

        inicio = _encontrar_fila_encabezados(valores)
        encabezados = [_normalizar_encabezado(str(c)) for c in valores[inicio]]
        return [
            dict(zip(encabezados, fila))
            for fila in valores[inicio + 1 :]
            if any(c not in (None, "") for c in fila)
        ]
