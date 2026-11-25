"""A small made-up Flex report whose figures can be worked out by hand.

    5 Jan  £1,000 paid in, all cash. The record starts here.
    6 Jan  Buys 10 AAA at £50 (closes at £52) and 2 BBB at $100 with $1 = £0.80 (closes at $105).
           Value: £340 cash + £520 + £168 = £1,028.
    7 Jan  AAA closes at £54. BBB closes at $110, but $1 = £0.75, so it is worth less in pounds.
           Value: £340 + £540 + £165 = £1,045.
    8 Jan  £100 paid in, a £5 dividend from AAA, and 4 AAA sold at £55 (closes at £54).
           Value: £665 + £324 + £165 = £1,154.

`scale` multiplies every amount of money and every holding's size, but no price, so the stored
weights and returns should come out exactly the same.
"""

from datetime import date

AAA, BBB = 1001, 2002
# The day the sample record starts.
START = date(2026, 1, 5)

DAYS = [("20260102", 0, 0), ("20260105", 1000, 1000), ("20260106", 1028, 340),
        ("20260107", 1045, 340), ("20260108", 1154, 665)]  # fmt: skip


def report(scale: float = 1, *, extra: str = "") -> str:
    def money(value: float) -> str:
        return repr(value * scale)

    values = "".join(
        f'<EquitySummaryReportInBase reportDate="{day}" total="{money(total)}" '
        f'cash="{money(cash)}" currency="GBP"/>'
        for day, total, cash in DAYS
    )
    aaa = 'conid="1001" symbol="AAAl" listingExchange="LSE" currency="GBP" assetCategory="STK"'
    bbb = 'conid="2002" symbol="BBB" listingExchange="NYSE" currency="USD" assetCategory="STK"'
    return f"""<FlexQueryResponse queryName="test" type="AF"><FlexStatements count="1">
<FlexStatement accountId="DU0000000" fromDate="20260102" toDate="20260108">
<EquitySummaryInBase>{values}</EquitySummaryInBase>
<OpenPositions>
  <OpenPosition {aaa} position="{money(6)}" markPrice="54" percentOfNAV="30"/>
  <OpenPosition {bbb} position="{money(2)}" markPrice="110" percentOfNAV="15"/>
</OpenPositions>
<PriorPeriodPositions>
  <PriorPeriodPosition {aaa} date="20260107" price="54" fxRateToBase="1" priorMtmPnl="1"/>
  <PriorPeriodPosition {bbb} date="20260107" price="110" fxRateToBase="0.75" priorMtmPnl="1"/>
  <PriorPeriodPosition {aaa} date="20260108" price="54" fxRateToBase="1" priorMtmPnl="1"/>
  <PriorPeriodPosition {bbb} date="20260108" price="110" fxRateToBase="0.75" priorMtmPnl="1"/>
</PriorPeriodPositions>
<Trades>
  <Trade {aaa} transactionID="t1" tradeDate="20260106" quantity="{money(10)}"
    tradeMoney="{money(500)}" closePrice="52" fxRateToBase="1"/>
  <Trade {bbb} transactionID="t2" tradeDate="20260106" quantity="{money(2)}"
    tradeMoney="{money(200)}" closePrice="105" fxRateToBase="0.8"/>
  <Trade {aaa} transactionID="t3" tradeDate="20260108" quantity="{money(-4)}"
    tradeMoney="{money(-220)}" closePrice="54" fxRateToBase="1"/>
  <Trade conid="12087792" symbol="GBP.USD" assetCategory="CASH" transactionID="t4"
    tradeDate="20260106" quantity="{money(-160)}" tradeMoney="{money(-200)}" fxRateToBase="1"/>
</Trades>
<CashTransactions>
  <CashTransaction type="Deposits/Withdrawals" currency="GBP" fxRateToBase="1"
    dateTime="20260105;120000" amount="{money(1000)}" transactionID="c1" levelOfDetail="DETAIL"/>
  <CashTransaction type="Deposits/Withdrawals" currency="GBP" fxRateToBase="1"
    dateTime="20260108;120000" amount="{money(100)}" transactionID="c2" levelOfDetail="DETAIL"/>
  <CashTransaction {aaa} type="Dividends" fxRateToBase="1"
    dateTime="20260108;120000" amount="{money(5)}" transactionID="c3" levelOfDetail="DETAIL"/>
  <CashTransaction {aaa} type="Dividends" fxRateToBase="1"
    dateTime="20260108" amount="{money(5)}" transactionID="" levelOfDetail="SUMMARY"/>
</CashTransactions>
<SecuritiesInfo>
  <SecurityInfo {aaa} description="AAA PLC" isin="GB0000000001" issuerCountryCode="GB"
    subCategory="COMMON"/>
  <SecurityInfo {bbb} description="BBB INC" isin="US0000000002" issuerCountryCode="US"
    subCategory="COMMON"/>
</SecuritiesInfo>
{extra}
</FlexStatement></FlexStatements></FlexQueryResponse>"""
