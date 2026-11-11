"""What the plugin attaches to (plugin API 2.2, liminal_libs.sources.apis): TWSE's OpenAPI, for the day's table of every
listed stock, and the JSON behind its website's report pages, for a stock's month of days. Every address below was read
on TWSE's own pages on 2026-11-11 (the OpenAPI's Swagger specification, its 143 calls in seven groups; the site's Market
Info menu and its report pages, each naming the address it asks in `data-api`); nothing is asked to show it."""
from __future__ import annotations

from liminal_libs.sources.apis import Api, Area, Call, Link

VERIFIED = "2026-11-11"
OPENAPI_NAME = "TWSE OpenAPI"
SITE_NAME = "TWSE website reports"
SWAGGER = "https://openapi.twse.com.tw/"
TERMS = "https://www.twse.com.tw/en/terms/use.html"
TERMS_ZH = "https://www.twse.com.tw/zh/terms/use.html"
LICENSE = "https://data.gov.tw/license"
EN = "https://www.twse.com.tw/en"  # the site's English pages (the Market Info menu)
STOCK_DAY_PAGE = f"{EN}/trading/historical/stock-day.html"

# the OpenAPI's seven groups (its Swagger tags), as the specification names them
TRADING = "Securities trading (證券交易)"
INDICES = "Indices (指數)"
GOVERNANCE = "Corporate governance (公司治理)"
STATEMENTS = "Financial statements (財務報表)"
WARRANTS = "Warrants (權證)"
BROKERS = "Brokers (券商資料)"
OTHERS = "Others (其他)"

OPENAPI = Api(
    name=OPENAPI_NAME,
    maker="Taiwan Stock Exchange (TWSE)",
    about=("TWSE's open data API: the exchange's daily and monthly reports as JSON, each one table of every listed "
           "security, company or broker for the latest day or month (trading, indices, warrants, companies' governance "
           "and financial statements). No key: its data is open government data, free to reuse with attribution."),
    kind="rest",
    base="https://openapi.twse.com.tw",
    version="1.0 (its Swagger 2.0 specification: 143 calls in seven groups, under /v1)",
    auth="none",
    limits=("none published; asked once a run here (STOCK_DAY_ALL), within the plugin's window of 10 requests a "
            "minute. Its data is under Taiwan's Open Government Data License 1.0 (attribution; compatible with CC BY "
            "4.0)"),
    costs="",
    links=(
        Link("OpenAPI reference (Swagger UI)", SWAGGER, "reference"),
        Link("Swagger specification (swagger.json)", "https://openapi.twse.com.tw/v1/swagger.json", "spec"),
        Link("Open Government Data License 1.0", LICENSE, "terms"),
        Link("TWSE terms of use", TERMS, "terms"),
    ),
    areas=(
        Area(TRADING, "the trading of every listed stock: the latest day's bars of all, the daily closing prices and "
                      "monthly averages, monthly and yearly trading, P/E and yields, the market's daily statistics, "
                      "margin, day trading, odd lots, block trades, trading halts, the holiday schedule (36 calls)",
             covered="STOCK_DAY_ALL: the latest day's table of every listed stock, read once a run for the directory "
                     "(the listings and their names) and a stock's record"),
        Area(INDICES, "TAIEX's history and its total return index, Taiwan 50, the Formosa index, the cross-market "
                      "daily trading (5 calls)"),
        Area(GOVERNANCE, "listed and public companies' basic data, material news, large shareholders, insiders' "
                         "holdings and transfers, dividends, shareholder meetings, ESG disclosures, new and delisted "
                         "listings (56 calls)"),
        Area(STATEMENTS, "listed and public companies' balance sheets and income statements by industry, monthly "
                         "revenue, EPS by industry (30 calls)"),
        Area(WARRANTS, "warrants' yearly issuance, their traders and their daily trading (3 calls)"),
        Area(BROKERS, "securities firms and their branches, staff, monthly accounts, regular-savings plans (9 calls)"),
        Area(OTHERS, "funds' basic data, TWSE's news and events, government bonds' interest (4 calls)"),
    ),
    calls=(
        Call("GET /v1/exchangeReport/STOCK_DAY_ALL", "the latest trading day's bars of every listed stock (Code, Name, "
             "TradeVolume, TradeValue, prices, Change, Transaction; ROC dates)", TRADING,
             used="the directory of listings and their names, a stock's record (once a run)"),
        Call("GET /v1/exchangeReport/STOCK_DAY_AVG_ALL", "every stock's closing price of the day and its monthly "
             "average", TRADING),
        Call("GET /v1/exchangeReport/FMSRFK_ALL", "every stock's monthly trading", TRADING),
        Call("GET /v1/exchangeReport/FMNPTK_ALL", "every stock's yearly trading", TRADING),
        Call("GET /v1/exchangeReport/BWIBBU_ALL", "every stock's P/E ratio, dividend yield and P/B ratio", TRADING),
        Call("GET /v1/exchangeReport/MI_INDEX", "the market's daily closing statistics", TRADING),
        Call("GET /v1/exchangeReport/TWT48U_ALL", "the coming ex-rights and ex-dividend dates", TRADING),
        Call("GET /v1/exchangeReport/TWTAWU", "securities whose trading is halted", TRADING),
        Call("GET /v1/holidaySchedule/holidaySchedule", "the market's open and closed days", TRADING),
        Call("GET /v1/indicesReport/MI_5MINS_HIST", "TAIEX's daily history", INDICES),
        Call("GET /v1/indicesReport/MFI94U", "TAIEX's total return index", INDICES),
        Call("GET /v1/opendata/t187ap03_L", "listed companies' basic data", GOVERNANCE),
        Call("GET /v1/opendata/t187ap04_L", "listed companies' material news of the day", GOVERNANCE),
        Call("GET /v1/opendata/t187ap45_L", "listed companies' dividend distributions", GOVERNANCE),
        Call("GET /v1/company/newlisting", "the latest listed companies", GOVERNANCE),
        Call("GET /v1/company/suspendListingCsvAndHtml", "companies whose listing ended", GOVERNANCE),
        Call("GET /v1/opendata/t187ap05_L", "listed companies' monthly revenue", STATEMENTS),
        Call("GET /v1/opendata/t187ap06_L_ci", "listed companies' income statements (general industry)", STATEMENTS),
        Call("GET /v1/opendata/t187ap07_L_ci", "listed companies' balance sheets (general industry)", STATEMENTS),
        Call("GET /v1/opendata/t187ap42_L", "listed warrants' daily trading", WARRANTS),
        Call("GET /v1/brokerService/brokerList", "securities firms' head offices", BROKERS),
        Call("GET /v1/news/newsList", "TWSE's news", OTHERS),
    ),
    verified=VERIFIED,
)

