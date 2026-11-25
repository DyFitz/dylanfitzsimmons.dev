"""The site's admin, with two-factor login.

While ADMIN_TWO_FACTOR is on, signing in takes a code from an authenticator app, or one of the
backup codes, after the password, and a session only counts as signed in once a code has been
given. While it's off, the password alone does, as before. The setting is read on each request,
so changing it on the host takes effect at the next deploy; turning it off is the way back in
if the phone and the backup codes are both lost.

The two-factor page, linked from the top of every admin page, sets up the authenticator app and
the backup codes. It works with the setting off, so a code can be proved to work before the
setting is turned on.
"""

from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.urls import path
from django_otp.admin import OTPAdminAuthenticationForm
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice


def two_factor_on() -> bool:
    return settings.ADMIN_TWO_FACTOR


class TwoFactorLoginForm(OTPAdminAuthenticationForm):
    """Takes either kind of code in one box: six digits are from the app, and anything else is
    a backup code. django-otp otherwise asks which device the code came from."""

    def _chosen_device(self, user):
        token = (self.cleaned_data.get("otp_token") or "").replace(" ", "")
        self.cleaned_data["otp_token"] = token
        kind = TOTPDevice if token.isdigit() and len(token) == 6 else StaticDevice
        return kind.objects.filter(user=user, confirmed=True).first()


class SiteAdmin(AdminSite):
    """Its titles are set in apps/core/admin.py."""

    @property
    def login_form(self):
        return TwoFactorLoginForm if two_factor_on() else AdminAuthenticationForm

    @property
    def login_template(self):
        return "admin/two_factor_login.html" if two_factor_on() else None

    def has_permission(self, request) -> bool:
        allowed = super().has_permission(request)
        return allowed and (not two_factor_on() or request.user.is_verified())

    def get_urls(self):
        from apps.core.two_factor import two_factor_page

        return [
            path("two-factor/", self.admin_view(two_factor_page), name="two_factor"),
            *super().get_urls(),
        ]
