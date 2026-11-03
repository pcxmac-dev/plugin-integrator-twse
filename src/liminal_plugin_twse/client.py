"""TWSE's two public endpoints as one source: a stock's month pages of days (www.twse.com.tw) and the
latest day's whole-market table (openapi.twse.com.tw), each on the library's keyless client of its
host (a client sends to its own host alone)."""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Callable, Iterator
from zoneinfo import ZoneInfo

from liminal_lib.errors import NotEntitled, SourceError
from liminal_lib.models import Exchange, Instrument, Stock, country, listing_ticker, suffix_mic
from liminal_lib.sources.archive import ET, Archive, bounds, ms
from liminal_lib.sources.http import PublicClient

WWW = "https://www.twse.com.tw"
OPENAPI = "https://openapi.twse.com.tw"
MIC = "XTAI"
TAIPEI = ZoneInfo("Asia/Taipei")
FINAL_AFTER = time(15, 0)  # a day's bars are final once TWSE has published its close (13:30 Taipei; by 15:00)
START = date(2010, 1, 4)  # STOCK_DAY's history begins in 2010
NO_DATA = "沒有符合條件的資料"  # TWSE's "no matching data": a month before a listing
COLUMNS = ("日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "成交筆數")  # date, shares, value, o, h, l, c, trades
XTAI = Exchange("twse", 1, "Taiwan Stock Exchange", country("TW"), mic=MIC, acronym="TWSE", type="exchange")


def twse_code(ticker: str) -> str:
    """TWSE's code of a stored listing (2330 for 2330.TW; a bare code as it is)."""
    t = ticker.strip().upper()
    base, dot, tail = t.rpartition(".")
    return base if base and dot and suffix_mic(tail) == MIC else t


def roc_date(text: str) -> date | None:
    """A date in the ROC calendar (1151102 or 115/11/02: year 115 is 2026) as a date, or None."""
    digits = re.sub(r"\D", "", str(text or ""))
    if len(digits) < 7:
        return None
    try:
        return date(int(digits[:-4]) + 1911, int(digits[-4:-2]), int(digits[-2:]))
    except ValueError:
        return None


def number(text) -> float | None:
    """A number TWSE writes with commas (41,165,068; 2,310.00); "--" (no trade) and nothing are None."""
    try:
        return float(str(text or "").replace(",", "").strip())
    except ValueError:
        return None


def listing_type(code: str) -> str:
    """CS for a four-digit code (a company's shares), ETF for the 00 series (ETNs among them), OTHER
    for the rest (warrants, depositary receipts, preferred shares)."""
    if code.startswith("00"):
        return "ETF"
    return "CS" if re.fullmatch(r"\d{4}", code) else "OTHER"


def day_bar(d: date, o, h, l, c, shares, value, trades) -> dict | None:
    """A day's bar stamped at midnight US/Eastern of its Taipei date (the library's rule for a
    listing abroad), its volume in shares, its vwap the day's value over its shares; a day without
    a trade (prices "--") is none."""
    if None in (o, h, l, c):
        return None
    v = shares or 0.0
    return {"t": ms(datetime(d.year, d.month, d.day, tzinfo=ET)), "o": o, "h": h, "l": l, "c": c, "v": v,
            "vw": value / v if value and v else None, "n": int(trades) if trades is not None else None}


def read_month(answer) -> list[dict]:
    """A STOCK_DAY answer's days as bars, oldest first; a month before the listing is none."""
    if not isinstance(answer, dict):
        raise SourceError(0, "unexpected TWSE answer for a month of days (not an object)")
    stat = str(answer.get("stat") or "")
    if stat != "OK":
        if NO_DATA in stat:
            return []
        raise SourceError(0, f"TWSE: {stat or 'an answer without a stat'}")
    fields = [str(f).strip() for f in answer.get("fields") or []]
    idx = {f: i for i, f in enumerate(fields)}
    if any(f not in idx for f in COLUMNS):
        raise SourceError(0, f"TWSE: the month page's columns changed ({', '.join(fields)})")
    width = max(idx[f] for f in COLUMNS)
    bars = []
    for row in answer.get("data") or []:
        if not isinstance(row, (list, tuple)) or len(row) <= width:
            continue
        d = roc_date(row[idx["日期"]])
        if d is None:
            continue
        cell = lambda name: number(row[idx[name]])  # noqa: E731
        bar = day_bar(d, cell("開盤價"), cell("最高價"), cell("最低價"), cell("收盤價"), cell("成交股數"), cell("成交金額"),
                      cell("成交筆數"))
        if bar:
            bars.append(bar)
    bars.sort(key=lambda b: b["t"])
    return bars


def _months(first: date, last: date) -> list[date]:
    out, m = [], first.replace(day=1)
    while m <= last:
        out.append(m)
        m = (m.replace(year=m.year + 1, month=1) if m.month == 12 else m.replace(month=m.month + 1))
    return out


class TwseSource(Archive):
    """Every listed stock's daily bars: a stock-month a request from the site's STOCK_DAY (kept for
    the run), the latest day's whole-market table from the OpenAPI (one request a run) for the
    listings, their names and a stock's record. Live: the day's bars come once TWSE has published
    its close (FINAL_AFTER, Taipei); a day under way is never served."""

    name = "twse"
    assets = ("stock",)
    archival = False

    def __init__(self, client: PublicClient, openapi: PublicClient, now: Callable[[], datetime] | None = None):
        super().__init__(client)
        self.openapi = openapi
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._months: dict[tuple[str, date], list[dict]] = {}
        self._market: list[dict] | None = None

    @property
    def requests_made(self) -> int:
        return self.client.requests_made + self.openapi.requests_made

    def resolutions(self, asset: str) -> tuple[str, ...]:
        return ("day",) if asset == "stock" else ()

    def native_frames(self, asset: str) -> tuple:
        return ()

    def covers(self, ticker: str) -> bool:
        t = ticker.strip().upper()
        return twse_code(t) != t or t.isalnum()

    def final_through(self) -> date:
        """The last Taipei date whose bars are final: today once its close is published, else the
        day before (a weekend's days have no bars either way)."""
        now = self.now().astimezone(TAIPEI)
        return now.date() if now.time() >= FINAL_AFTER else now.date() - timedelta(days=1)

    def _month(self, code: str, month: date) -> list[dict]:
        key = (code, month)
        if key not in self._months:
            answer = self.client.get("/exchangeReport/STOCK_DAY",
                                     {"response": "json", "date": month.strftime("%Y%m%d"), "stockNo": code})
            self._months[key] = read_month(answer)
        return self._months[key]

    def bar_pages(self, ticker, start, end, timespan, multiplier=1, descending=False, asset="stock",
                  limit: int | None = None) -> Iterator[list[dict]]:
        if timespan != "day":
            raise NotEntitled(0, "TWSE publishes daily bars here")
        code = twse_code(ticker)
        if not code.isalnum():
            raise NotEntitled(0, f"{ticker} is not a Taiwan Stock Exchange code")
        first = max(start.date() if isinstance(start, datetime) else start, START)
        last = min(end.date() if isinstance(end, datetime) else end, self.final_through())
        a, b = bounds(start, end, ET)
        b = min(b, ms(datetime.combine(last + timedelta(days=1), time(0), ET)))  # nothing of a day under way
        months = _months(first, last) if first <= last else []
        for month in (reversed(months) if descending else months):
            bars = [x for x in self._month(code, month) if a <= x["t"] < b]
            bars.sort(key=lambda x: -x["t"] if descending else x["t"])
            if limit:
                yield bars[:limit]
                return
            yield bars

    def _market_rows(self) -> list[dict]:
        """The latest trading day's table of every listed stock (STOCK_DAY_ALL), once a run."""
        if self._market is None:
            rows = self.openapi.get("/v1/exchangeReport/STOCK_DAY_ALL")
            if not isinstance(rows, list):
                raise SourceError(0, "unexpected TWSE answer for STOCK_DAY_ALL (not a list)")
            self._market = [r for r in rows if isinstance(r, dict) and r.get("Code")]
        return self._market

    def listings(self, exchange: str) -> list[dict]:
        if exchange.upper() != MIC:
            raise NotImplementedError("TWSE lists the Taiwan Stock Exchange alone")
        return [{"ticker": listing_ticker(str(r["Code"]), MIC), "name": r.get("Name"), "exchange": MIC,
                 "type": listing_type(str(r["Code"])), "figi": None, "kind": "stock"} for r in self._market_rows()]

    def exchanges(self) -> list[Exchange]:
        return [XTAI]

    def instrument(self, ticker: str, resolve_exchange: bool = True) -> Instrument:
        """A stock's record from the day's table: its name and exchange (no listing date: TWSE's
        open data has none; a code not in the table is inactive by the table alone, which the
        library does not read as a delisting)."""
        code = twse_code(ticker)
        row = next((r for r in self._market_rows() if str(r.get("Code")) == code), None)
        if row is None:
            return Stock(ticker=listing_ticker(code, MIC), primary_exchange=XTAI, currency="TWD", active=False,
                         details={"source": "TWSE STOCK_DAY_ALL", "listed": False})
        return Stock(ticker=listing_ticker(code, MIC), name=row.get("Name"), primary_exchange=XTAI, currency="TWD",
                     details={**row, "source": "TWSE STOCK_DAY_ALL"})
