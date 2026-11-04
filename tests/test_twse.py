"""The TWSE plugin: its month pages and whole-market table read (fakes shaped like the answers seen
2026-11-02), the ticker and date forms, the day under way left out, and the app loading it from this
package with its own version and facts. No request is ever sent."""
from __future__ import annotations

from datetime import date, datetime, timezone
from importlib.metadata import version

import pytest

from liminal_libs import composite, freshness
from liminal_libs.collector import history_floor
from liminal_libs.config import load_settings
from liminal_libs.errors import NotEntitled, SourceError
from liminal_libs.freshness import Delay
from liminal_libs.sources import is_archive, markets, provider, rate_window, registry, supports
from liminal_libs.sources.archive import ET, ms
from liminal_libs.sources.http import PublicClient
from liminal_libs.symbols import resolve

import plugin_integrator_twse as twse
from plugin_integrator_twse import PER_DAY, PER_RUN, TIER
from plugin_integrator_twse.client import (OPENAPI, TAIPEI, WWW, TwseSource, listing_type, number, read_month, roc_date,
                                        twse_code)

from .conftest import FakeResponse, FakeSession

FIELDS = ["日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌價差", "成交筆數", "註記"]
NOVEMBER = {"stat": "OK", "date": "20261101", "title": "115年11月 2330 台積電 各日成交資訊", "fields": FIELDS,
            "data": [["115/11/02", "41,165,068", "95,950,896,264", "2,310.00", "2,345.00", "2,310.00", "2,330.00", "-40.00", "298,087", ""],
                     ["115/11/03", "36,567,000", "84,242,030,000", "2,300.00", "2,335.00", "2,280.00", "2,295.00", "-35.00", "17,745", ""]]}
OCTOBER = {"stat": "OK", "date": "20261001", "title": "115年10月 2330 台積電 各日成交資訊", "fields": FIELDS,
           "data": [["115/10/30", "0", "0", "--", "--", "--", "--", "X0.00", "0", ""],
                    ["115/10/31", "30,000,000", "70,500,000,000", "2,340.00", "2,360.00", "2,330.00", "2,350.00", "+10.00", "200,000", ""]]}
MARKET = [{"Date": "1151102", "Code": "2330", "Name": "台積電", "TradeVolume": "41165068", "TradeValue": "95950896264",
           "OpeningPrice": "2310.00", "HighestPrice": "2345.00", "LowestPrice": "2310.00", "ClosingPrice": "2330.00",
           "Change": "-40.0000", "Transaction": "298087"},
          {"Date": "1151102", "Code": "0050", "Name": "元大台灣50", "TradeVolume": "9000000", "TradeValue": "900000000",
           "OpeningPrice": "100.00", "HighestPrice": "101.00", "LowestPrice": "99.50", "ClosingPrice": "100.50",
           "Change": "0.5000", "Transaction": "12000"},
          {"Date": "1151102", "Code": "00400A", "Name": "主動統一台灣高息", "TradeVolume": "40358170", "TradeValue": "552309165",
           "OpeningPrice": "13.60", "HighestPrice": "13.88", "LowestPrice": "13.53", "ClosingPrice": "13.79",
           "Change": "-0.0100", "Transaction": "10836"}]


def _source(www=(), openapi=(), now=None):
    s1, s2 = FakeSession(list(www)), FakeSession(list(openapi))
    src = TwseSource(PublicClient(WWW, session=s1, sleep=lambda s: None), PublicClient(OPENAPI, session=s2, sleep=lambda s: None),
                     now=now)
    return src, s1, s2


def _at(d: date, hour: int, minute: int = 0):
    return lambda: datetime(d.year, d.month, d.day, hour, minute, tzinfo=TAIPEI)


