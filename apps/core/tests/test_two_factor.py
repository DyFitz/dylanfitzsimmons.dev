import pytest
from django.urls import reverse
from django_otp.oath import totp
from django_otp.plugins.otp_static.models import StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from pytest_django.asserts import assertContains, assertRedirects

PAGE = "admin:two_factor"


def code_for(device: TOTPDevice, ahead: int = 0) -> str:
    """The app's code now, or `ahead` steps on: a code can't be used twice."""
    return f"{totp(device.bin_key, step=device.step, digits=device.digits, drift=ahead):06d}"


def set_up_app(client, user) -> list[str]:
    """Goes through the page's setup, returning the backup codes it shows."""
    client.post(reverse(PAGE), {"action": "start"})
    device = TOTPDevice.objects.get(user=user, confirmed=False)
    response = client.post(reverse(PAGE), {"action": "confirm", "token": code_for(device)})
    return response.context["codes"]


@pytest.fixture
def superuser(admin_user):
    return admin_user


def test_the_page_says_two_factor_is_off_until_it_is_turned_on(admin_client):
    response = admin_client.get(reverse(PAGE))
    assertContains(response, "Two-factor login is <strong>off</strong>")
    assertContains(response, "Set up an authenticator app")


def test_every_admin_page_links_to_it(admin_client):
    assertContains(admin_client.get(reverse("admin:index")), reverse(PAGE))


def test_setting_up_shows_a_qr_code_then_backup_codes(admin_client, superuser):
    admin_client.post(reverse(PAGE), {"action": "start"})
    page = admin_client.get(reverse(PAGE))
    assertContains(page, "<svg")
    assertContains(page, "Or type this key in by hand")
    assert "style=" not in page.content.decode().split('class="two-factor__qr"')[1][:2000]

    codes = set_up_app(admin_client, superuser)
    assert len(codes) == 10
    assert TOTPDevice.objects.get(user=superuser).confirmed
    assert StaticToken.objects.filter(device__user=superuser).count() == 10


def test_a_wrong_code_sets_nothing_up(admin_client, superuser):
    admin_client.post(reverse(PAGE), {"action": "start"})
    response = admin_client.post(
        reverse(PAGE), {"action": "confirm", "token": "000000"}, follow=True
    )
    assertContains(response, "didn&#x27;t match")
    assert not TOTPDevice.objects.filter(user=superuser, confirmed=True).exists()


def test_a_new_phone_replaces_the_old_only_once_it_works(admin_client, superuser):
    set_up_app(admin_client, superuser)
    old = TOTPDevice.objects.get(user=superuser, confirmed=True)
    admin_client.post(reverse(PAGE), {"action": "start"})
    assert TOTPDevice.objects.filter(pk=old.pk, confirmed=True).exists()
    set_up_app(admin_client, superuser)
    assert not TOTPDevice.objects.filter(pk=old.pk).exists()
    assert TOTPDevice.objects.filter(user=superuser, confirmed=True).count() == 1


def test_new_backup_codes_replace_the_old(admin_client, superuser):
    first = set_up_app(admin_client, superuser)
    second = admin_client.post(reverse(PAGE), {"action": "backup"}).context["codes"]
    assert set(first).isdisjoint(second)
    assert set(StaticToken.objects.values_list("token", flat=True)) == set(second)


# ---------------------------------------------------------------- with it turned on


def sign_in(client, code: str):
    return client.post(
        reverse("admin:login"),
        {"username": "admin", "password": "password", "otp_token": code, "next": "/"},
    )


def test_turned_on_the_password_alone_isnt_enough(client, admin_client, superuser, settings):
    set_up_app(admin_client, superuser)
    settings.ADMIN_TWO_FACTOR = True
    page = client.get(reverse("admin:login"))
    assertContains(page, "From your authenticator app, or one of your backup codes.")
    response = sign_in(client, "")
    assert response.status_code == 200
    assert client.get(reverse("admin:index")).status_code == 302


def test_turned_on_a_code_from_the_app_signs_in(client, admin_client, superuser, settings):
    set_up_app(admin_client, superuser)
    settings.ADMIN_TWO_FACTOR = True
    device = TOTPDevice.objects.get(user=superuser)
    assertRedirects(sign_in(client, code_for(device, 1)), "/", fetch_redirect_response=False)
    assert client.get(reverse("admin:index")).status_code == 200


def test_turned_on_a_backup_code_signs_in_once(client, admin_client, superuser, settings):
    codes = set_up_app(admin_client, superuser)
    settings.ADMIN_TWO_FACTOR = True
    assertRedirects(sign_in(client, codes[0]), "/", fetch_redirect_response=False)
    assert not StaticToken.objects.filter(token=codes[0]).exists()


def test_turned_on_a_session_without_a_code_is_sent_to_sign_in(admin_client, settings):
    settings.ADMIN_TWO_FACTOR = True
    response = admin_client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert reverse("admin:login") in response["Location"]
