import logging
from io import BytesIO
from wsgiref.util import setup_testing_defaults

import pytest
from django.core.wsgi import get_wsgi_application
from django.http import HttpRequest, HttpResponse
from django.test import Client
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from config.sentry import start


@csrf_exempt
def broken(request: HttpRequest) -> HttpResponse:
    email = request.POST["email"]
    raise RuntimeError(f"Broke on purpose, for {len(email)} characters")


urlpatterns = [path("broken/", broken)]


def test_nothing_starts_without_a_dsn() -> None:
    assert start("") is False


@pytest.mark.urls("apps.core.tests.test_error_tracking")
def test_a_failing_page_is_reported_without_the_visitors_details(sentry, admin_user) -> None:
    client = Client(raise_request_exception=False)
    client.force_login(admin_user)
    client.cookies["theme"] = "dark"

    response = client.post(
        "/broken/?from=somewhere", {"email": "someone@example.com", "message": "Hello"}
    )

    assert response.status_code == 500
    [event] = sentry.events()
    assert event["exception"]["values"][-1]["value"].startswith("Broke on purpose")
    assert event["release"] == "abc123"
    assert event["environment"] == "production"
    sent = str(event)
    assert "someone@example.com" not in sent
    assert "Hello" not in sent
    assert "dark" not in sent
    assert "somewhere" not in sent
    assert admin_user.email not in sent
    assert "vars" not in str(event["exception"])


@pytest.mark.urls("apps.core.tests.test_error_tracking")
def test_a_reported_page_keeps_its_address_but_not_the_visitors(sentry) -> None:
    body = b"email=someone%40example.com"
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/broken/",
        "QUERY_STRING": "from=somewhere",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
        "REMOTE_ADDR": "203.0.113.7",
        "HTTP_X_FORWARDED_FOR": "198.51.100.9",
        "HTTP_TRUE_CLIENT_IP": "198.51.100.9",
        "HTTP_COOKIE": "sessionid=s3ss10n; theme=dark",
        "HTTP_USER_AGENT": "Test browser",
        "HTTP_HOST": "testserver",
    }
    setup_testing_defaults(environ)

    response = get_wsgi_application()(environ, lambda status, headers: None)
    b"".join(response)
    response.close()

    [event] = sentry.events()
    request = event["request"]
    assert request["url"].endswith("/broken/")
    assert request["method"] == "POST"
    assert request["headers"]["User-Agent"] == "Test browser"
    sent = str(event)
    for private in ("203.0.113.7", "198.51.100.9", "someone", "somewhere", "dark", "s3ss10n"):
        assert private not in sent


def test_a_logged_error_is_reported(sentry) -> None:
    logging.getLogger("apps.contact.notify").error("Couldn't email contact message %s", "M-1")

    [event] = sentry.events()
    assert event["logentry"]["params"] == ["M-1"]


def test_requests_for_other_hosts_arent_reported(sentry) -> None:
    response = Client(raise_request_exception=False).get("/", headers={"host": "elsewhere.test"})

    assert response.status_code == 400
    assert sentry.events() == []
