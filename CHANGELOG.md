# Changelog

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
