"""Herramienta de diagnóstico (no toca datos): prueba, una por una, cada
nombre candidato de métrica de "alcance" de Facebook contra un post real y
muestra cuál responde con un valor y cuál viene vacía.

Existe porque Meta deprecó `post_impressions_unique` (alcance orgánico
total) en v25 y lo reemplazó por métricas de "media views" — pero el nombre
exacto del reemplazo a nivel de post no está claro en la documentación y
Meta descarta en silencio los nombres que no reconoce (responde 200 sin esa
métrica, en vez de un error). Sin este script, la única forma de saber cuál
funciona es mirar columnas en cero en el Excel final.

Usa el token del .env (el mismo del pipeline) y hace pocas llamadas: una
para encontrar un post reciente por Página, más una por candidato.

Uso:
    python -m marketing_analytics.verificar_metricas_alcance
    python -m marketing_analytics.verificar_metricas_alcance --perfil cainco_bolivia
"""
from __future__ import annotations

import datetime

import click

from marketing_analytics.config.loader import load_config, load_secrets
from marketing_analytics.config.schema import Red
from marketing_analytics.connectors.http_utils import ApiError
from marketing_analytics.connectors.meta_organico.client import MetaOrganicoClient

# Candidatos encontrados en la documentación de Meta y en changelogs de
# terceros (Sprout Social, Fivetran, Databox) como reemplazo de
# `post_impressions_unique`. Se prueban todos porque Meta no documenta con
# claridad cuál aplica a nivel de post.
_CANDIDATOS_ALCANCE = (
    "post_total_media_view_unique",
    "post_media_view_unique",
    "post_unique_media_view",
    "post_total_media_views_unique",
    "post_impressions_unique",
    # Estos tres no son alcance (cuentan visualizaciones, no usuarios
    # únicos), pero se prueban para descartar que sean algo distinto de
    # post_media_view, que ya usamos como Visualizaciones.
    "post_views",
    "post_unique_views",
    "post_views_unique",
)


@click.command()
@click.option("--config", "config_path", default="config.yaml", show_default=True)
@click.option("--env", "env_path", default=None)
@click.option(
    "--perfil",
    "perfil_id",
    default=None,
    help="id del perfil de Facebook a usar (por defecto, el primero de config.yaml)",
)
@click.option("--dias", default=30, show_default=True, help="Días hacia atrás para buscar un post")
def main(config_path: str, env_path: str | None, perfil_id: str | None, dias: int) -> None:
    config = load_config(config_path)
    secrets = load_secrets(env_path)

    perfiles_fb = [p for p in config.meta.organico.perfiles if p.red == Red.FACEBOOK]
    if perfil_id:
        perfiles_fb = [p for p in perfiles_fb if p.id == perfil_id]
    if not perfiles_fb:
        click.echo("No hay perfiles de Facebook que coincidan en config.yaml.", err=True)
        raise SystemExit(1)

    perfil = perfiles_fb[0]
    cliente = MetaOrganicoClient(secrets.meta_system_user_token, config.meta.api_version)

    hasta = datetime.date.today()
    desde = hasta - datetime.timedelta(days=dias)

    click.echo(f"Perfil: {perfil.nombre} (page_id {perfil.page_id})")
    token_pagina = cliente.obtener_token_de_pagina(perfil.page_id)
    posts = cliente.obtener_posts_pagina(perfil.page_id, desde, hasta, token=token_pagina)
    if not posts:
        click.echo(
            f"No se encontraron posts entre {desde} y {hasta}. Probá con --dias mayor "
            "o con otro --perfil.",
            err=True,
        )
        raise SystemExit(1)

    post_id = posts[0]["id"]
    click.echo(f"Post de prueba: {post_id} ({posts[0].get('created_time', 'sin fecha')})\n")

    # Referencia de control: una métrica que YA sabemos que funciona, para
    # distinguir "este nombre no existe" de "este post no tiene insights".
    click.echo("=== Métricas de referencia (deben responder) ===")
    for metrica in ("post_media_view", "post_reactions_by_type_total"):
        _probar(cliente, post_id, metrica, token_pagina)

    click.echo("\n=== Candidatos de alcance ===")
    funcionan = []
    for metrica in _CANDIDATOS_ALCANCE:
        if _probar(cliente, post_id, metrica, token_pagina):
            funcionan.append(metrica)

    click.echo("")
    if funcionan:
        click.echo(f"Candidato(s) que SÍ responden: {', '.join(funcionan)}")
        click.echo("Pasar este nombre para usarlo como 'Alcance' de Facebook.")
    else:
        click.echo(
            "Ningún candidato respondió: el alcance orgánico de Facebook no está "
            "disponible en esta versión de API con este token."
        )


def _probar(
    cliente: MetaOrganicoClient, post_id: str, metrica: str, token: str | None
) -> bool:
    """Devuelve True si la métrica respondió con algún valor."""
    try:
        resultado = cliente.obtener_insights_con_fallback(post_id, (metrica,), token=token)
    except ApiError as error:
        click.echo(f"  {metrica}: ERROR ({error})")
        return False

    if metrica in resultado:
        click.echo(f"  {metrica}: OK -> {resultado[metrica]}")
        return True
    click.echo(f"  {metrica}: vacía (Meta no la reconoce o no hay dato)")
    return False


if __name__ == "__main__":
    main()
