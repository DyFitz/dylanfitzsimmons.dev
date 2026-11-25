import pytest

from apps.investments.models import Instrument, Portfolio
from apps.investments.tests.samples import START


@pytest.fixture
def portfolio(db):
    """The portfolio set up from the sample report's first day, with no instruments yet."""
    Portfolio.objects.all().delete()
    Instrument.objects.all().delete()
    return Portfolio.objects.create(inception=START)
