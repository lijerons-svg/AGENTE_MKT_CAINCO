"""Herramienta de verificación (no toca datos): muestra cómo quedarían
agrupados los perfiles por "unidad" y a qué unidad matchearía cada campaña
real de Meta Ads, para confirmar con datos reales antes de construir el
dashboard "Control de Contenido" sobre ese supuesto.

Uso:
    python -m marketing_analytics.verificar_unidades
"""
from __future__ import annotations

import click

from marketing_analytics.config.loader import load_config
from marketing_analytics.database.connection import get_connection
from marketing_analytics.dashboard.control_contenido.matching import emparejar_unidad_campana


@click.command()
@click.option("--config", "config_path", default="config.yaml", show_default=True)
def main(config_path: str) -> None:
    config = load_config(config_path)

    perfiles_por_unidad: dict[str, list[str]] = {}
    alias_a_unidad: dict[str, tuple[str, bool]] = {}
    for perfil in config.meta.organico.perfiles:
        perfiles_por_unidad.setdefault(perfil.unidad, []).append(
            f"{perfil.nombre} ({perfil.red.value})"
        )
        alias_a_unidad[perfil.alias_pauta] = (perfil.unidad, perfil.alias_pauta_generico)

    click.echo("=== Perfiles agrupados por unidad ===")
    for unidad, perfiles in perfiles_por_unidad.items():
        click.echo(f"{unidad}:")
        for p in perfiles:
            click.echo(f"  - {p}")

    click.echo("\n=== Campañas de Meta Ads -> unidad detectada ===")
    with get_connection(config.general.database_path) as conn:
        campanas = [
            fila["campana"]
            for fila in conn.execute(
                "SELECT DISTINCT campana FROM meta_ads ORDER BY campana"
            ).fetchall()
        ]

    if not campanas:
        click.echo("(no hay campañas en la base todavía)")
        return

    sin_match = []
    for campana in campanas:
        unidad = emparejar_unidad_campana(campana, alias_a_unidad)
        if unidad is None:
            sin_match.append(campana)
            click.echo(f"  [SIN MATCH] {campana}")
        else:
            click.echo(f"  {campana} -> {unidad}")

    if sin_match:
        click.echo(f"\n{len(sin_match)} campaña(s) sin unidad detectada (revisar arriba).")
    else:
        click.echo("\nTodas las campañas matchearon con alguna unidad.")


if __name__ == "__main__":
    main()
