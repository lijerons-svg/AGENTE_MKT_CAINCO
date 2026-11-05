"""Interfaz común que debe implementar cualquier conector (actual o futuro).

El orquestador (fase 4) solo conoce esta interfaz: agregar Google Analytics 4,
TikTok, etc. es crear una clase nueva que la implemente y registrarla en
`registry.py` — nunca tocar el núcleo (services/, database/).
"""
from __future__ import annotations

import datetime
import sqlite3
from abc import ABC, abstractmethod
from typing import Any

from marketing_analytics.database.repository import ResultadoUpsert


class BaseConnector(ABC):
    nombre: str

    @abstractmethod
    def fetch(self, desde: datetime.date, hasta: datetime.date) -> Any:
        """Trae los datos crudos del rango [desde, hasta] y los devuelve ya
        mapeados a los modelos de marketing_analytics.models.records."""

    @abstractmethod
    def upsert(self, conn: sqlite3.Connection, datos: Any) -> ResultadoUpsert:
        """Persiste lo que devolvió fetch() usando database.repository."""
