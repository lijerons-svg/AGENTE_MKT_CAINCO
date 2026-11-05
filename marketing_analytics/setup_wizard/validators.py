"""Validaciones EN VIVO contra las APIs oficiales — el asistente de
configuración nunca escribe un token/ID en config.yaml/.env sin antes
confirmar que la propia API lo acepta.

Cada validador atrapa tanto errores de la API (`ApiError`, ej. key/token
rechazado) como errores de red (`requests.exceptions.RequestException`,
ej. DNS roto por un valor corrompido, sin conexión, proxy) — ninguno debe
dejar escapar un traceback crudo hacia la persona usando el asistente.
"""
from __future__ import annotations

import re

import requests

from marketing_analytics.connectors.http_utils import ApiError, solicitar

_ERRORES_DE_RED = (ApiError, requests.exceptions.RequestException)
_FORMATO_MAILCHIMP = re.compile(r"^[0-9a-f]{32}-[a-z]{2,3}\d{1,3}$")


def extraer_datacenter_mailchimp(api_key: str) -> str:
    return api_key.rsplit("-", 1)[-1]


def validar_mailchimp(api_key: str) -> tuple[bool, str]:
    if not _FORMATO_MAILCHIMP.match(api_key):
        return False, (
            "Esa key no tiene el formato esperado de Mailchimp (32 caracteres, un guion, "
            "y el datacenter, ej. '...f2da4-us5'). ¿Se pegó bien? Revisá que no haya "
            "caracteres de más ni de menos."
        )
    datacenter = extraer_datacenter_mailchimp(api_key)
    try:
        data = solicitar(
            "GET",
            f"https://{datacenter}.api.mailchimp.com/3.0/ping",
            auth=("anystring", api_key),
        )
    except _ERRORES_DE_RED as error:
        return False, f"Mailchimp rechazó la API key o no se pudo conectar: {error}"
    return True, data.get("health_status", "OK")


def validar_token_meta(token: str, api_version: str) -> tuple[bool, str]:
    try:
        data = solicitar(
            "GET",
            f"https://graph.facebook.com/{api_version}/me",
            params={"fields": "id,name", "access_token": token},
        )
    except _ERRORES_DE_RED as error:
        return False, f"Meta rechazó el token o no se pudo conectar: {error}"
    return True, data.get("name") or data.get("id", "token válido")


def validar_cuenta_publicitaria(
    token: str, api_version: str, account_id: str
) -> tuple[bool, str, str]:
    """Devuelve (ok, nombre_o_error, moneda). La moneda viene directo de Meta
    — nunca se le pide al usuario que la tipee, para no arriesgar un typo."""
    try:
        data = solicitar(
            "GET",
            f"https://graph.facebook.com/{api_version}/act_{account_id}",
            params={"fields": "name,account_status,currency", "access_token": token},
        )
    except _ERRORES_DE_RED as error:
        return False, f"No se pudo validar la cuenta act_{account_id}: {error}", ""
    return True, data.get("name", ""), data.get("currency", "")


def validar_pagina_facebook(token: str, api_version: str, page_id: str) -> tuple[bool, str]:
    try:
        data = solicitar(
            "GET",
            f"https://graph.facebook.com/{api_version}/{page_id}",
            params={"fields": "name", "access_token": token},
        )
    except _ERRORES_DE_RED as error:
        return False, f"No se pudo validar la Página {page_id}: {error}"
    return True, data.get("name", "")


def validar_cuenta_instagram(token: str, api_version: str, ig_user_id: str) -> tuple[bool, str]:
    try:
        data = solicitar(
            "GET",
            f"https://graph.facebook.com/{api_version}/{ig_user_id}",
            params={"fields": "username", "access_token": token},
        )
    except _ERRORES_DE_RED as error:
        return False, f"No se pudo validar la cuenta de Instagram {ig_user_id}: {error}"
    return True, data.get("username", "")