# the site's Market Info groups, as its menu names them
HISTORICAL = "Historical trading"
DELIVERY = "Price variation limit and full delivery"
DAY_TRADING = "Day trading"
MARGIN = "Margin trading and short sales"
FOREIGN = "Foreign and other investors"
BONDS = "Government bonds"
BLOCK = "Block trade"
STATISTICS = "Statistics"
HOLIDAYS = "Holiday schedule"
SITE_INDICES = "Indices"

SITE = Api(
    name=SITE_NAME,
    maker="Taiwan Stock Exchange (TWSE)",
    about=("The JSON behind the report pages of TWSE's website (Market Info: historical trading, margin, foreign "
           "investors, block trades, indices): each page asks it for a date, a month or a stock and draws the table "
           "it answers (a stat, its fields, its rows). TWSE documents the reports, not this address: its pages are "
           "the documentation."),
    kind="query",
    base="https://www.twse.com.tw",
    version="the reports as the site serves them in 2026 (its pages ask /rwd/{lang}/...; the older /exchangeReport/... "
            "this plugin asks still answers)",
    auth="none",
    limits=("none published; its data pages refuse bursts (kept at 10 requests a minute, 600 a run, 2,000 a day). "
            "TWSE's terms of use (section 6) forbid downloading the site's data with automated tools unless TWSE "
            "agreed to the method; its open data is the OpenAPI's"),
    costs="",
    links=(
        Link("Daily trading value and volume of a stock (the report)", STOCK_DAY_PAGE, "docs"),
        Link("個股日成交資訊 (the report in Chinese)", "https://www.twse.com.tw/zh/trading/historical/stock-day.html", "docs"),
        Link("TWSE terms of use", TERMS, "terms"),
        Link("使用條款 (the terms in Chinese, the binding text)", TERMS_ZH, "terms"),
        Link("Data E-Shop (TWSE's market data for sale)", "https://eshop.twse.com.tw/en/", "pricing"),
    ),
    areas=(
        Area(HISTORICAL, "the day's highlights and quotes, a stock's days of a month, its monthly and yearly trading, "
                         "P/E and yields, odd lots, after-hours trading, top 20, halts",
             f"{EN}/trading/historical/fmtqik.html",
             covered="STOCK_DAY: a stock's days of one month (from 2010-01-04), a request a stock-month: the history"),
        Area(DELIVERY, "price variation limits, new stocks' first five days, full-delivery securities",
             f"{EN}/trading/delivery/twt84u.html"),
        Area(DAY_TRADING, "the securities open to day trading, its monthly statistics, its suspensions",
             f"{EN}/trading/day-trading.html"),
        Area(MARGIN, "margin transactions, short sale balances and suspensions, securities lending",
             f"{EN}/trading/margin/mi-margn.html"),
        Area(FOREIGN, "foreign, dealer and investment trust trading by day, week and month; foreign shareholdings",
             f"{EN}/trading/foreign/t86.html"),
        Area(BONDS, "central government construction bonds' quotes and accrued interest",
             f"{EN}/trading/government/abp010.html"),
        Area(BLOCK, "block trades by stock, day, month and year", f"{EN}/trading/block/bfiauu.html"),
        Area(STATISTICS, "weekly market capitalization; monthly, quarterly and yearly statistics",
             f"{EN}/trading/statistics/index01.html"),
        Area(HOLIDAYS, "the market's open and closed days", f"{EN}/trading/holiday.html"),
        Area(SITE_INDICES, "TAIEX and its sub-indices, FTSE TWSE Taiwan indices, cross-market indices: histories",
             f"{EN}/indices/indices/series.html"),
    ),
    calls=(
        Call("GET /exchangeReport/STOCK_DAY", "a stock's days of one month (response=json, date=YYYYMMDD, stockNo; ROC "
             "dates, numbers with commas, \"--\" for a day without a trade)", HISTORICAL,
             used="a stock's daily bars, a stock-month a request (from 2010-01-04)", docs=STOCK_DAY_PAGE),
        Call("GET /rwd/{lang}/afterTrading/STOCK_DAY", "the same report at the address the site's page asks now",
             HISTORICAL, docs=STOCK_DAY_PAGE),
        Call("GET /rwd/{lang}/afterTrading/STOCK_DAY_AVG", "a stock's daily closing prices and the month's average",
             HISTORICAL, docs=f"{EN}/trading/historical/stock-day-avg.html"),
        Call("GET /rwd/{lang}/afterTrading/FMSRFK", "a stock's monthly trading of a year", HISTORICAL,
             docs=f"{EN}/trading/historical/fmsrfk.html"),
        Call("GET /rwd/{lang}/afterTrading/FMNPTK", "a stock's yearly trading", HISTORICAL,
             docs=f"{EN}/trading/historical/fmnptk.html"),
        Call("GET /rwd/{lang}/afterTrading/MI_INDEX", "the day's quotes of every security", HISTORICAL,
             docs=f"{EN}/trading/historical/mi-index.html"),
        Call("GET /rwd/{lang}/afterTrading/FMTQIK", "the highlights of each day's trading", HISTORICAL,
             docs=f"{EN}/trading/historical/fmtqik.html"),
        Call("GET /rwd/{lang}/afterTrading/BWIBBU", "a stock's P/E ratio, dividend yield and P/B ratio by day",
             HISTORICAL, docs=f"{EN}/trading/historical/bwibbu.html"),
        Call("GET /rwd/{lang}/afterTrading/TWTAWU", "trading halts", HISTORICAL,
             docs=f"{EN}/trading/historical/twtawu.html"),
        Call("GET /rwd/{lang}/marginTrading/MI_MARGN", "the day's margin transactions", MARGIN,
             docs=f"{EN}/trading/margin/mi-margn.html"),
        Call("GET /rwd/{lang}/fund/T86", "foreign and other investors' trading of the day", FOREIGN,
             docs=f"{EN}/trading/foreign/t86.html"),
        Call("GET /rwd/{lang}/block/BFIAUU", "the day's block trades", BLOCK, docs=f"{EN}/trading/block/bfiauu.html"),
        Call("GET /rwd/{lang}/holidaySchedule/holidaySchedule", "the market's open and closed days", HOLIDAYS,
             docs=f"{EN}/trading/holiday.html"),
        Call("GET /rwd/{lang}/TAIEX/MI_5MINS_HIST", "TAIEX's daily history", SITE_INDICES,
             docs=f"{EN}/indices/taiex/mi-5min-hist.html"),
    ),
    verified=VERIFIED,
)

APIS = (OPENAPI, SITE)
