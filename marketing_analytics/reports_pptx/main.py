"""Herramienta aparte para generar el reporte PPT mensual, por unidad.

No es parte del pipeline automático de lunes/viernes — el reporte es
mensual, así que se corre a mano cuando el mes cierra:

    python -m marketing_analytics.reports_pptx.main
    python -m marketing_analytics.reports_pptx.main --anio 2026 --mes 8
    python -m marketing_analytics.reports_pptx.main --unidad "Academy Cainco"
"""
from __future__ import annotations

import datetime
import sys
import tempfile
from pathlib import Path

import click
from pydantic import ValidationError

from marketing_analytics.config.loader import load_config, load_secrets
from marketing_analytics.dashboard.control_contenido.data_builder import (
    construir_datos_control_contenido,
)
from marketing_analytics.dashboard.control_contenido.matching import emparejar_unidad_campana
from marketing_analytics.database.connection import get_connection
from marketing_analytics.reports_pptx import agregacion
from marketing_analytics.reports_pptx.competencia import obtener_competidor
from marketing_analytics.reports_pptx.generador import generar_pptx_mailchimp, generar_pptx_unidad
from marketing_analytics.reports_pptx.pauta_destacada import (
    obtener_insights_anuncios,
    top_anuncios_destacados,
)


def _mes_anterior(hoy: datetime.date) -> tuple[int, int]:
    primero_del_mes = hoy.replace(day=1)
    ultimo_del_mes_anterior = primero_del_mes - datetime.timedelta(days=1)
    return ultimo_del_mes_anterior.year, ultimo_del_mes_anterior.month


def _resolver_unidades(
    unidades_cli: tuple[str, ...], unidades_config: list[str], disponibles: list[str]
) -> tuple[list[str], list[str]]:
    """Prioridad: --unidad de la línea de comando > reportes_pptx.unidades
    de config.yaml > todas. Devuelve (unidades_validas, no_encontradas) —
    una unidad pedida que no existe se avisa, no rompe la corrida de las
    demás."""
    solicitadas = list(unidades_cli) or unidades_config or disponibles
    validas = [u for u in solicitadas if u in disponibles]
    no_encontradas = [u for u in solicitadas if u not in disponibles]
    return validas, no_encontradas


def _competidores_por_unidad(config, secrets, anio: int, mes: int) -> dict[str, list[dict]]:
    if not config.competencia.enabled or not config.competencia.perfiles:
        return {}
    desde = datetime.date(anio, mes, 1)
    hasta_dia = (datetime.date(anio, mes % 12 + 1, 1) if mes < 12 else datetime.date(anio + 1, 1, 1)) - datetime.timedelta(days=1)

    resultado: dict[str, list[dict]] = {}
    for perfil in config.competencia.perfiles:
        try:
            datos = obtener_competidor(
                perfil.facebook_page_alias,
                secrets.meta_system_user_token,
                config.meta.api_version,
                desde,
                hasta_dia,
            )
        except Exception as error:
            click.echo(f"  Aviso: no se pudo traer competencia '{perfil.nombre}' ({error})", err=True)
            continue
        resultado.setdefault(perfil.unidad, []).append(datos)
    return resultado


def _anuncios_destacados_por_unidad(config, secrets, anio: int, mes: int) -> dict[str, list[dict]]:
    """Trae insights a nivel de anuncio (no de campaña, distinto del
    pipeline automático) y arma el top 4 por unidad, matcheando campañas
    con el mismo alias_pauta que usa el dashboard — así una cuenta
    publicitaria que sirve a varias unidades no mezcla sus anuncios."""
    if not config.meta.ads.cuentas:
        return {}
    alias_a_unidad = {
        p.alias_pauta: (p.unidad, p.alias_pauta_generico) for p in config.meta.organico.perfiles
    }
    desde = datetime.date(anio, mes, 1)
    hasta_dia = (datetime.date(anio, mes % 12 + 1, 1) if mes < 12 else datetime.date(anio + 1, 1, 1)) - datetime.timedelta(days=1)

    filas_por_unidad: dict[str, list[dict]] = {}
    for cuenta in config.meta.ads.cuentas:
        try:
            filas = obtener_insights_anuncios(
                cuenta.id, secrets.meta_system_user_token, config.meta.api_version, desde, hasta_dia
            )
        except Exception as error:
            click.echo(f"  Aviso: no se pudo traer anuncios de la cuenta '{cuenta.nombre}' ({error})", err=True)
            continue
        for fila in filas:
            unidad = emparejar_unidad_campana(fila.get("campaign_name", ""), alias_a_unidad)
            if unidad:
                filas_por_unidad.setdefault(unidad, []).append(fila)

    resultado: dict[str, list[dict]] = {}
    for unidad, filas in filas_por_unidad.items():
        try:
            resultado[unidad] = top_anuncios_destacados(
                filas, secrets.meta_system_user_token, config.meta.api_version
            )
        except Exception as error:
            click.echo(f"  Aviso: no se pudo armar el top de pauta destacada de '{unidad}' ({error})", err=True)
    return resultado


