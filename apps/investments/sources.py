"""Where the daily update gets its data: IBKR's Flex Web Service for the account, the Bank of
England for SONIA, and CSV files for any price history that has to be filled in by hand."""

import csv
import io
import re
import time

# The responses come from IBKR and FRED, and Python's own parser doesn't fetch
# external entities and refuses entity expansion attacks, so it is safe to use here.
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date, datetime
from statistics import median
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

FLEX_BASE = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
# The Bank of England's own database turns away requests from cloud servers, so SONIA comes
# from FRED, the St. Louis Fed's database, which republishes the Bank's series unchanged.
SONIA_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
# The SONIA Compounded Index: SONIA's daily rate built up into an index, so a period's return
# is one value over another.
SONIA_SERIES = "IUDZOS2"
# Both services sit behind firewalls that turn away requests which don't look like a browser.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0 Safari/537.36"
)
# IBKR's "the report is still being made" and "try again shortly".
NOT_READY = {"1019", "1021"}


class SourceError(RuntimeError):
    """A source couldn't be reached, or sent something unusable."""


def _gist(data: bytes) -> str:
    """The start of a reply, as plain text, to show what came back instead of the data."""
    text = data[:4000].decode("utf-8", errors="replace")
    # Error pages put their styles first, which would fill the summary before the message.
    text = re.sub(r"<(style|script)\b.*?</\1\s*>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())[:200]


def _get(url: str, opener=urlopen, timeout: float = 60) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    request = Request(url, headers=headers)  # noqa: S310 - fixed https URLs
    try:
        with opener(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        reply = _gist(error.read() or b"")
        raise SourceError(
            f"Couldn't reach {url.split('?')[0]}: {error}" + (f" ({reply})" if reply else "")
        ) from error
    except OSError as error:
        raise SourceError(f"Couldn't reach {url.split('?')[0]}: {error}") from error


def _flex_reply(data: bytes) -> ET.Element | None:
    """IBKR's status reply, or None if the data is the report itself."""
    try:
        root = ET.fromstring(data)  # noqa: S314
    except ET.ParseError as error:
        raise SourceError(f"IBKR sent something that isn't XML: {error}") from error
    return root if root.tag == "FlexStatementResponse" else None


def fetch_flex_report(
    token: str,
    query_id: str,
    *,
    opener=urlopen,
    sleep: Callable[[float], None] = time.sleep,
    tries: int = 10,
    wait: float = 15,
) -> bytes:
    """Asks IBKR to make the report, then collects it, waiting while it's being made."""
    if not token or not query_id:
        raise SourceError("IBKR_FLEX_TOKEN and IBKR_FLEX_QUERY_ID need to be set.")
    asked = _flex_reply(
        _get(f"{FLEX_BASE}/SendRequest?{urlencode({'t': token, 'q': query_id, 'v': 3})}", opener)
    )
    if asked is None or asked.findtext("Status") != "Success":
        code = asked.findtext("ErrorCode") if asked is not None else "?"
        message = asked.findtext("ErrorMessage") if asked is not None else "no reply"
        raise SourceError(f"IBKR refused the request ({code}): {message}")
    reference = asked.findtext("ReferenceCode")
    url = asked.findtext("Url") or f"{FLEX_BASE}/GetStatement"
    for attempt in range(tries):
        data = _get(f"{url}?{urlencode({'t': token, 'q': reference, 'v': 3})}", opener)
        reply = _flex_reply(data)
        if reply is None:
            return data
        code = reply.findtext("ErrorCode")
        if code not in NOT_READY:
            raise SourceError(
                f"IBKR couldn't send the report ({code}): {reply.findtext('ErrorMessage')}"
            )
        if attempt < tries - 1:
            sleep(wait)
    raise SourceError(f"IBKR was still making the report after {tries} tries.")


def fetch_sonia(since: date, *, opener=urlopen) -> list[tuple[date, float]]:
    """The SONIA Compounded Index, from `since` to the latest, by way of FRED."""
    query = urlencode({"id": SONIA_SERIES, "cosd": since.isoformat()})
    data = _get(f"{SONIA_URL}?{query}", opener, timeout=20)
    rows = read_prices(data.decode("utf-8-sig", errors="replace"))
    if not rows:
        raise SourceError(f"FRED sent no SONIA figures: {_gist(data)!r}")
    return rows


# ---------------------------------------------------------------- price files

DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d %b %Y",
    "%d-%b-%Y",
    "%d-%b-%y",
    "%d/%m/%y",
    "%b %d, %Y",
    "%m/%d/%Y",
    "%Y%m%d",
)
# The column holding the price, in order of preference. An adjusted close already allows for
# dividends, but an accumulating fund has none, so either serves.
CLOSE_COLUMNS = ("adj close", "close", "price", "last", SONIA_SERIES.lower())


def _date(text: str) -> date | None:
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()  # noqa: DTZ007
        except ValueError:
            continue
    return None


def _number(text: str) -> float | None:
    try:
        return float(
            text.replace(",", "").replace("£", "").replace("$", "").replace("p", "").strip()
        )
    except ValueError:
        return None


def read_prices(text: str) -> list[tuple[date, float]]:
    """(date, close) from a CSV of daily prices, in date order.

    Takes the usual layouts: a header row naming a date column and a close or price column, as
    price sites and FRED give them. Rows without a date or a number are skipped.
    """
    text = text.strip()
    # A table copied from a web page and pasted into a text file is separated by tabs.
    first = text.split("\n", 1)[0]
    reader = csv.reader(io.StringIO(text), delimiter="\t" if "\t" in first else ",")
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return []
    # Yahoo marks its columns "Close*" and "Adj Close**", so only letters and spaces count.
    header = [
        "".join(c for c in cell.lower() if c.isalnum() or c == " ").strip() for cell in rows[0]
    ]
    date_col = next((i for i, h in enumerate(header) if "date" in h), 0)
    close_col = next((header.index(c) for c in CLOSE_COLUMNS if c in header), len(header) - 1)
    out = {}
    for row in rows[1:]:
        if max(date_col, close_col) >= len(row):
            continue
        day, close = _date(row[date_col]), _number(row[close_col])
        if day and close:
            out[day] = close
    return sorted(out.items())


def match_units(
    new: list[tuple[date, float]], known: dict[date, float]
) -> tuple[list[tuple[date, float]], float]:
    """Rescales prices quoted in pence to pounds, or the other way, to match those already kept.

    IBKR gives London prices in pounds, while most price sites give them in pence. Where the
    two overlap and differ by about a hundred times, the new ones are rescaled.
    Returns the prices and the factor used.
    """
    ratios = [known[d] / close for d, close in new if d in known and close]
    if not ratios:
        return new, 1.0
    ratio = median(ratios)
    for factor in (0.01, 100.0):
        if 0.8 * factor < ratio < 1.25 * factor:
            return [(d, close * factor) for d, close in new], factor
    return new, 1.0
