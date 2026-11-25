"""The admin page that sets up two-factor login: an authenticator app, then backup codes."""

from base64 import b32encode

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django_otp import login as otp_login
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.core.admin_site import two_factor_on

APP = "authenticator"
BACKUP = "backup codes"
BACKUP_COUNT = 10


def _qr(url: str) -> str:
    """The setup link as a QR code, drawn as SVG so it needs no image file or inline style."""
    image = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    return image.to_string(encoding="unicode")


def _new_backup_codes(user) -> list[str]:
    """Replaces any backup codes with a fresh set, shown once."""
    device, _ = StaticDevice.objects.get_or_create(user=user, name=BACKUP)
    device.token_set.all().delete()
    codes = [StaticToken.random_token() for _ in range(BACKUP_COUNT)]
    StaticToken.objects.bulk_create(StaticToken(device=device, token=code) for code in codes)
    return codes


def _grouped(secret: str) -> str:
    """The key in fours, for typing into an app by hand."""
    return " ".join(secret[i : i + 4] for i in range(0, len(secret), 4))


def two_factor_page(request: HttpRequest) -> HttpResponse:
    from django.contrib import admin

    user = request.user
    confirmed = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    # A new app waits, unconfirmed, until it has given one right code.
    pending = TOTPDevice.objects.filter(user=user, confirmed=False).first()
    backup = StaticDevice.objects.filter(user=user, name=BACKUP).first()
    context = {
        **admin.site.each_context(request),
        "title": "Two-factor login",
        "enforced": two_factor_on(),
        "confirmed": confirmed,
        "backup_left": backup.token_set.count() if backup else 0,
        "codes": None,
    }

    action = request.POST.get("action") if request.method == "POST" else None
    if action == "start":
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()
        TOTPDevice.objects.create(user=user, name=APP, confirmed=False)
        return redirect("admin:two_factor")
    if action == "cancel":
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()
        return redirect("admin:two_factor")
    if action == "confirm" and pending:
        token = request.POST.get("token", "").replace(" ", "")
        if pending.verify_token(token):
            with transaction.atomic():
                TOTPDevice.objects.filter(user=user, confirmed=True).delete()
                pending.confirmed = True
                pending.save(update_fields=["confirmed"])
                codes = _new_backup_codes(user)
            # This session is now signed in with the app, so it stays in when two-factor is on.
            otp_login(request, pending)
            context |= {"confirmed": pending, "codes": codes, "backup_left": len(codes)}
            return TemplateResponse(request, "admin/two_factor.html", context)
        messages.error(request, "That code didn't match. Check the phone's clock, and try again.")
        return redirect("admin:two_factor")
    if action == "backup" and confirmed:
        codes = _new_backup_codes(user)
        context |= {"codes": codes, "backup_left": len(codes)}
        return TemplateResponse(request, "admin/two_factor.html", context)

    if pending:
        context |= {
            "pending": pending,
            "qr": mark_safe(_qr(pending.config_url)),  # noqa: S308 - drawn here from our own data
            "secret": _grouped(b32encode(pending.bin_key).decode()),
        }
    return TemplateResponse(request, "admin/two_factor.html", context)
