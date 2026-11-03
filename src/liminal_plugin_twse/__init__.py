"""The Taiwan Stock Exchange (twse.com.tw) for Liminal: every listed stock's daily bars from TWSE's own
open data, no key. A live feed: each trading day's bars come once TWSE has published its close.

Two public endpoints, checked 2026-11-02:

- the OpenAPI's STOCK_DAY_ALL (https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL): the latest
  trading day's bars of every listed stock in one answer (1,389 rows of Date in the ROC calendar,
  1151102, Code, Name, TradeVolume, TradeValue, OpeningPrice, HighestPrice, LowestPrice,
  ClosingPrice, Change, Transaction), read once a run: the listings and their names, a stock's record;
- the site's STOCK_DAY (https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=YYYYMMDD&stockNo=CODE):
  one stock's days of one month (stat "OK"; fields 日期 (the ROC date, 115/11/02), 成交股數, 成交金額,
  開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數, 註記; numbers with commas, "--" where a day had no
  trade), from 2010-01-04: the history, a stock-month a request.

A listing is stored as 2330.TW (the library's notation for a listing abroad; `TWSE:2330` and
`2330::XTAI` mean the same) and asked for by its code. Its days are the exchange's own calendar days
(every weekday, until the library carries Taiwan's holidays), each day bar stamped at midnight New
York of the Taipei date like every stock's, its volume in shares, its vwap the day's value over its
shares. TPEx, the over-the-counter board (ROCO, .TWO), is a follow-up: its OpenAPI's endpoints were
not verified.

A Liminal plugin released on its own (liminal_lib.sources.registry: Provider), registered under the
entry point group `liminal.providers`. It relies on plugin API 1.12 (Provider.exchanges: the Taiwan
Stock Exchange's listings, XTAI, and no US listing) and nothing of the app outside it; its version is
this distribution's (pyproject.toml).
"""
from __future__ import annotations

from datetime import date

from liminal_lib.config import Tier
from liminal_lib.sources.registry import Provider, public_client
from .client import OPENAPI, WWW, TwseSource

# its plan and caps: a public site with no published limits whose data pages refuse bursts; asked slowly
TIER = Tier("twse", requests_per_minute=10, history_years=None, history_start=date(2010, 1, 4))
PER_RUN, PER_DAY = 600, 2000


def build(settings, request_budget):
    """The two hosts, each on the library's keyless client (a client keeps its key, here none, to its
    own host), both counted under the feed's name: one window, one daily cap for the machine."""
    return TwseSource(public_client("twse", WWW, settings, request_budget), public_client("twse", OPENAPI, settings, None))


PLUGIN = Provider(
    api="1.12",  # the contract it needs (Provider.exchanges); its version: the distribution's
    name="twse", title="Taiwan Stock Exchange", build=build, assets=frozenset({"stock"}), order=110,
    about="every listed stock's daily bars from TWSE's open data, from 2010 (no key)",
    exchanges=frozenset({"XTAI"}),  # its own listings alone, stored as 2330.TW
    tier=TIER, per_run=PER_RUN, per_day=PER_DAY,
    limits="none published; its data pages refuse bursts (kept at 10 requests a minute)",
    kind="exchange", markets=lambda settings: {"stock": "twse"},
    provides={"stock": ("day",)}, per_request={"day": 22},  # a stock-month a request
    bulk_resolution="day", rate=lambda settings: (10, 60.0),
)
