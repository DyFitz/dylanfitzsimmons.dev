import pytest
from django.core import signing
from django.test import RequestFactory
from pytest_django import Settings

from apps.contact import spam


def test_seconds_since_reads_back_the_time_the_form_was_served(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(spam, "now", lambda: 1000.0)
    token = spam.new_token()
    monkeypatch.setattr(spam, "now", lambda: 1012.5)

    assert spam.seconds_since(token) == pytest.approx(12.5)


def test_a_token_signed_for_something_else_is_rejected() -> None:
    token = signing.dumps(0, salt="something-else")

    with pytest.raises(signing.BadSignature):
        spam.seconds_since(token)


def test_client_ip_is_remote_addr_with_no_proxy(settings: Settings) -> None:
    settings.CLIENT_IP_HEADER = ""
    request = RequestFactory().get(
        "/", REMOTE_ADDR="203.0.113.9", HTTP_X_FORWARDED_FOR="198.51.100.1"
    )

    assert spam.client_ip(request) == "203.0.113.9"


def test_client_ip_behind_a_proxy_trusts_only_the_address_it_added(settings: Settings) -> None:
    settings.CLIENT_IP_HEADER = "HTTP_X_FORWARDED_FOR"
    # The first address came from the sender, so could be made up; the proxy added the last.
    request = RequestFactory().get(
        "/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="1.2.3.4, 203.0.113.9"
    )

    assert spam.client_ip(request) == "203.0.113.9"


def test_client_ip_falls_back_when_the_proxy_header_is_missing(settings: Settings) -> None:
    settings.CLIENT_IP_HEADER = "HTTP_X_FORWARDED_FOR"
    request = RequestFactory().get("/", REMOTE_ADDR="10.0.0.1")

    assert spam.client_ip(request) == "10.0.0.1"


def test_the_sender_hash_is_steady_and_does_not_contain_the_address() -> None:
    first = spam.sender_hash(RequestFactory().get("/", REMOTE_ADDR="203.0.113.9"))
    again = spam.sender_hash(RequestFactory().get("/", REMOTE_ADDR="203.0.113.9"))
    other = spam.sender_hash(RequestFactory().get("/", REMOTE_ADDR="203.0.113.10"))

    assert first == again
    assert first != other
    assert "203.0.113" not in first
    assert len(first) == 64
