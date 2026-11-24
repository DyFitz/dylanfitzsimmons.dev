import re
from typing import Any, ClassVar

from django import forms
from django.core import signing

from apps.contact import spam
from apps.contact.models import Message

MAX_LENGTH = 2000

# Line breaks and other control characters have no place in a name, and would break the
# headers of the email it goes into.
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


class MessageField(forms.CharField):
    def to_python(self, value: Any) -> str:
        # Browsers send line breaks as \r\n but count them as one character towards the limit,
        # so they're stored and counted the same way here.
        return super().to_python(value).replace("\r\n", "\n")


class MessageForm(forms.ModelForm):
    body = MessageField(
        label="message",
        max_length=MAX_LENGTH,
        widget=forms.Textarea(
            attrs={"rows": 7, "placeholder": "What would you like to talk about?"}
        ),
        error_messages={
            "required": "nothing to send yet",
            "max_length": "that's over 2,000 characters",
        },
    )
    # The honeypot. People never see it (see contact.css); bots fill it in.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )
    # When the form was served, signed so it can't be faked. Checked in clean().
    served = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Message
        fields = ("name", "email", "reason", "body")
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "your name"}),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email", "placeholder": "you@example.com"}
            ),
            "reason": forms.RadioSelect,
        }
        error_messages: ClassVar[dict[str, dict[str, str]]] = {
            "name": {"required": "your name is missing", "max_length": "that name is too long"},
            "email": {
                "required": "an address to reply to is needed",
                "invalid": "that address is incomplete",
            },
        }

    def __init__(self, *args: Any, sender_hash: str = "", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.sender_hash = sender_hash
        # Set when the honeypot is filled in. The view then pretends to send it.
        self.is_spam = False
        for name in ("name", "email", "body"):
            self.fields[name].widget.attrs["class"] = "field__input"

    def full_clean(self) -> None:
        super().full_clean()
        # Ties each error to its field, so screen readers read it out with the field.
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs["aria-describedby"] = f"{self[name].auto_id}-error"

    def clean_name(self) -> str:
        name = self.cleaned_data["name"]
        if CONTROL_CHARACTERS.search(name):
            raise forms.ValidationError("a name can't contain line breaks")
        return name

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if self.data.get(spam.HONEYPOT_FIELD):
            self.is_spam = True
            return cleaned_data

        try:
            seconds = spam.seconds_since(self.data.get("served", ""))
        except signing.SignatureExpired:
            raise forms.ValidationError(
                "This form was open for over a day, so it's been refreshed. "
                "Please press Transmit again."
            ) from None
        except signing.BadSignature:
            raise forms.ValidationError(
                "Something went wrong with the form. Please press Transmit again."
            ) from None
        if seconds < spam.MIN_SECONDS:
            raise forms.ValidationError(
                "That was sent very quickly, so it looked automated. "
                "Please check it over and press Transmit again."
            )

        recent = Message.objects.recent_from(self.sender_hash, spam.RATE_WINDOW)
        if self.sender_hash and recent.count() >= spam.RATE_LIMIT:
            raise forms.ValidationError(
                "You've sent a few messages in the last hour, which is the limit. "
                "Please try again later."
            )
        return cleaned_data