@click.command()
@click.option("--config", "config_path", default="config.yaml", show_default=True, help="Ruta a config.yaml")
@click.option("--env", "env_path", default=None, help="Ruta a .env")
@click.option("--anio", "anio", default=None, type=int, help="Año del reporte (default: mes calendario anterior)")
@click.option("--mes", "mes", default=None, type=int, help="Mes del reporte, 1-12 (default: mes calendario anterior)")
@click.option(
    "--unidad", "unidades_filtro", multiple=True,
    help="Generar solo para esta unidad (repetible: --unidad X --unidad Y). Default: lista de config.yaml (reportes_pptx.unidades), o todas si esa lista está vacía.",
)
def main(config_path: str, env_path: str | None, anio: int | None, mes: int | None, unidades_filtro: tuple[str, ...]) -> None:
    try:
        config = load_config(config_path)
        secrets = load_secrets(env_path)
    except (FileNotFoundError, ValidationError) as error:
        click.echo(f"Error de configuración: {error}", err=True)
        sys.exit(1)

    if anio is None or mes is None:
        anio, mes = _mes_anterior(datetime.date.today())

    output_dir = Path(config.general.output_dir) / "reportes_ppt"
    output_dir.mkdir(parents=True, exist_ok=True)

    with get_connection(config.general.database_path) as conn:
        datos = construir_datos_control_contenido(conn, config)

    todas_las_unidades = sorted(datos["unidades"].keys())
    unidades, no_encontradas = _resolver_unidades(unidades_filtro, config.reportes_pptx.unidades, todas_las_unidades)
    if no_encontradas:
        click.echo(
            f"Aviso: no existen en config.yaml (se omiten): {', '.join(no_encontradas)}. "
            f"Unidades disponibles: {', '.join(todas_las_unidades)}",
            err=True,
        )
    if not unidades:
        click.echo("Ninguna unidad válida para generar. Nada que hacer.", err=True)
        sys.exit(1)

    click.echo(f"Generando reporte PPT de {mes:02d}/{anio} para {len(unidades)} unidad(es)...")
    competidores_por_unidad = _competidores_por_unidad(config, secrets, anio, mes)
    anuncios_destacados_por_unidad = _anuncios_destacados_por_unidad(config, secrets, anio, mes)

    generados = 0
    with tempfile.TemporaryDirectory(prefix="reportes_ppt_img_") as carpeta_tmp:
        for unidad in unidades:
            balde = datos["unidades"][unidad]
            constructor = generar_pptx_unidad(
                unidad=unidad,
                anio=anio,
                mes=mes,
                filas_organico=balde["meta_organico"],
                filas_control_perfiles=balde["control_perfiles_red"],
                filas_ads=balde["meta_ads"],
                carpeta_imagenes_tmp=Path(carpeta_tmp),
                competidores=competidores_por_unidad.get(unidad),
                anuncios_destacados=anuncios_destacados_por_unidad.get(unidad),
            )
            nombre_archivo = f"{unidad.replace(' ', '_')}_{anio}-{mes:02d}.pptx"
            ruta = output_dir / nombre_archivo
            constructor.guardar(ruta)
            click.echo(f"  Generado: {ruta}")
            generados += 1

    mailchimp_mes = agregacion.filtrar_por_mes(datos["mailchimp"], anio, mes, campo_fecha="fecha")
    if mailchimp_mes:
        constructor_mailchimp = generar_pptx_mailchimp(anio, mes, datos["mailchimp"])
        ruta_mailchimp = output_dir / f"Mailchimp_CAINCO_{anio}-{mes:02d}.pptx"
        constructor_mailchimp.guardar(ruta_mailchimp)
        click.echo(f"  Generado: {ruta_mailchimp}")
        generados += 1
    else:
        click.echo("  Sin envíos de Mailchimp este mes, no se genera ese reporte.", err=True)

    click.echo(f"Listo. {generados} reporte(s) generado(s) en {output_dir}")


if __name__ == "__main__":
    main()
