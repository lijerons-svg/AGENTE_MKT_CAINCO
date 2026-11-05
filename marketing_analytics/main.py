"""Punto de entrada del Skill "Actualizar Reporte RRSS".

Corre el ciclo completo sin intervención manual: extracción → dedupe/upsert
en la base histórica → Historico_RRSS.xlsx → Dashboard.html →
ControlContenido.html → Log_Ejecucion.txt.

Uso:
    python -m marketing_analytics.main
    python -m marketing_analytics.main --config config.yaml --desde 2026-07-01 --hasta 2026-07-31
"""
from __future__ import annotations

import datetime
import shutil
import subprocess
import sys
from pathlib import Path

import click
from pydantic import ValidationError

from marketing_analytics.config.loader import load_config, load_secrets
from marketing_analytics.connectors.registry import construir_conectores_activos
from marketing_analytics.dashboard.builder import generar_dashboard
from marketing_analytics.dashboard.control_contenido.builder import generar_control_contenido
from marketing_analytics.database.configuracion import registrar_fecha_hasta
from marketing_analytics.database.connection import get_connection
from marketing_analytics.reports.excel_builder import generar_historico_excel
from marketing_analytics.services.log_writer import escribir_log_ejecucion
from marketing_analytics.services.orchestrator import ejecutar
from marketing_analytics.services.rango_fechas import resolver_rango_automatico


@click.command()
@click.option(
    "--config", "config_path", default="config.yaml", show_default=True, help="Ruta a config.yaml"
)
@click.option(
    "--env", "env_path", default=None, help="Ruta a .env (por defecto, busca .env en el directorio actual)"
)
@click.option(
    "--desde", "desde_str", default=None, help="Fecha desde (YYYY-MM-DD); sobreescribe config.general.date_range"
)
@click.option(
    "--hasta", "hasta_str", default=None, help="Fecha hasta (YYYY-MM-DD); sobreescribe config.general.date_range"
)
def main(config_path: str, env_path: str | None, desde_str: str | None, hasta_str: str | None) -> None:
    """Ejecuta: extracción -> deduplicación -> base histórica -> reportes."""
    try:
        config = load_config(config_path)
        secrets = load_secrets(env_path)
        conectores = construir_conectores_activos(config, secrets)

        desde_manual = datetime.date.fromisoformat(desde_str) if desde_str and hasta_str else None
        hasta_manual = datetime.date.fromisoformat(hasta_str) if desde_str and hasta_str else None
    except (FileNotFoundError, RuntimeError, ValidationError) as error:
        click.echo(f"Error de configuración: {error}", err=True)
        sys.exit(1)

    if not conectores:
        click.echo("No hay conectores activos en config.yaml. Nada que hacer.", err=True)
        sys.exit(1)

    output_dir = Path(config.general.output_dir)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with get_connection(config.general.database_path) as conn:
            if desde_manual and hasta_manual:
                desde, hasta = desde_manual, hasta_manual
            else:
                # Sin fechas manuales: continúa automáticamente desde el día
                # siguiente a la última corrida registrada (tabla
                # `configuracion`), sin importar cuánto tiempo pasó.
                desde, hasta = resolver_rango_automatico(conn, config.general.date_range)

            click.echo(f"Ejecutando {len(conectores)} conector(es) para el rango {desde} → {hasta}...")

            resumen = ejecutar(conn, conectores, desde, hasta)
            # El checkpoint solo avanza si la corrida fue 100% exitosa. Caso
            # real de QA: durante un corte de token de Meta, cada corrida
            # fallida igual avanzaba el checkpoint — la ventana de fechas
            # nunca se reintentaba y esos datos se perdían para siempre
            # aunque el token se renovara después. Con esto, una corrida con
            # errores simplemente vuelve a intentar el mismo rango la
            # próxima vez (el dedupe por uid hace que reintentar lo ya
            # guardado sea seguro, nunca duplica).
            if resumen.estado == "exitoso":
                registrar_fecha_hasta(conn, hasta)
            else:
                click.echo(
                    "Aviso: hubo errores en esta corrida, así que el checkpoint no avanza — "
                    "la próxima corrida reintenta este mismo rango de fechas en vez de "
                    "saltearlo.",
                    err=True,
                )

            ruta_excel = generar_historico_excel(conn, output_dir / "Historico_RRSS.xlsx", config)
            ruta_dashboard = generar_dashboard(conn, output_dir / "Dashboard.html")
            ruta_control_contenido = generar_control_contenido(
                conn, config, output_dir / "ControlContenido.html"
            )
            ruta_log = escribir_log_ejecucion(conn, resumen, output_dir / "Log_Ejecucion.txt")
    except PermissionError as error:
        click.echo(
            f"Error al escribir archivos ({error}). ¿Alguno está abierto en otro "
            "programa (Excel), o OneDrive lo está sincronizando? Cerralo/pausá la "
            "sincronización e intentá de nuevo.",
            err=True,
        )
        sys.exit(1)

    click.echo(f"Estado: {resumen.estado}")
    click.echo(
        f"Nuevos: {resumen.resultado_total.nuevos} | "
        f"Actualizados: {resumen.resultado_total.actualizados} | "
        f"Descartados: {resumen.resultado_total.descartados}"
    )
    if resumen.errores:
        click.echo("Errores:", err=True)
        for error in resumen.errores:
            click.echo(f"  - {error}", err=True)

    click.echo(f"Generado: {ruta_excel}")
    click.echo(f"Generado: {ruta_dashboard}")
    click.echo(f"Generado: {ruta_control_contenido}")
    click.echo(f"Generado: {ruta_log}")

    # ── Publicar ControlContenido.html en GitHub Pages ──────────────────────
    publicar_github_pages(ruta_control_contenido)
    # ────────────────────────────────────────────────────────────────────────

    sys.exit(1 if resumen.estado == "fallido" else 0)


def publicar_github_pages(ruta_html: Path) -> None:
    """Copia ControlContenido.html a docs/index.html y hace git push.

    Requiere que el repo esté clonado en la misma máquina donde corre el script
    y que git tenga credenciales configuradas (GitHub CLI, credential manager, etc.).
    Si algo falla, solo muestra un aviso — no interrumpe la corrida.
    """
    # Ruta del repo de publicación (AGENTE_MKT_CAINCO en tu compu)
    repo_root = Path(r"C:\Users\sandylu\Claude\Projects\AGENTE_MKT_CAINCO")
    docs_dir = repo_root / "docs"
    destino = docs_dir / "index.html"

    try:
        docs_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ruta_html, destino)
        click.echo(f"GitHub Pages: copiado {ruta_html.name} → docs/index.html")

        # Commit y push solo si hay cambios
        result = subprocess.run(
            ["git", "status", "--porcelain", "docs/index.html"],
            cwd=repo_root, capture_output=True, text=True
        )
        if not result.stdout.strip():
            click.echo("GitHub Pages: sin cambios, nada que publicar.")
            return

        subprocess.run(["git", "add", "docs/index.html"], cwd=repo_root, check=True)
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(
            ["git", "commit", "-m", f"dashboard: actualizar ControlContenido.html ({fecha})"],
            cwd=repo_root, check=True
        )
        subprocess.run(
            ["git", "push"],
            cwd=repo_root, check=True
        )
        click.echo("GitHub Pages: publicado ✓ — el equipo ya puede ver la versión nueva.")

    except Exception as exc:  # noqa: BLE001
        click.echo(
            f"Aviso: no se pudo publicar en GitHub Pages ({exc}). "
            "El dashboard local sí se generó correctamente.",
            err=True,
        )


if __name__ == "__main__":
    main()
