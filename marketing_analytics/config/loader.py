"""Carga config.yaml (+ .env) y devuelve un AppConfig validado."""
from __future__ import annotations

from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.config.secrets import Secrets


def load_config(config_path: str | Path, env_path: str | Path | None = None) -> AppConfig:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(raw)


def load_secrets(env_path: str | Path | None = None) -> Secrets:
    if env_path is not None:
        load_dotenv(dotenv_path=env_path, override=False)
    else:
        # find_dotenv(usecwd=True): sin esto, la búsqueda automática de
        # load_dotenv() arranca desde la ubicación de ESTE archivo
        # (config/loader.py), no del directorio desde el que se corre el
        # comando — contradice el propio texto de ayuda de main.py ("por
        # defecto, busca .env en el directorio actual"). Caso real:
        # corriendo `python -m marketing_analytics.main` desde la carpeta
        # del proyecto, con un .env ahí mismo, no lo encontraba igual.
        load_dotenv(dotenv_path=find_dotenv(usecwd=True), override=False)
    return Secrets.from_env()
