"""Identificador único de deduplicación: Fuente + ID publicación/campaña +
Perfil + Fecha, tal como lo define la especificación del proyecto."""
from __future__ import annotations

import datetime


def build_uid(
    fuente: str,
    fecha: datetime.date | str,
    perfil: str = "",
    id_publicacion: str = "",
    id_campana: str = "",
) -> str:
    if not fuente:
        raise ValueError("fuente es obligatoria para construir el uid")
    if not id_publicacion and not id_campana:
        raise ValueError("se requiere id_publicacion o id_campana para construir el uid")

    fecha_str = fecha.isoformat() if isinstance(fecha, datetime.date) else str(fecha)
    partes = [fuente, perfil or "-", id_publicacion or "-", id_campana or "-", fecha_str]
    return "|".join(partes)
