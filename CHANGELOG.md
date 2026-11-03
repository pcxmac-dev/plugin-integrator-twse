# Changelog

## 1.0.0 (2026-11-02)

The Taiwan Stock Exchange's daily bars from TWSE's open data (the user: "update existing plugins, add exchanges
where applicable and symbols, and if new sources, create a new plugin"): every listed stock, stored as `2330.TW`
(the library's notation, plugin API 1.12: `Provider.exchanges` = XTAI), a stock-month a request from the site's
`STOCK_DAY` page (from 2010-01-04; ROC dates, numbers with commas, "--" for a day without a trade), the listings,
names and records from the OpenAPI's `STOCK_DAY_ALL` table (one request a run); a day under way is never served
(final once TWSE has published its close, by 15:00 Taipei). No key; 10 requests a minute, 600 a run, 2,000 a day.
