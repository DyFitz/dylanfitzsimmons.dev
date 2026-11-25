"""The investment portfolio as the site keeps it.

Nothing here is an amount of money. The account's values are used during an import to work out
weights and returns, and only those are stored (see docs/adr/0003). Prices and exchange rates
are kept, as they are the market's figures, not the account's.
"""

from typing import ClassVar

from django.db import models


class Portfolio(models.Model):
    """The written side of the page, and the date the record starts. There is only one."""

    inception = models.DateField(
        help_text="The close the record starts from. Earlier days in a report are left out."
    )
    idea = models.TextField(blank=True, help_text="The idea, in Markdown.")
    holdings = models.TextField(blank=True, help_text="Why these holdings, in Markdown.")
    rules = models.TextField(blank=True, help_text="The rules, in Markdown.")
    cash_target = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="Target weight of cash, in %."
    )

    class Meta:
        verbose_name = "portfolio"
        verbose_name_plural = "portfolio"

    def __str__(self) -> str:
        return f"Portfolio from {self.inception:%d %b %Y}"

    @classmethod
    def load(cls) -> Portfolio | None:
        return cls.objects.first()


class Instrument(models.Model):
    """Something the portfolio holds or has held. IBKR's contract ID identifies it."""

    class Sleeve(models.TextChoices):
        GROWTH = "growth", "Growth"
        INCOME = "income", "Income and value"
        DEFENSIVE = "defensive", "Defensive equities"
        DEFENCE = "defence", "Capital defence"

    conid = models.PositiveBigIntegerField("IBKR contract ID", unique=True)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=120, help_text="IBKR's name for it.")
    label = models.CharField(
        max_length=80, blank=True, help_text="The name the page shows. IBKR's is used if blank."
    )
    isin = models.CharField("ISIN", max_length=12, blank=True)
    currency = models.CharField(max_length=3)
    kind = models.CharField(max_length=40, blank=True, help_text='IBKR\'s, e.g. "STK / ETF".')
    exchange = models.CharField(max_length=20, blank=True)
    country = models.CharField(
        max_length=2, blank=True, help_text="Where the issuer is registered, from IBKR."
    )
    # Set by hand in the admin. An import never changes these.
    sleeve = models.CharField(max_length=10, choices=Sleeve, blank=True)
    sector = models.CharField(max_length=40, blank=True)
    region = models.CharField(max_length=20, blank=True)
    target_weight = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="In %."
    )
    benchmark_only = models.BooleanField(
        default=False,
        help_text="Held only so IBKR reports its price for a benchmark. Left off the page.",
    )
    series_key = models.SlugField(
        blank=True,
        help_text="If set, each import also keeps its closing price, in pounds, as the price "
        'series with this key (e.g. "acwi").',
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["symbol"]

    def __str__(self) -> str:
        return self.symbol

    @property
    def display_name(self) -> str:
        return self.label or self.name.title()


class Day(models.Model):
    """The whole portfolio at one day's close."""

    date = models.DateField(unique=True)
    daily_return = models.FloatField(
        help_text="Since the previous close, as a fraction. 0 on the first day."
    )
    cash_weight = models.FloatField(help_text="Cash as a fraction of the portfolio.")
    flow = models.FloatField(
        default=0,
        help_text="Money paid in that day (negative if taken out), as a fraction of the previous "
        "close. The day's return and income are measured against the two together.",
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["date"]

    def __str__(self) -> str:
        return f"{self.date:%Y-%m-%d}"


class Holding(models.Model):
    """One instrument at one day's close."""

    date = models.DateField()
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="days")
    weight = models.FloatField(help_text="Its share of the portfolio, as a fraction.")
    contribution = models.FloatField(
        help_text="What it added to the day's return, in pounds and as a fraction of the "
        "portfolio. Dividends are kept apart, as income."
    )
    price = models.FloatField(help_text="The closing price, in its own currency.")
    fx = models.FloatField("rate to pounds", help_text="Pounds for one unit of its currency.")

    class Meta:
        ordering: ClassVar[list[str]] = ["date", "instrument"]
        constraints: ClassVar[list] = [
            models.UniqueConstraint(fields=["date", "instrument"], name="one_holding_a_day"),
        ]

    def __str__(self) -> str:
        return f"{self.instrument} on {self.date:%Y-%m-%d}"


class Trade(models.Model):
    """A purchase or sale, sized as a share of the portfolio."""

    class Side(models.TextChoices):
        BUY = "buy", "Buy"
        SELL = "sell", "Sell"

    ibkr_id = models.CharField("IBKR transaction ID", max_length=30, unique=True)
    date = models.DateField()
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="trades")
    side = models.CharField(max_length=4, choices=Side)
    weight = models.FloatField(help_text="Its size against the portfolio, as a fraction.")

    class Meta:
        ordering: ClassVar[list[str]] = ["-date", "instrument"]

    def __str__(self) -> str:
        return f"{self.get_side_display()} {self.instrument} on {self.date:%Y-%m-%d}"


class Income(models.Model):
    """Dividends, interest, tax withheld and fees, each as a share of the portfolio."""

    class Kind(models.TextChoices):
        DIVIDEND = "dividend", "Dividend"
        TAX = "tax", "Tax withheld"
        INTEREST = "interest", "Interest"
        FEE = "fee", "Fee"

    ibkr_id = models.CharField("IBKR transaction ID", max_length=30, unique=True)
    date = models.DateField()
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, null=True, blank=True, related_name="income"
    )
    kind = models.CharField(max_length=10, choices=Kind)
    weight = models.FloatField(
        help_text="Against the portfolio, as a fraction. Costs are negative."
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-date"]
        verbose_name_plural = "income"

    def __str__(self) -> str:
        return f"{self.get_kind_display()} on {self.date:%Y-%m-%d}"


class PriceSeries(models.Model):
    """Prices from outside the account, such as a benchmark's, which IBKR's reports don't have."""

    key = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    currency = models.CharField(max_length=3, default="GBP")
    source = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["key"]
        verbose_name_plural = "price series"

    def __str__(self) -> str:
        return self.name


class Price(models.Model):
    series = models.ForeignKey(PriceSeries, on_delete=models.CASCADE, related_name="prices")
    date = models.DateField()
    close = models.FloatField()

    class Meta:
        ordering: ClassVar[list[str]] = ["series", "date"]
        constraints: ClassVar[list] = [
            models.UniqueConstraint(fields=["series", "date"], name="one_price_a_day"),
        ]

    def __str__(self) -> str:
        return f"{self.series} on {self.date:%Y-%m-%d}"


class ImportRun(models.Model):
    """A record of each import, so a missed or failed one can be seen."""

    class Status(models.TextChoices):
        OK = "ok", "OK"
        FAILED = "failed", "Failed"

    started = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=200)
    status = models.CharField(max_length=6, choices=Status)
    period_from = models.DateField(null=True, blank=True)
    period_to = models.DateField(null=True, blank=True)
    days = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-started"]

    def __str__(self) -> str:
        return f"{self.get_status_display()} at {self.started:%Y-%m-%d %H:%M}"
