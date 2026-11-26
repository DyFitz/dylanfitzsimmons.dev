"""Error tracking with Sentry, switched on in production by setting `SENTRY_DSN`.

Only the server reports errors; there's no browser script, so the content security policy is
unchanged. Personal details are kept out: contact messages and other request bodies, cookies,
the signed-in user, visitors' IP addresses, query strings (the IBKR token travels in one) and
the values of a frame's variables are never sent. The code and its line numbers are, which is
enough to find a fault.

Besides errors, one request in ten is traced, warnings and errors that are logged go to Sentry's
logs, and the daily update checks in so a missed or failed run raises an alert.
"""

import logging
from typing import Any

from django.core.management.base import CommandError

# The daily update's schedule, as set on the cron job, so Sentry can tell when a run is missed.
UPDATE_SCHEDULE = "45 10 * * 2-6"

DATA_COLLECTION = {
    "user_info": False,
    "cookies": {"mode": "off"},
    # Only headers that describe the request, not the visitor's address.
    "http_headers": {
        "request": {
            "mode": "allowlist",
            "terms": ["user-agent", "referer", "accept", "content-type", "content-length", "host"],
        },
    },
    "http_bodies": [],
    "url_query_params": {"mode": "off"},
    "database_query_data": False,
    "stack_frame_variables": False,
}

UPDATE_MONITOR = {
    "schedule": {"type": "crontab", "value": UPDATE_SCHEDULE},
    "timezone": "UTC",
    # Minutes Render may start late, and the longest a run should take.
    "checkin_margin": 30,
    "max_runtime": 15,
}


def start(dsn: str, release: str = "", environment: str = "production", **options: Any) -> bool:
    """Start reporting errors, if there's somewhere to send them. Returns whether it started.

    `options` go straight to Sentry, for the tests to swap in their own transport.
    """
    if not dsn:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.logging import (
        LoggingIntegration,
        ignore_logger,
        ignore_logger_for_events,
    )

    sentry_sdk.init(
        dsn=dsn,
        release=release or None,
        environment=environment,
        data_collection=DATA_COLLECTION,
        # A failed daily update is already emailed and shows on the cron monitor, so the
        # error that ends the command isn't reported a third time.
        ignore_errors=[CommandError],
        # Warnings and errors go to Sentry's logs, beside the issue they belong to, and an
        # error that's logged (a contact email that didn't send, say) becomes an issue itself.
        integrations=[LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR)],
        # One request in ten is traced, so an error shows the request it came from without
        # using up the free plan.
        traces_sample_rate=0.1,
        # No tracing headers on requests to other services: they need none, a firewall may
        # take them for a bot (IBKR's began refusing requests once they were added), and
        # they'd tell outside servers about this site's traces.
        trace_propagation_targets=[],
        # This setup has been checked against the package's own checklist.
        _experiments={"agent_setup_complete": True},
        **options,
    )
    # Scanners send requests for other host names all day; Django refuses and logs them, and
    # they'd soon bury the real errors.
    ignore_logger_for_events("django.security.DisallowedHost")
    ignore_logger("django.security.DisallowedHost")
    return True
