import pytest


@pytest.fixture(autouse=True)
def _database(db):
    """The home page reads the portfolio for its investments banner, so every page test here
    may touch the database."""
