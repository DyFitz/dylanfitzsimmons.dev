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


def import_production_settings(environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Import the production settings in a fresh interpreter.

    The project's own environment variables are replaced by `environment`.
    """
    inherited = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("DJANGO_", "DATABASE_", "SITE_"))
    }
    return subprocess.run(
        [sys.executable, "-c", "import config.settings.production"],
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
