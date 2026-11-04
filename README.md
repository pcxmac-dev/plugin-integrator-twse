# plugin-integrator-twse

The Taiwan Stock Exchange for [Liminal](https://github.com/pcxmac-dev/liminal-charts): every listed
stock's daily bars from TWSE's own open data, from 2010, no key. A live feed: each trading day's bars
come once TWSE has published its close (by 15:00 Taipei).

A Liminal provider plugin released on its own. The app finds it through the entry point group
`liminal.providers` and lists it on the Plugins view and in `liminal-charts plugins`
as `package: plugin-integrator-twse`, with this package's version.

## What it serves

- Every stock listed on the Taiwan Stock Exchange (XTAI), under the library's name for a listing
  abroad: `2330.TW` (`TWSE:2330` and `2330::XTAI` mean the same). Daily bars only, a stock-month a
  request (the site's `STOCK_DAY` page, from 2010-01-04), each day's volume in shares and its vwap the
  day's value over its shares; the directory's listings and names, and a stock's record, from the
  OpenAPI's `STOCK_DAY_ALL` table (one request a run).
- A listing's days are the exchange's own calendar days (every weekday, until the library carries
  Taiwan's holidays); day bars are stamped at midnight New York of the Taipei date like every stock's.
- Not yet: TPEx, the over-the-counter board (`.TWO`), a follow-up once its OpenAPI's endpoints are
  verified.

## Install

Into the app's environment, from the app's folder:

```powershell
.venv\Scripts\python.exe -m pip install "plugin-integrator-twse @ git+https://github.com/pcxmac-dev/plugin-integrator-twse@v0.2.0"
```

or with the app's plugins (`pip install -e ".[plugins]"` in liminal-charts). The app loads it on its next
start. No key or setting is needed; it is asked at 10 requests a minute, 600 a run and 2,000 a day
(TWSE publishes no limits; its data pages refuse bursts).

## Compatibility

It is written for plugin API 2.0 (`PLUGIN.api`: the class contract, `TwsePlugin` a `FeedPlugin` of
liminal-libs 1.3.0 or later; the exchanges a feed carries, `exchanges`, among what it declares). An app
offering 2.0 or a later 2.x loads it; an app of another major, or one older than 2.0, leaves it out
and says why on the Plugins view.

## Develop

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install "liminal-libs @ git+https://github.com/pcxmac-dev/liminal-libs@main"
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q
```

Tests never send requests (a fake session answers) and never read your keys.