def test_a_stocks_days_come_a_month_a_request_without_the_day_under_way():
    src, www, _ = _source([FakeResponse(200, OCTOBER), FakeResponse(200, NOVEMBER)], now=_at(date(2026, 11, 3), 10))
    pages = list(src.bar_pages("2330.TW", date(2026, 10, 1), date(2026, 11, 30), "day"))
    assert [c[1] for c in www.calls] == [{"response": "json", "date": "20261001", "stockNo": "2330"},
                                         {"response": "json", "date": "20261101", "stockNo": "2330"}]
    assert www.calls[0][0] == "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
    bars = [b for page in pages for b in page]
    assert [b["t"] for b in bars] == [ms(datetime(2026, 10, 31, tzinfo=ET)), ms(datetime(2026, 11, 2, tzinfo=ET))]
    nov2 = bars[1]  # the day without a trade is none; November 3 is under way at 10:00 Taipei
    assert (nov2["o"], nov2["h"], nov2["l"], nov2["c"], nov2["v"], nov2["n"]) == (2310.0, 2345.0, 2310.0, 2330.0, 41165068.0, 298087)
    assert round(nov2["vw"], 2) == 2330.88  # the day's value over its shares
    assert src.requests_made == 2
    # after the close is published the day is served, from the month kept for the run
    src.now = _at(date(2026, 11, 3), 15, 30)
    (page,) = src.bar_pages("2330.TW", date(2026, 11, 1), date(2026, 11, 30), "day")
    assert [b["c"] for b in page] == [2330.0, 2295.0] and len(www.calls) == 2
    newest = list(src.bar_pages("2330.TW", date(2026, 10, 1), date(2026, 11, 30), "day", descending=True, limit=1))
    assert [[b["c"] for b in p] for p in newest] == [[2295.0]]
    assert list(src.bar_pages("2330.TW", date(2026, 12, 1), date(2026, 12, 31), "day")) == []  # nothing final yet: no request
    assert list(src.bar_pages("2330.TW", date(2009, 1, 1), date(2009, 12, 31), "day")) == []  # before its history
    assert len(www.calls) == 2
    with pytest.raises(NotEntitled):
        next(src.bar_pages("2330.TW", date(2026, 11, 1), date(2026, 11, 30), "minute"))
    with pytest.raises(NotEntitled):
        next(src.bar_pages("BRK.B", date(2026, 11, 1), date(2026, 11, 30), "day"))


def test_the_month_page_is_read_by_its_columns_and_refused_when_they_change():
    assert read_month({"stat": "很抱歉，沒有符合條件的資料!"}) == []  # a month before the listing
    with pytest.raises(SourceError):
        read_month({"stat": "error"})
    with pytest.raises(SourceError):
        read_month({"stat": "OK", "fields": ["日期", "收盤價"], "data": []})
    with pytest.raises(SourceError):
        read_month("<html>")
    shuffled = {"stat": "OK", "fields": FIELDS[::-1], "data": [list(reversed(NOVEMBER["data"][0]))]}
    (bar,) = read_month(shuffled)  # the columns by name, whatever their order
    assert bar["c"] == 2330.0 and bar["v"] == 41165068.0
    assert read_month({"stat": "OK", "fields": FIELDS, "data": [["bad date"] + ["1"] * 9, ["115/11/02", "1"]]}) == []
    assert roc_date("1151102") == date(2026, 11, 2) == roc_date("115/11/02") and roc_date("115") is None
    assert roc_date("115/13/02") is None
    assert number("2,310.00") == 2310.0 and number("--") is None and number("") is None and number(None) is None
    assert twse_code("2330.TW") == "2330" == twse_code("2330") == twse_code(" 2330.tw ") and twse_code("BRK.B") == "BRK.B"
    assert listing_type("2330") == "CS" and listing_type("0050") == "ETF" and listing_type("00400A") == "ETF"
    assert listing_type("030001") == "OTHER"


