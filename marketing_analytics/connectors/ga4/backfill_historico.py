"""Script de un solo uso (manual): trae un historial de GA4 más largo que
el que deja el checkpoint automático.

El pipeline normal (python -m marketing_analytics.main) usa un solo
checkpoint de fecha COMPARTIDO por todos los conectores (Meta, Mailchimp,
etc. — ver resolver_rango_automatico). Como ese checkpoint ya venía
avanzado cuando se activó GA4, la corrida normal solo trajo los últimos
días, no un historial completo — por eso el tab Web del dashboard
mostraba menos días que el widget de Site Kit de WordPress (que siempre
pide los últimos 28 días en vivo a Google, sin esta limitación).

Este script llama al mismo GA4Connector pero con un rango de fechas
elegido a mano, SIN tocar ese checkpoint compartido — así no se adelanta
ni se atrasa la fecha desde la que arrancan los demás conectores en la
próxima corrida normal. Es seguro correrlo las veces que haga falta: el
dedupe por uid solo actualiza una fila si cambió, nunca duplica.

Uso (desde la carpeta del proyecto, con el entorno ya configurado):
    python -m marketing_analytics.connectors.ga4.backfill_historico --dias 90
"""
from __future__ import annotations

import datetime

import click

from marketing_analytics.config.loader import load_config, load_secrets
from marketing_analytics.connectors.ga4.connector import GA4Connector
from marketing_analytics.database.connection import get_connection


@click.command()
@click.option(
    "--config", "config_path", default="config.yaml", show_default=True, help="Ruta a config.yaml"
)
@click.option(
    "--env", "env_path", default=None, help="Ruta a .env (por defecto, busca .env en el directorio actual)"
)
@click.option(
    "--dias", default=90, show_default=True, help="Cuántos días hacia atrás traer, contando desde hoy"
)
def backfill(config_path: str, env_path: str | None, dias: int) -> None:
    config = load_config(config_path)
    secrets = load_secrets(env_path)

    if not config.ga4.enabled or not config.ga4.propiedades:
        click.echo("ga4.enabled es false (o no hay propiedades) en config.yaml — no hay nada que traer.", err=True)
        return
    if not secrets.google_service_account_json_path:
        click.echo("Falta GOOGLE_SERVICE_ACCOUNT_JSON_PATH en el .env.", err=True)
        return

    conector = GA4Connector(config.ga4, secrets.google_service_account_json_path)
    hasta = datetime.date.today()
    desde = hasta - datetime.timedelta(days=dias)

    click.echo(f"Trayendo GA4 de {len(config.ga4.propiedades)} propiedad(es), desde {desde} hasta {hasta}...")
    with get_connection(config.general.database_path) as conn:
        datos = conector.fetch(desde, hasta)
        resultado = conector.upsert(conn, datos)

    click.echo(
        f"Listo. Nuevos: {resultado.nuevos} | Actualizados: {resultado.actualizados} | "
        f"Sin cambios: {resultado.descartados}"
    )
    click.echo("Corré tu reporte de siempre (el .bat) para que el dashboard publicado refleje este historial.")


if __name__ == "__main__":
    backfill()
