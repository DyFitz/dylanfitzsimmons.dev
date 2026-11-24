import logging
from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from apps.contact.models import Message

logger = logging.getLogger(__name__)


def email_me(message: Message) -> bool:
    """Email me the message, with Reply-To set to the sender so I can answer straight back.

    Returns whether it went. If it doesn't, the message is still saved, so it's logged rather
    than shown to the sender as a failure.
    """
    email = EmailMessage(
        subject=f"{message.reference} {message.get_reason_display()}: {message.name}",
        body=render_to_string("contact/email.txt", {"message": message}),
        to=[settings.CONTACT_EMAIL],
        reply_to=[formataddr((message.name, message.email))],
    )
    try:
        email.send()
    except OSError:
        # smtplib's errors are all OSErrors, as are connection failures.
        logger.exception("Couldn't email contact message %s", message.reference)
        return False
    return True
