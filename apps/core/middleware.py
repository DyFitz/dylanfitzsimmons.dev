import logging
from collections.abc import Callable
from http import HTTPStatus

from django.db import DEFAULT_DB_ALIAS, DatabaseError, connections
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)

HEALTH_CHECK_PATH = "/healthz/"


def database_is_reachable(alias: str = DEFAULT_DB_ALIAS) -> bool:
    try:
        with connections[alias].cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        logger.exception("Health check could not reach the %r database", alias)
        return False
    return True


class HealthCheckMiddleware:
    """Answer GET /healthz/ before host validation and the HTTPS redirect.

    Load balancers probe over plain HTTP using internal host names, which
    ALLOWED_HOSTS and SECURE_SSL_REDIRECT would otherwise reject. Must stay
    first in MIDDLEWARE.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path == HEALTH_CHECK_PATH and request.method in {"GET", "HEAD"}:
            return self.health_response()
        return self.get_response(request)

    @staticmethod
    def health_response() -> JsonResponse:
        healthy = database_is_reachable()
        response = JsonResponse(
            {"status": "ok" if healthy else "unavailable"},
            status=HTTPStatus.OK if healthy else HTTPStatus.SERVICE_UNAVAILABLE,
        )
        response["Cache-Control"] = "no-store"
        return response
