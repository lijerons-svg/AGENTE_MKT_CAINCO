import sqlite3

import pytest

from marketing_analytics.database.connection import initialize_schema


@pytest.fixture()
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture(autouse=True)
def _entorno_de_secretos_limpio(monkeypatch):
    """load_dotenv() usa override=False: una vez que un test setea
    META_SYSTEM_USER_TOKEN/MAILCHIMP_API_KEY en os.environ, quedan pegadas
    para el resto del proceso de pytest y contaminan tests posteriores que
    esperaban esas variables ausentes. Se limpian antes de cada test."""
    monkeypatch.delenv("META_SYSTEM_USER_TOKEN", raising=False)
    monkeypatch.delenv("MAILCHIMP_API_KEY", raising=False)
