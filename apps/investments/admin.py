from django import forms
from django.contrib import admin, messages

from apps.investments.models import ImportRun, Instrument, Portfolio, Price, PriceSeries
from apps.investments.sources import read_prices
from apps.investments.update import store_prices


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("inception", "cash_target")}),
        ("The thinking behind it", {"fields": ("idea", "holdings", "rules")}),
    )

    def has_add_permission(self, request) -> bool:
        # There is only ever one.
        return not Portfolio.objects.exists()


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("symbol", "label", "sleeve", "sector", "region", "target_weight", "currency")
    list_editable = ("sleeve", "sector", "region", "target_weight")
    list_filter = ("sleeve", "currency", "benchmark_only")
    search_fields = ("symbol", "name", "isin")
    readonly_fields = ("conid", "symbol", "name", "isin", "currency", "kind", "exchange", "country")
    fieldsets = (
        ("From IBKR", {"fields": readonly_fields}),
        (
            "Set here",
            {
                "fields": (
                    "label",
                    "sleeve",
                    "sector",
                    "region",
                    "target_weight",
                    "benchmark_only",
                    "series_key",
                )
            },
        ),
    )

    def has_add_permission(self, request) -> bool:
        # Imports add them.
        return False


class PriceInline(admin.TabularInline):
    model = Price
    extra = 0


class PriceSeriesForm(forms.ModelForm):
    """The series, plus a CSV of closes to add to it."""

    UNITS = (("", "Work it out from prices already kept"), ("pence", "Pence"), ("pounds", "Pounds"))

    prices = forms.FileField(
        required=False,
        label="Add prices from a CSV",
        help_text="A date column and a close or price column, as price sites give them.",
    )
    units = forms.ChoiceField(choices=UNITS, required=False, label="Prices are in")

    class Meta:
        model = PriceSeries
        fields = ("key", "name", "currency", "source")

    def clean_prices(self):
        upload = self.cleaned_data.get("prices")
        if not upload:
            return []
        try:
            rows = read_prices(upload.read().decode("utf-8-sig"))
        except UnicodeDecodeError as error:
            raise forms.ValidationError("That isn't a text CSV file.") from error
        if not rows:
            raise forms.ValidationError("No dates and prices found in the file.")
        return rows


@admin.register(PriceSeries)
class PriceSeriesAdmin(admin.ModelAdmin):
    form = PriceSeriesForm
    list_display = ("name", "key", "currency", "source")
    inlines = (PriceInline,)

    def save_related(self, request, form, formsets, change) -> None:
        super().save_related(request, form, formsets, change)
        rows = form.cleaned_data.get("prices")
        if not rows:
            return
        scale = {"pence": 0.01, "pounds": 1.0}.get(form.cleaned_data.get("units") or "")
        count, used = store_prices(form.instance.key, rows, source="CSV upload", scale=scale)
        note = " (converted from pence)" if used == 0.01 else ""
        self.message_user(
            request,
            f"Added {count} prices, {rows[0][0]:%d %b %Y} to {rows[-1][0]:%d %b %Y}{note}.",
            messages.SUCCESS,
        )


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = ("started", "status", "source", "period_from", "period_to", "days")
    list_filter = ("status",)
    readonly_fields = (
        "started",
        "source",
        "status",
        "period_from",
        "period_to",
        "days",
        "message",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
