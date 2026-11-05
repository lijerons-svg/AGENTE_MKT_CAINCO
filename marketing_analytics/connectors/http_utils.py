"""Cliente HTTP compartido: retry automático con backoff exponencial y
manejo de rate limits (429/5xx, respetando Retry-After). Usado por todos
los conectores — ningún conector debe llamar a `requests` directamente.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

ESTADOS_REINTENTABLES = {429, 500, 502, 503, 504}
TIMEOUT_SEGUNDOS = 30


class ApiError(RuntimeError):
    def __init__(self, mensaje: str, status_code: int | None = None, payload: str = ""):
        super().__init__(mensaje)
        self.status_code = status_code
        self.payload = payload


def _es_reintentable(excepcion: BaseException) -> bool:
    if isinstance(excepcion, ApiError):
        return excepcion.status_code in ESTADOS_REINTENTABLES
    return isinstance(excepcion, requests.exceptions.RequestException)


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception(_es_reintentable),
)
def solicitar(metodo: str, url: str, **kwargs: Any) -> dict:
    """Hace una request y devuelve el JSON. Reintenta con backoff exponencial
    ante errores transitorios (429/500/502/503/504) o de red, respetando el
    header Retry-After cuando el servidor lo manda."""
    kwargs.setdefault("timeout", TIMEOUT_SEGUNDOS)
    respuesta = requests.request(metodo, url, **kwargs)

    if respuesta.status_code in ESTADOS_REINTENTABLES:
        retry_after = respuesta.headers.get("Retry-After")
        if retry_after:
            try:
                segundos = float(retry_after)
                logger.warning(
                    "Rate limit de %s: esperando %.0fs antes de reintentar (Retry-After)",
                    url,
                    segundos,
                )
                time.sleep(segundos)
            except ValueError:
                pass
        raise ApiError(
            f"Error temporal {respuesta.status_code} en {url}",
            status_code=respuesta.status_code,
            payload=respuesta.text,
        )

    if not respuesta.ok:
        raise ApiError(
            f"Error {respuesta.status_code} en {url}: {respuesta.text}",
            status_code=respuesta.status_code,
            payload=respuesta.text,
        )

    return respuesta.json()
