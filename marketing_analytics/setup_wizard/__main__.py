"""Asistente de configuración interactivo — pide tokens/IDs, los valida
contra las APIs oficiales en vivo, y genera/actualiza config.yaml y .env.
Se puede correr varias veces: cada corrida solo toca lo que se le pida,
sin pisar lo ya configurado.

Uso:
    python -m marketing_analytics.setup_wizard
"""
from __future__ import annotations

from pathlib import Path

import click
from pydantic import ValidationError

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.setup_wizard.prompts import (
    preguntar_mailchimp,
    preguntar_meta_ads,
    preguntar_meta_organico,
)
from marketing_analytics.setup_wizard.validators import validar_token_meta
from marketing_analytics.setup_wizard.writer import cargar_config, guardar_config, guardar_secreto


def _guardar_o_avisar(fn, *args) -> None:
    """Escribe config.yaml/.env; si el archivo está bloqueado (típico de
    OneDrive sincronizando, o el archivo abierto en otro programa) avisa
    claro en vez de dejar escapar un traceback de Windows."""
    try:
        fn(*args)
    except PermissionError as error:
        click.echo(
            click.style(
                f"\n✗ No se pudo escribir el archivo ({error}).\n"
                "Puede estar bloqueado por OneDrive sincronizando, o abierto en otro "
                "programa (Excel, un editor). Cerrá esos programas — o pausá la "
                "sincronización de OneDrive — e intentá de nuevo.",
                fg="red",
            )
        )
        raise SystemExit(1)


@click.command()
@click.option("--config", "config_path", default="config.yaml", show_default=True)
@click.option("--env", "env_path", default=".env", show_default=True)
def main(config_path: str, env_path: str) -> None:
    ruta_config = Path(config_path)
    ruta_env = Path(env_path)
    config = cargar_config(ruta_config)

    click.echo("=== Asistente de configuración — Marketing Analytics ===\n")

    if click.confirm("¿Configurar Mailchimp?", default=not config["mailchimp"]["server_prefix"]):
        api_key, datacenter = preguntar_mailchimp()
        _guardar_o_avisar(guardar_secreto, ruta_env, "MAILCHIMP_API_KEY", api_key)
        config["mailchimp"]["server_prefix"] = datacenter
        config["mailchimp"]["enabled"] = True

    hay_meta_configurado = bool(
        config["meta"]["ads"]["cuentas"] or config["meta"]["organico"]["perfiles"]
    )
    if click.confirm("\n¿Configurar algo de Meta (Ads y/o Orgánico)?", default=hay_meta_configurado):
        token = click.prompt("\nSystem User Access Token de Meta", hide_input=True)
        click.echo("Validando token...")
        ok, info = validar_token_meta(token, config["meta"]["api_version"])
        if not ok:
            click.echo(click.style(f"✗ {info}", fg="red"))
            raise SystemExit(1)
        click.echo(click.style(f"✓ Token válido ({info})", fg="green"))
        _guardar_o_avisar(guardar_secreto, ruta_env, "META_SYSTEM_USER_TOKEN", token)

        if click.confirm("\n¿Configurar Meta Ads?", default=bool(config["meta"]["ads"]["cuentas"])):
            config["meta"]["ads"]["cuentas"] = preguntar_meta_ads(
                token, config["meta"]["api_version"], config["meta"]["ads"]["cuentas"]
            )

        if click.confirm(
            "\n¿Configurar Meta Orgánico?", default=bool(config["meta"]["organico"]["perfiles"])
        ):
            config["meta"]["organico"]["perfiles"] = preguntar_meta_organico(
                token, config["meta"]["api_version"], config["meta"]["organico"]["perfiles"]
            )

    try:
        AppConfig.model_validate(config)
    except ValidationError as error:
        click.echo(click.style(f"\n✗ La configuración resultante no es válida:\n{error}", fg="red"))
        raise SystemExit(1)

    _guardar_o_avisar(guardar_config, ruta_config, config)
    click.echo(f"\n✓ {ruta_config} actualizado.")
    click.echo(f"✓ {ruta_env} actualizado (secretos — no se muestran ni se commitean).")
    click.echo("\nProbá con un rango chico primero, por ejemplo los últimos 7 días:")
    click.echo("  python -m marketing_analytics.main --desde AAAA-MM-DD --hasta AAAA-MM-DD")


if __name__ == "__main__":
    main()
