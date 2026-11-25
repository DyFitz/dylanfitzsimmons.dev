import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_ENVIRONMENT = {
    "DJANGO_SECRET_KEY": "test-only-value-for-importing-settings",
    "DJANGO_ALLOWED_HOSTS": "example.com",
    "DATABASE_URL": "sqlite://:memory:",
    "SITE_URL": "https://example.com",
}


def import_production_settings(
    environment: dict[str, str], then: str = ""
) -> subprocess.CompletedProcess[str]:
    """Import the production settings in a fresh interpreter, then run `then`.

    The project's own environment variables are replaced by `environment`.
    """
    inherited = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("DJANGO_", "DATABASE_", "SITE_", "SENTRY_"))
    }
    return subprocess.run(
        [sys.executable, "-c", f"import config.settings.production\n{then}"],
        cwd=PROJECT_ROOT,
        env={**inherited, **environment, "DJANGO_READ_DOT_ENV": "false"},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_production_settings_load_with_the_required_environment() -> None:
    result = import_production_settings(REQUIRED_ENVIRONMENT)

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("missing", sorted(REQUIRED_ENVIRONMENT))
def test_production_settings_fail_fast_when_configuration_is_missing(missing: str) -> None:
    environment = {key: value for key, value in REQUIRED_ENVIRONMENT.items() if key != missing}

    result = import_production_settings(environment)

    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert missing in result.stderr


REPORT_SENTRY = """
import sentry_sdk
client = sentry_sdk.get_client()
print(client.is_active())
if client.is_active():
    options = client.options
    print(options["release"], options["environment"])
    print(options["data_collection"]["user_info"], options["data_collection"]["http_bodies"])
    print(client.get_integration("logging") is not None)
"""


def test_error_tracking_stays_off_without_a_dsn() -> None:
    result = import_production_settings(REQUIRED_ENVIRONMENT, then=REPORT_SENTRY)

    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["False"]


def test_error_tracking_starts_with_a_dsn_and_keeps_personal_details_out() -> None:
    environment = {
        **REQUIRED_ENVIRONMENT,
        "SENTRY_DSN": "https://public@sentry.example.com/1",
        "GIT_SHA": "abc123",
    }

    result = import_production_settings(environment, then=REPORT_SENTRY)

    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["True", "abc123", "production", "False", "[]", "True"]
