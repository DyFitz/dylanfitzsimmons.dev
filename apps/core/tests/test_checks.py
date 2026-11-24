import pytest
from django.core.management import call_command
from pytest_django import Settings

from apps.core.checks import check_admin_url_format, check_admin_url_is_not_default


@pytest.mark.parametrize("admin_url", ["admin/", "manage-7f3a/", "site/admin/"])
def test_well_formed_admin_urls_pass(settings: Settings, admin_url: str) -> None:
    settings.ADMIN_URL = admin_url

    assert check_admin_url_format(app_configs=None) == []


@pytest.mark.parametrize("admin_url", ["", "admin", "/admin/"])
def test_malformed_admin_urls_are_errors(settings: Settings, admin_url: str) -> None:
    settings.ADMIN_URL = admin_url

    assert [message.id for message in check_admin_url_format(app_configs=None)] == ["core.E001"]


def test_the_default_admin_url_is_flagged_for_deployment(settings: Settings) -> None:
    settings.ADMIN_URL = "admin/"

    messages = check_admin_url_is_not_default(app_configs=None)

    assert [message.id for message in messages] == ["core.W001"]


def test_a_custom_admin_url_passes_the_deployment_check(settings: Settings) -> None:
    settings.ADMIN_URL = "manage-7f3a/"

    assert check_admin_url_is_not_default(app_configs=None) == []


@pytest.mark.django_db  # check also runs the database checks as of Django 6.1.
def test_the_project_passes_all_system_checks() -> None:
    # Raises SystemCheckError on any warning or error.
    call_command("check", fail_level="WARNING")
