import pytest

from petshop_ai.config import get_settings
from petshop_ai.crear_db import crear_db


@pytest.fixture(autouse=True)
def db_temporal(tmp_path, monkeypatch):
    """Cada test usa una base nueva (como un fixture de xUnit con IClassFixture + reset)."""
    monkeypatch.setenv("PETSHOP_DB", str(tmp_path / "petshop_test.db"))
    get_settings.cache_clear()
    crear_db()
    yield
    get_settings.cache_clear()
