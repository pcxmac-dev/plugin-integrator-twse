"""What the plugin attaches to (plugin API 2.2): its two APIs as TWSE's pages describe them, the calls it says it makes
being the ones its source really sends, what its clients learned said without a request, and (LIMINAL_VENDOR_PAGES=1
only) every page it names still answering. Nothing else is sent; no ledger or key is touched."""
from __future__ import annotations

import gc
import os
from datetime import date, datetime

import pytest

from liminal_libs.config import load_settings
from liminal_libs.sources.apis import dead_links, problems, urls
from liminal_libs.sources.http import PublicClient

import plugin_integrator_twse as twse
from plugin_integrator_twse.apis import OPENAPI, OPENAPI_NAME, SITE, SITE_NAME
from plugin_integrator_twse.client import OPENAPI as OPENAPI_HOST, TAIPEI, WWW, TwseSource
from plugin_integrator_twse.facts import NOTES

from .conftest import FakeResponse, FakeSession
from .test_twse import MARKET, NOVEMBER


@pytest.fixture(autouse=True)
def fresh_notes():
    NOTES.clear()
    yield
    NOTES.clear()


def _source(www: list, openapi: list) -> tuple[TwseSource, FakeSession, FakeSession]:
    s1, s2 = FakeSession(www), FakeSession(openapi)
    src = TwseSource(PublicClient(WWW, session=s1, sleep=lambda s: None),
                     PublicClient(OPENAPI_HOST, session=s2, sleep=lambda s: None),
                     now=lambda: datetime(2026, 11, 3, 16, tzinfo=TAIPEI))
    return src, s1, s2


def test_it_declares_both_apis_soundly_with_every_part_and_what_it_does_with_each():
    apis = twse.PLUGIN.apis
    assert apis == (OPENAPI, SITE) and problems(apis) == [] and [a.name for a in apis] == [OPENAPI_NAME, SITE_NAME]
    assert OPENAPI.docs == "https://openapi.twse.com.tw/" and OPENAPI.link("spec").endswith("/v1/swagger.json")
    assert len(OPENAPI.areas) == 7 and [a.name for a in OPENAPI.covered] == ["Securities trading (證券交易)"]
    assert SITE.docs.endswith("/trading/historical/stock-day.html") and len(SITE.areas) == 10
    assert [a.name for a in SITE.covered] == ["Historical trading"]
    for api in apis:  # each call in one of its API's parts; it only reads, and nothing of it costs
        assert {c.area for c in api.calls} <= {a.name for a in api.areas}
        assert not any(c.writes or c.costs for c in api.calls) and api.costs == "" and api.verified == "2026-11-11"
    assert "section 6" in SITE.limits and "Open Government Data License" in OPENAPI.limits
    assert all(u.startswith("https://") for u in urls(apis)) and twse.PLUGIN.interface()["apis"] == [OPENAPI_NAME, SITE_NAME]


def test_the_calls_it_says_it_makes_are_the_ones_its_source_sends():
    src, www, openapi = _source([FakeResponse(200, NOVEMBER)], [FakeResponse(200, MARKET)])
    list(src.bar_pages("2330.TW", date(2026, 11, 1), date(2026, 11, 30), "day"))
    src.listings("XTAI")
    assert {"GET " + url.removeprefix(SITE.base) for url, _, _ in www.calls} == {c.name for c in SITE.used}
    assert {"GET " + url.removeprefix(OPENAPI.base) for url, _, _ in openapi.calls} == {c.name for c in OPENAPI.used}
    assert [c.name for c in SITE.used] == ["GET /exchangeReport/STOCK_DAY"]
    assert [c.name for c in OPENAPI.used] == ["GET /v1/exchangeReport/STOCK_DAY_ALL"]
    assert (SITE.base, OPENAPI.base) == (WWW, OPENAPI_HOST)  # the card's addresses are the client's


def test_api_facts_say_what_its_clients_learned_and_ask_nothing():
    assert twse.PLUGIN.api_facts() == {}  # nothing built here yet: nothing known, nothing asked
    built = twse.PLUGIN.build(load_settings(env={}, env_file=None), 5)  # its build notes both clients (no request)
    live = twse.PLUGIN.api_facts()
    assert set(live) == {OPENAPI_NAME, SITE_NAME} and live[SITE_NAME]["Requests"] == "0 so far (of 5 allowed)"
    assert live[OPENAPI_NAME]["Run began"].endswith("(under way)") and built.requests_made == 0
    del built
    gc.collect()  # the run over: its clients go, their last words stay
    assert twse.PLUGIN.api_facts()[SITE_NAME]["Run began"].endswith("(ended)")
    # a run's clients as TWSE answers them (fakes, no ledger): the requests, the server's clock, the table's day
    src, _, _ = _source([], [FakeResponse(200, MARKET, {"Date": "Tue, 03 Nov 2026 08:00:00 GMT"})])
    NOTES.note(SITE_NAME, src.client)
    NOTES.note(OPENAPI_NAME, src.openapi)
    src.listings("XTAI")
    said = twse.PLUGIN.api_facts()[OPENAPI_NAME]
    assert said["Requests"] == "1 so far" and said["Last answer (server's clock)"] == "Tue, 03 Nov 2026 08:00:00 GMT"
    assert said["STOCK_DAY_ALL's day"] == "2026-11-02 (3 listings)"
    del src
    gc.collect()
    after = twse.PLUGIN.api_facts()
    assert after[OPENAPI_NAME]["Requests"] == "1" and after[OPENAPI_NAME]["STOCK_DAY_ALL's day"].startswith("2026-11-02")
    assert after[SITE_NAME]["Requests"] == "0"


@pytest.mark.skipif(os.environ.get("LIMINAL_VENDOR_PAGES") != "1", reason="asks TWSE's pages: set LIMINAL_VENDOR_PAGES=1")
def test_every_page_it_names_answers():
    assert dead_links(twse.PLUGIN.apis) == []
