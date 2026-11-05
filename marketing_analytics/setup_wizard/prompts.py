"""Prompts interactivos del asistente — cada uno valida contra la API real
antes de aceptar el dato."""
from __future__ import annotations

import click

from marketing_analytics.setup_wizard.validators import (
    extraer_datacenter_mailchimp,
    validar_cuenta_instagram,
    validar_cuenta_publicitaria,
    validar_mailchimp,
    validar_pagina_facebook,
)


def preguntar_mailchimp() -> tuple[str, str]:
    """Devuelve (api_key, server_prefix) ya validados contra Mailchimp."""
    while True:
        api_key = click.prompt("API Key de Mailchimp", hide_input=True)
        click.echo("Validando contra Mailchimp...")
        ok, mensaje = validar_mailchimp(api_key)
        if ok:
            datacenter = extraer_datacenter_mailchimp(api_key)
            click.echo(click.style(f"✓ Mailchimp OK (datacenter: {datacenter}) — {mensaje}", fg="green"))
            return api_key, datacenter
        click.echo(click.style(f"✗ {mensaje}", fg="red"))
        if not click.confirm("¿Reintentar?", default=True):
            raise SystemExit(1)


def preguntar_meta_ads(token: str, api_version: str, existentes: list[dict]) -> list[dict]:
    cuentas = list(existentes)
    if cuentas:
        click.echo(f"Ya hay {len(cuentas)} cuenta(s) publicitaria(s) configurada(s):")
        for c in cuentas:
            click.echo(f"  - {c['id']} ({c['nombre']}, {c['moneda']})")

    while click.confirm("¿Agregar una cuenta publicitaria de Meta Ads?", default=not cuentas):
        account_id = click.prompt("ID de la cuenta publicitaria (sin 'act_')").strip()
        click.echo("Validando contra Meta...")
        ok, nombre_o_error, moneda = validar_cuenta_publicitaria(token, api_version, account_id)
        if not ok:
            click.echo(click.style(f"✗ {nombre_o_error}", fg="red"))
            continue
        click.echo(click.style(f"✓ Cuenta encontrada: '{nombre_o_error}' — moneda: {moneda}", fg="green"))
        nombre = click.prompt("Nombre para usar en los reportes", default=nombre_o_error)
        cuentas.append({"id": account_id, "nombre": nombre, "moneda": moneda})
    return cuentas


def preguntar_meta_organico(token: str, api_version: str, existentes: list[dict]) -> list[dict]:
    perfiles = list(existentes)
    if perfiles:
        click.echo(f"Ya hay {len(perfiles)} perfil(es) configurado(s):")
        for p in perfiles:
            click.echo(f"  - {p['id']} ({p['nombre']}, {p['red']})")

    while click.confirm(
        "¿Agregar un perfil de Meta Orgánico (Facebook o Instagram)?", default=not perfiles
    ):
        red = click.prompt("Red", type=click.Choice(["facebook", "instagram"]))
        clave = click.prompt("Identificador corto para este perfil (ej. 'marca_x_ig')").strip()
        click.echo("Validando contra Meta...")

        if red == "facebook":
            page_id = click.prompt("Page ID de Facebook").strip()
            ok, nombre_o_error = validar_pagina_facebook(token, api_version, page_id)
            entrada = {"id": clave, "red": red, "page_id": page_id}
        else:
            ig_user_id = click.prompt("Instagram Business Account ID").strip()
            ok, nombre_o_error = validar_cuenta_instagram(token, api_version, ig_user_id)
            entrada = {"id": clave, "red": red, "ig_user_id": ig_user_id}

        if not ok:
            click.echo(click.style(f"✗ {nombre_o_error}", fg="red"))
            continue

        click.echo(click.style(f"✓ Encontrado: '{nombre_o_error}'", fg="green"))
        entrada["nombre"] = click.prompt("Nombre para usar en los reportes", default=nombre_o_error)
        perfiles.append(entrada)
    return perfiles
