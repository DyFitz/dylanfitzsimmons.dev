"""Reads an IBKR Activity Flex report (XML) into plain records.

The report needs these sections: Net Asset Value in Base, Open Positions, Prior Period
Positions, Trades, Cash Transactions and Financial Instrument Information. Amounts here are
still the account's own; the importer turns them into weights and returns.
"""

# The report comes from IBKR, and Python's own parser doesn't fetch external entities and
# refuses entity expansion attacks (expat 2.4.1 and later), so it is safe to use here.
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime

# Cash transaction types, by what the importer does with them. Anything else is ignored.
FLOWS = {"Deposits/Withdrawals"}
INCOME_KINDS = {
    "Dividends": "dividend",
    "Payment In Lieu Of Dividends": "dividend",
    "Withholding Tax": "tax",
    "871(m) Withholding": "tax",
    "Broker Interest Received": "interest",
    "Broker Interest Paid": "interest",
    "Bond Interest Received": "interest",
    "Bond Interest Paid": "interest",
    "Other Fees": "fee",
    "Commission Adjustments": "fee",
}


class FlexError(ValueError):
    """The file isn't a report the importer can use."""


@dataclass(frozen=True)
class Security:
    conid: int
    symbol: str
    name: str
    isin: str
    currency: str
    kind: str
    exchange: str
    country: str


@dataclass(frozen=True)
class Trade:
    ibkr_id: str
    conid: int
    day: date
    quantity: float  # negative for a sale
    money: float  # in its own currency, negative for a sale
    close: float  # that day's closing price
    fx: float


@dataclass(frozen=True)
class CashItem:
    ibkr_id: str
    day: date
    conid: int | None
    kind: str  # "flow", or one of INCOME_KINDS' values
    amount: float  # in pounds


@dataclass
class Statement:
    start: date
    end: date
    securities: dict[int, Security] = field(default_factory=dict)
    # Each day's total value and cash, in pounds.
    values: dict[date, float] = field(default_factory=dict)
    cash: dict[date, float] = field(default_factory=dict)
    # Units held at the end of the report.
    closing: dict[int, float] = field(default_factory=dict)
    # (contract, day) -> (closing price, pounds per unit of its currency).
    prices: dict[tuple[int, date], tuple[float, float]] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    cash_items: list[CashItem] = field(default_factory=list)


def _day(text: str) -> date:
    # Dates come as yyyyMMdd, sometimes followed by ";HHmmss" for a time.
    return datetime.strptime(text[:8], "%Y%m%d").date()  # noqa: DTZ007


def _number(element: ET.Element, name: str) -> float:
    value = element.get(name, "")
    return float(value) if value not in ("", "--") else 0.0


def _symbol(symbol: str, exchange: str) -> str:
    # IBKR adds a lower-case "l" to London tickers (BPl for BP), which nobody else uses.
    if exchange == "LSE" and symbol.endswith("l") and symbol[:-1].isupper():
        return symbol[:-1]
    return symbol


def _section(statement: ET.Element, name: str, *, required: bool = True) -> list[ET.Element]:
    section = statement.find(name)
    if section is None:
        if required:
            raise FlexError(f"The report has no {name} section.")
        return []
    return list(section)


def _security(element: ET.Element) -> Security:
    exchange = element.get("listingExchange", "")
    return Security(
        conid=int(element.get("conid", "0")),
        symbol=_symbol(element.get("symbol", ""), exchange),
        name=element.get("description", ""),
        isin=element.get("isin", ""),
        currency=element.get("currency", ""),
        kind=" / ".join(filter(None, (element.get("assetCategory"), element.get("subCategory")))),
        exchange=exchange,
        country=element.get("issuerCountryCode", ""),
    )


def parse(data: bytes | str) -> Statement:
    try:
        root = ET.fromstring(data)  # noqa: S314
    except ET.ParseError as error:
        raise FlexError(f"The file isn't valid XML: {error}") from error
    if root.tag == "FlexStatementResponse" or root.find("FlexStatements") is None:
        # What the web service sends while a report is still being made, or an error.
        message = root.findtext(".//ErrorMessage") or "The file isn't an IBKR Flex report."
        raise FlexError(message)
    statements = root.findall(".//FlexStatement")
    if len(statements) != 1:
        raise FlexError("The report should cover one account.")
    element = statements[0]
    statement = Statement(
        start=_day(element.get("fromDate", "")), end=_day(element.get("toDate", ""))
    )

    for row in _section(element, "SecuritiesInfo"):
        security = _security(row)
        statement.securities[security.conid] = security

    for row in _section(element, "EquitySummaryInBase"):
        day = _day(row.get("reportDate", ""))
        statement.values[day] = _number(row, "total")
        statement.cash[day] = _number(row, "cash")

    for row in _section(element, "OpenPositions"):
        conid = int(row.get("conid", "0"))
        statement.securities.setdefault(conid, _security(row))
        statement.closing[conid] = statement.closing.get(conid, 0.0) + _number(row, "position")

    for row in _section(element, "PriorPeriodPositions"):
        conid = int(row.get("conid", "0"))
        statement.securities.setdefault(conid, _security(row))
        key = (conid, _day(row.get("date", "")))
        statement.prices[key] = (_number(row, "price"), _number(row, "fxRateToBase") or 1.0)

    for row in _section(element, "Trades"):
        # Currency conversions are trades too, but not of anything the portfolio holds.
        if row.tag != "Trade" or row.get("assetCategory") == "CASH":
            continue
        conid = int(row.get("conid", "0"))
        statement.securities.setdefault(conid, _security(row))
        statement.trades.append(
            Trade(
                ibkr_id=row.get("transactionID") or row.get("tradeID", ""),
                conid=conid,
                day=_day(row.get("tradeDate", "")),
                quantity=_number(row, "quantity"),
                money=_number(row, "tradeMoney"),
                close=_number(row, "closePrice"),
                fx=_number(row, "fxRateToBase") or 1.0,
            )
        )

    for row in _section(element, "CashTransactions"):
        kind = "flow" if row.get("type") in FLOWS else INCOME_KINDS.get(row.get("type", ""))
        # Summary rows repeat the detail rows' totals.
        if kind is None or row.get("levelOfDetail", "DETAIL") != "DETAIL":
            continue
        conid = row.get("conid")
        statement.cash_items.append(
            CashItem(
                ibkr_id=row.get("transactionID", ""),
                day=_day(row.get("dateTime") or row.get("reportDate", "")),
                conid=int(conid) if conid else None,
                kind=kind,
                amount=_number(row, "amount") * (_number(row, "fxRateToBase") or 1.0),
            )
        )

    if not statement.values:
        raise FlexError("The report has no daily values. Is Net Asset Value in Base included?")
    return statement
