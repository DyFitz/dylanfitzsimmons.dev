from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView

from apps.contact import packet, spam
from apps.contact.forms import MAX_LENGTH, MessageForm
from apps.contact.models import Message
from apps.contact.notify import email_me
from apps.core.mixins import PageMetaMixin
from apps.cv.models import Profile

# Which message the confirmation page shows, kept in the sender's session so a refresh
# shows it again and nobody else can see it.
SESSION_KEY = "contact_message_id"

# How soon a reply can be expected, shown on the contact and sent pages.
REPLY_WITHIN = "two working days"


def station_context() -> dict[str, Any]:
    """What the panel beside the console shows, on both pages."""
    return {"profile": Profile.objects.first(), "reply_within": REPLY_WITHIN}


class ContactView(PageMetaMixin, FormView):
    template_name = "contact/contact.html"
    form_class = MessageForm
    page_title = "Contact"
    page_description = "Got a role or a project in mind? Send me a message and I'll reply by email."

    def get_initial(self) -> dict[str, Any]:
        return {"served": spam.new_token(), "reason": Message.Reason.JOB}

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["sender_hash"] = spam.sender_hash(self.request)
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(station_context())
        context["max_length"] = MAX_LENGTH
        context["honeypot"] = spam.HONEYPOT_FIELD
        return context

    def form_valid(self, form: MessageForm) -> HttpResponse:
        if form.is_spam:
            # Looks the same as a real send from outside, so bots don't learn anything.
            return HttpResponseRedirect(reverse("contact:sent"))

        message = form.save(commit=False)
        message.sender_hash = form.sender_hash
        message.save()
        message.emailed = email_me(message)
        message.save(update_fields=["emailed"])
        # Clearing out old messages as new ones come in keeps to the 12 months even if the
        # scheduled delete_old_messages command stops running.
        Message.objects.expired().delete()

        self.request.session[SESSION_KEY] = message.pk
        return HttpResponseRedirect(reverse("contact:sent"))

    def form_invalid(self, form: MessageForm) -> HttpResponse:
        # A fresh timestamp, so a form that had expired works the next time.
        form.data = form.data.copy()
        form.data["served"] = spam.new_token()
        return super().form_invalid(form)


@method_decorator(never_cache, name="dispatch")
class SentView(PageMetaMixin, TemplateView):
    """The confirmation, with the message being sent shown as the console's readout.

    Reached by a redirect after the form is sent, so refreshing it doesn't send it again.
    """

    template_name = "contact/sent.html"
    page_title = "Message sent"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        message_id = request.session.get(SESSION_KEY)
        self.message = Message.objects.filter(pk=message_id).first() if message_id else None
        if self.message is None:
            return redirect("contact:page")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(station_context())
        context["message"] = self.message
        context["hex_dump"] = packet.hex_dump(self.message.body)
        context["hex_dump_narrow"] = packet.hex_dump(
            self.message.body, row=8, rows=4, offsets=False
        )
        context["checksum"] = packet.checksum(self.message.body)
        context["size"] = len(self.message.body.encode())
        return context
