"""The contact form's defences against spam, none of which ask anything of a real person.

- A honeypot: a field hidden from people that bots fill in anyway.
- A timing check: the form carries a signed note of when it was served, and anything sent
  back within a few seconds wasn't typed by hand.
- A rate limit: a few messages an hour from any one sender.
"""

import time
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.http import HttpRequest
from django.utils.crypto import salted_hmac

HONEYPOT_FIELD = "website"
SERVED_SALT = "apps.contact.form-served"

# Quicker than this, the form was filled in by a script.
MIN_SECONDS = 3
# Longer than this, the form has been left open and is served again.
MAX_SECONDS = 24 * 60 * 60

RATE_LIMIT = 3
RATE_WINDOW = timedelta(hours=1)


def now() -> float:
    return time.time()


def new_token() -> str:
    """A signed note of when the form was served, for its hidden field."""
    return signing.dumps(now(), salt=SERVED_SALT)


def seconds_since(token: str) -> float:
    """How long ago the form carrying this token was served.

    Raises signing.SignatureExpired if it was over a day ago, and signing.BadSignature if the
    token has been tampered with.
    """
    served = signing.loads(token, salt=SERVED_SALT, max_age=MAX_SECONDS)
    return now() - float(served)


def client_ip(request: HttpRequest) -> str:
    """The sender's IP address.

    Behind the hosting platform's proxy, REMOTE_ADDR is the proxy's address, so
    CLIENT_IP_HEADER names the header the proxy puts the real one in. The proxy adds the
    address it saw to the end of the list, so the last entry is the one to trust: anything
    before it came from the sender and could be made up.
    """
    header = settings.CLIENT_IP_HEADER
    if header:
        forwarded = request.META.get(header, "").split(",")[-1].strip()
        if forwarded:
            return forwarded
    return request.META.get("REMOTE_ADDR", "")


def sender_hash(request: HttpRequest) -> str:
    """The sender's IP address, hashed with the secret key so the address itself isn't kept."""
    return salted_hmac("apps.contact.sender", client_ip(request), algorithm="sha256").hexdigest()