def test_the_listings_names_and_a_stocks_record_come_from_the_days_table_once():
    src, www, openapi = _source(openapi=[FakeResponse(200, MARKET)])
    rows = src.listings("XTAI")
    assert [r["ticker"] for r in rows] == ["2330.TW", "0050.TW", "00400A.TW"]
    assert rows[0] == {"ticker": "2330.TW", "name": "台積電", "exchange": "XTAI", "type": "CS", "figi": None, "kind": "stock"}
    assert [r["type"] for r in rows] == ["CS", "ETF", "ETF"]
    inst = src.instrument("2330.TW")
    assert inst.ticker == "2330.TW" and inst.name == "台積電" and inst.primary_exchange.mic == "XTAI" and inst.currency == "TWD"
    assert inst.active and inst.list_date is None and inst.details["Code"] == "2330"
    gone = src.instrument("9999.TW")
    assert gone.ticker == "9999.TW" and not gone.active and gone.list_date is None and gone.figi is None
    assert openapi.calls == [("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", None, {})] or len(openapi.calls) == 1
    assert www.calls == [] and src.requests_made == 1
    assert [(e.mic, e.name, e.country.code) for e in src.exchanges()] == [("XTAI", "Taiwan Stock Exchange", "TW")]
    with pytest.raises(NotImplementedError):
        src.listings("XNAS")
    assert src.covers("2330.TW") and src.covers("2330") and not src.covers("BRK.B")


def test_the_app_loads_it_from_this_package_with_its_own_version():
    registry.reload()
    p = provider("twse")
    assert p is not None, dict(registry.errors())
    assert p.origin in {"package: plugin-integrator-twse (plugin_integrator_twse)", "plugins/plugin-integrator-twse (plugin_integrator_twse)"}
    assert p.version == version("plugin-integrator-twse") and twse.PLUGIN.version == "" and p.api == "2.0"
    assert registry.api_refusal(p.api) is None
    assert not [why for where, why in registry.errors() if "twse" in where or "twse" in why]
    row = {r["name"]: r for r in registry.menu()}["twse"]
    assert (row["version"], row["api"]) == (version("plugin-integrator-twse"), "2.0")


def test_it_carries_the_taiwan_stock_exchange_alone_on_its_own_days_and_limits():
    registry.reload()
    s = load_settings(env={}, env_file=None)
    view = s.for_source("twse")
    assert (view.tier, view.max_requests_per_run, view.max_requests_per_day) == (TIER, PER_RUN, PER_DAY)
    assert rate_window("twse", s) == (10, 60.0) and not is_archive("twse") and markets("twse", s) == {"stock": "twse"}
    assert supports("twse", resolve("2330.TW")) and supports("twse", resolve("TWSE:2330")) and supports("twse", resolve("2330::XTAI"))
    assert not supports("twse", resolve("AAPL")) and not supports("twse", resolve("7203.T")) and not supports("twse", resolve("EURUSD"))
    assert provider("twse").exchanges == {"XTAI"} and composite.feed_kind("twse", "stock") == "exchange"
    assert freshness.plan_delay(TIER, "stock").kind == "eod"  # its own rule (TwsePlugin.delays; the library's too): each day once it is over
    assert history_floor(TIER, date(2026, 11, 2)) == date(2010, 1, 4)
    src = twse.PLUGIN.build(s, 5)
    assert src.name == "twse" and src.client.base_url != src.openapi.base_url and src.requests_made == 0
    assert src.final_through() <= datetime.now(timezone.utc).astimezone(TAIPEI).date()


def test_it_is_a_class_on_the_contract_and_the_app_loads_it_as_one():
    assert isinstance(twse.PLUGIN, twse.TwsePlugin) and twse.PLUGIN.api == "2.0" and not twse.PLUGIN.is_record
    assert twse.PLUGIN.gives("build") and twse.PLUGIN.gives("markets") and twse.PLUGIN.gives("rate")
    assert not twse.PLUGIN.has_scan and not twse.PLUGIN.has_settings and not twse.PLUGIN.gives("view")
    assert twse.PLUGIN.delays == {"twse": {"stock": Delay("eod")}} and twse.PLUGIN.hours == {}
    p = registry.reload()["twse"]
    assert type(p) is twse.TwsePlugin and (p.version, p.api) == (version("plugin-integrator-twse"), "2.0")
    assert not [why for where, why in registry.errors() if "twse" in where or "twse" in why]
    moved = twse.PLUGIN.with_(order=1)  # a changed copy (the registry's version and origin come this way)
    assert type(moved) is twse.TwsePlugin and moved.order == 1 and twse.PLUGIN.order == 110
    assert moved.markets(None) == {"stock": "twse"} and moved.rate(None) == (10, 60.0)
