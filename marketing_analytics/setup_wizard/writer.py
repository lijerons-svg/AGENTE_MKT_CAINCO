"""Carga, fusiona y guarda config.yaml/.env sin pisar lo que no se toca en
esta corrida del asistente — así se puede configurar una fuente por vez."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml
from dotenv import set_key

_CONFIG_BASE = {
    "general": {
        "timezone": "America/La_Paz",
        "output_dir": "output",
        "database_path": "database/historico_rrss.db",
        "date_range": {"modo": "last_n_days", "ultimos_n_dias": 30},
    },
    "meta": {"api_version": "v25.0", "organico": {"perfiles": []}, "ads": {"cuentas": []}},
    "mailchimp": {"server_prefix": "", "enabled": False},
    "linkedin": {"enabled": False},
}


def cargar_config(ruta: Path) -> dict:
    base = copy.deepcopy(_CONFIG_BASE)
    if not ruta.exists():
        return base
    data = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    _fusionar(base, data)
    return base


def _fusionar(base: dict, nuevo: dict) -> None:
    for clave, valor in nuevo.items():
        if isinstance(valor, dict) and isinstance(base.get(clave), dict):
            _fusionar(base[clave], valor)
        else:
            base[clave] = valor


def guardar_config(ruta: Path, config: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")


def guardar_secreto(ruta_env: Path, clave: str, valor: str) -> None:
    ruta_env.parent.mkdir(parents=True, exist_ok=True)
    if not ruta_env.exists():
        ruta_env.write_text("", encoding="utf-8")
    set_key(str(ruta_env), clave, valor, quote_mode="never")
