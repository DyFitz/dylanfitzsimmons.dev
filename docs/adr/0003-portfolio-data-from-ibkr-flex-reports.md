# 3. Portfolio data from IBKR Flex reports

- Status: accepted
- Date: 2026-11-08

## Context

The portfolio page shows holdings and performance from an Interactive Brokers account. IBKR offers individual account holders two programmatic routes:

- **The Web API**, through the Client Portal Gateway. It needs a browser login on the same machine as the gateway, allows one session per username, and that session can place trades.
- **The Flex Web Service**, which returns reports configured in advance. It authenticates with a read-only token that expires after at most a year and can be restricted to one IP address. Activity reports refresh once a day, after the close of business.

## Decision

Use the Flex Web Service. A scheduled management command fetches the previous day's Activity report each morning, parses the XML and stores a dated snapshot. The page reads from the database, never from IBKR directly, and says when the data is from.

Show weights and percentage returns rather than money values. Don't republish live market quotes, which are licensed for personal use only.

## Consequences

- No brokerage credentials, and nothing able to trade, live on a public server.
- The page is a daily view, not a live one. That suits a long-term portfolio and avoids market data licensing problems.
- Stored snapshots build a history the site owns, so returns, volatility and drawdown are calculated here rather than copied from IBKR.
- The token expires, so the fetch job must alert on failure, and renewing the token is a yearly task.
