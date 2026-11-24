from typing import NoReturn

import pytest
from django.db import DEFAULT_DB_ALIAS, OperationalError, connections
from django.test import Client

from apps.core.middleware import HEALTH_CHECK_PATH, database_is_reachable


@pytest.mark.django_db
def test_health_check_reports_ok_when_the_database_is_reachable(client: Client) -> None:
    response = client.get(HEALTH_CHECK_PATH)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response["Cache-Control"] == "no-store"


def test_health_check_reports_unavailable_when_the_database_is_down(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("apps.core.middleware.database_is_reachable", lambda: False)

    response = client.get(HEALTH_CHECK_PATH)

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


@pytest.mark.django_db
def test_health_check_accepts_internal_host_names(client: Client) -> None:
    # Platforms probe with internal host names that aren't in ALLOWED_HOSTS.
    response = client.get(HEALTH_CHECK_PATH, headers={"host": "10.0.0.7:8000"})

    assert response.status_code == 200


def test_other_pages_still_validate_the_host(client: Client) -> None:
    response = client.get("/", headers={"host": "10.0.0.7:8000"})

    assert response.status_code == 400


def test_only_get_and_head_requests_reach_the_health_check(client: Client) -> None:
    # Other methods fall through to the URLconf, which has no such route.
    response = client.post(HEALTH_CHECK_PATH)

    assert response.status_code == 404


@pytest.mark.django_db
def test_database_is_reachable_for_a_working_database() -> None:
    assert database_is_reachable() is True


@pytest.mark.django_db
def test_database_is_reachable_reports_and_logs_failures(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def refuse_connection(*args: object, **kwargs: object) -> NoReturn:
        raise OperationalError("connection refused")

    monkeypatch.setattr(connections[DEFAULT_DB_ALIAS], "cursor", refuse_connection)

    assert database_is_reachable() is False
    assert "Health check could not reach" in caplog.text
