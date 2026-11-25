"""Fixtures shared by every app's tests."""

import pytest
import sentry_sdk
from sentry_sdk.transport import Transport

from config.sentry import start


class Envelopes(Transport):
    """Keeps what would have gone to Sentry, instead of sending it."""

    def __init__(self, options=None):
        super().__init__(options)
        self.kept = []

    def capture_envelope(self, envelope):
        self.kept.extend(item.payload.json for item in envelope.items)

    def events(self) -> list[dict]:
        """The errors reported, leaving out check-ins and logs."""
        return [sent for sent in self.kept if "exception" in sent or "logentry" in sent]


@pytest.fixture
def sentry():
    """Error tracking switched on as in production, with everything it sends kept here."""
    transport = Envelopes()
    start("https://public@sentry.example.com/1", release="abc123", transport=transport)
    yield transport
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)
