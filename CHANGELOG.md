# Changelog

## 0.3.0 (2026-11-11)

Its API on its page (plugin API 2.2, liminal-libs 1.49.0; the user: "each plugin should reflect the the API its attached
to, and present links that provide documentation, the plugin interface should more or less contain what it already has,
BUT, it should also expose more of what the API is about"). `TwsePlugin.apis` declares the two things it talks to, read
from TWSE's own pages on 2026-11-11 (`apis.py`):

- the **TWSE OpenAPI** (openapi.twse.com.tw): its Swagger reference and specification, all seven of its groups (143
  calls), the one call it makes (`STOCK_DAY_ALL`, the day's table of every listed stock) among 21 others worth knowing,
  its license (Taiwan's Open Government Data License 1.0) and TWSE's terms;
- **TWSE's website reports** (www.twse.com.tw): its Market Info menu in ten parts, each with its page, the call it makes
  (`/exchangeReport/STOCK_DAY`, a stock's month of days) and the addresses the site's own pages ask now
  (`/rwd/{lang}/...`), and TWSE's terms of use, whose section 6 forbids downloading the site's data with automated tools
  unless TWSE agreed to the method (said on the card; the plugin asks as before).

`api_facts()` says what its clients learned while they ran, asking nothing: the requests made, the last answer's clock,
and the day `STOCK_DAY_ALL` was of (`facts.py`: each client held weakly, its last words kept when it goes). Tests: the
contract at 2.2, the card's calls the ones its source sends, the facts, and every page it names answering (only with
`LIMINAL_VENDOR_PAGES=1`). On liminal-libs 1.49.0 or later; every behaviour, limit and string as in 0.2.0.

## 0.2.0 (2026-11-03)

Renamed `plugin-integrator-twse` (the package `plugin_integrator_twse`; it was `liminal-plugin-twse`) on 2026-11-03: the naming by system (plugins are `plugin-<app>-<name>`), on liminal-libs 1.4.0 (`liminal_libs`, the library renamed with it).

A class on plugin API 2.0 (liminal-libs 1.3.0; the user: "all the plugins under liminal should basically follow
inheritance/oop paradigm"): `TwsePlugin(FeedPlugin)`, what the `Provider` record declared as class attributes
and its callbacks as methods (`build`, `markets`, `rate`), `PLUGIN` its instance; it declares its publication
delay itself too (`delays`: each day's bars once the day is over, the row the library held for the `twse`
plan). Every behaviour, limit and string as in 1.0.0. Versioned 0.2.0 with every Liminal distribution of the
release (its `release/0.2.0` branch; CI against the library's).

## 1.0.0 (2026-11-02)

The Taiwan Stock Exchange's daily bars from TWSE's open data (the user: "update existing plugins, add exchanges
where applicable and symbols, and if new sources, create a new plugin"): every listed stock, stored as `2330.TW`
(the library's notation, plugin API 1.12: `Provider.exchanges` = XTAI), a stock-month a request from the site's
`STOCK_DAY` page (from 2010-01-04; ROC dates, numbers with commas, "--" for a day without a trade), the listings,
names and records from the OpenAPI's `STOCK_DAY_ALL` table (one request a run); a day under way is never served
(final once TWSE has published its close, by 15:00 Taipei). No key; 10 requests a minute, 600 a run, 2,000 a day.
