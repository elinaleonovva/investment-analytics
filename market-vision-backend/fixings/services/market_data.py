import datetime
import json
import os
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

import certifi
import requests
from django.db import transaction

from fixings.models import Currency, CurrencyUSDFixing, Fixing, Index, Metal, MetalUSDFixing


def _prepare_ascii_ca_bundle():
    """
    Prepare ASCII-only CA bundle path before importing yfinance/curl_cffi.
    Needed on Windows when project path contains non-ascii symbols.
    """
    src = certifi.where()
    dst = os.path.join(tempfile.gettempdir(), "yfinance-cacert.pem")
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)

    os.environ["CURL_CA_BUNDLE"] = dst
    os.environ["SSL_CERT_FILE"] = dst
    os.environ["REQUESTS_CA_BUNDLE"] = dst
    os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = dst

    # Force libraries that call certifi.where() to use ascii path.
    certifi.where = lambda: dst


try:
    _prepare_ascii_ca_bundle()
except Exception:
    # Fallback: do not break module import if CA workaround fails.
    pass

import yfinance as yf


# region agent log
DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / "debug-0b13f5.log"


def _debug_log(run_id, hypothesis_id, location, message, data):
    payload = {
        "sessionId": "0b13f5",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
    }
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
# endregion


class MarketUpdaterService:
    METAL_TICKERS = {
        "XAU": "GC=F",  # Gold futures (USD per ounce)
        "XAG": "SI=F",  # Silver futures
        "XPT": "PL=F",  # Platinum futures
        "XPD": "PA=F",  # Palladium futures
    }

    STOCK_TICKER_OVERRIDES = {
        "BRK.B": "BRK-B",
        "005930.KQ": "005930.KS",
    }
    YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def __init__(self):
        pass

    def _download_close_series_http(self, ticker, start_date, end_date):
        period1 = int(datetime.datetime.combine(start_date, datetime.time.min).timestamp())
        period2 = int(
            datetime.datetime.combine(end_date + datetime.timedelta(days=1), datetime.time.min).timestamp()
        )
        params = {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "events": "history",
        }

        def _parse(payload):
            chart = payload.get("chart", {})
            result = chart.get("result")
            if not result:
                if ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                    # region agent log
                    _debug_log(
                        "market-debug-1",
                        "H1",
                        "fixings/services/market_data.py:_download_close_series_http",
                        "Yahoo chart returned empty result",
                        {"ticker": ticker, "chart_error": chart.get("error")},
                    )
                    # endregion
                return []
            result = result[0]
            timestamps = result.get("timestamp") or []
            quote = (result.get("indicators", {}).get("quote") or [{}])[0]
            closes = quote.get("close") or []

            parsed = []
            for ts, close in zip(timestamps, closes):
                if close is None:
                    continue
                dt = datetime.datetime.utcfromtimestamp(int(ts)).date()
                parsed.append((dt, Decimal(str(close))))
            return parsed

        url = self.YAHOO_CHART_URL.format(symbol=ticker)
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            parsed = _parse(response.json())
            if ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                # region agent log
                _debug_log(
                    "market-debug-1",
                    "H1",
                    "fixings/services/market_data.py:_download_close_series_http",
                    "Yahoo HTTP parsed series",
                    {"ticker": ticker, "rows": len(parsed), "verify": True},
                )
                # endregion
            return parsed
        except Exception as exc:
            if ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                # region agent log
                _debug_log(
                    "market-debug-2",
                    "NH1",
                    "fixings/services/market_data.py:_download_close_series_http",
                    "Yahoo HTTP verify_true exception",
                    {"ticker": ticker, "error_type": type(exc).__name__, "error": str(exc)},
                )
                # endregion
            try:
                # Fallback for SSL path issues in local Windows environments.
                response = requests.get(url, params=params, timeout=20, verify=False)
                response.raise_for_status()
                parsed = _parse(response.json())
                if ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                    # region agent log
                    _debug_log(
                        "market-debug-1",
                        "H1",
                        "fixings/services/market_data.py:_download_close_series_http",
                        "Yahoo HTTP parsed series via verify_false",
                        {"ticker": ticker, "rows": len(parsed), "verify": False},
                    )
                    # endregion
                return parsed
            except Exception as exc2:
                if ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                    # region agent log
                    _debug_log(
                        "market-debug-2",
                        "NH1",
                        "fixings/services/market_data.py:_download_close_series_http",
                        "Yahoo HTTP verify_false exception",
                        {"ticker": ticker, "error_type": type(exc2).__name__, "error": str(exc2)},
                    )
                    # endregion
                if ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                    # region agent log
                    _debug_log(
                        "market-debug-1",
                        "H1",
                        "fixings/services/market_data.py:_download_close_series_http",
                        "Yahoo HTTP failed completely",
                        {"ticker": ticker},
                    )
                    # endregion
                return []

    def _download_close_series(self, ticker, start_date, end_date):
        def _to_date(value):
            if isinstance(value, datetime.datetime):
                return value.date()
            if isinstance(value, datetime.date):
                return value
            # yfinance can return string index for some tickers/providers
            try:
                parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                return parsed.date()
            except Exception:
                pass
            # Last fallback: YYYY-MM-DD
            return datetime.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()

        # 1) Primary simple source: direct Yahoo HTTP API.
        http_series = self._download_close_series_http(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )
        if http_series:
            return http_series

        # 2) Fallback source: yfinance wrapper.
        history = yf.download(
            tickers=ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=(end_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if not history.empty and "Close" in history.columns:
            closes = history["Close"].dropna()
            if not closes.empty:
                result = []
                for dt, close in closes.items():
                    try:
                        result.append((_to_date(dt), Decimal(str(close))))
                    except Exception:
                        continue
                return result
        elif ticker in {"AAPL", "EURUSD=X", "GC=F"}:
            # region agent log
            _debug_log(
                "market-debug-2",
                "NH2",
                "fixings/services/market_data.py:_download_close_series",
                "yfinance download empty result",
                {"ticker": ticker, "empty": bool(history.empty), "columns": list(history.columns)},
            )
            # endregion

        # Fallback path for some tickers when download() fails.
        try:
            fallback = yf.Ticker(ticker).history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                auto_adjust=True,
            )
            if not fallback.empty and "Close" in fallback.columns:
                closes = fallback["Close"].dropna()
                if not closes.empty:
                    result = []
                    for dt, close in closes.items():
                        try:
                            result.append((_to_date(dt), Decimal(str(close))))
                        except Exception:
                            continue
                    return result
            elif ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                # region agent log
                _debug_log(
                    "market-debug-2",
                    "NH2",
                    "fixings/services/market_data.py:_download_close_series",
                    "yfinance ticker.history empty result",
                    {"ticker": ticker, "empty": bool(fallback.empty), "columns": list(fallback.columns)},
                )
                # endregion
        except Exception as exc:
            if ticker in {"AAPL", "EURUSD=X", "GC=F"}:
                # region agent log
                _debug_log(
                    "market-debug-2",
                    "NH2",
                    "fixings/services/market_data.py:_download_close_series",
                    "yfinance ticker.history exception",
                    {"ticker": ticker, "error_type": type(exc).__name__, "error": str(exc)},
                )
                # endregion
            return []
        return []

    def _download_latest_close(self, ticker, start_date, end_date):
        series = self._download_close_series(ticker=ticker, start_date=start_date, end_date=end_date)
        if not series:
            return None
        return series[-1][1]

    def _resolve_currency_ticker(self, currency):
        if currency.currency == "USD":
            return None
        if currency.ticker:
            return currency.ticker
        return f"{currency.currency}USD=X"

    def _normalize_rate_from_usd(self, ticker, close):
        ticker = ticker.upper()

        # USDXXX=X → already USD base
        if ticker.startswith("USD"):
            return close

        # XXXUSD=X → invert
        if ticker.endswith("USD=X"):
            if close == 0:
                return Decimal("0")
            return Decimal("1") / close

        # fallback — считаем что котировка к USD и инвертируем
        return Decimal("1") / close

    def _upsert_currency_quotes(self, quote_date, start_date, end_date):
        currencies = list(Currency.objects.all())
        written_rows = 0
        for offset in range((end_date - start_date).days + 1):
            dt = start_date + datetime.timedelta(days=offset)
            usd_currency = next((c for c in currencies if c.currency == "USD"), None)
            if usd_currency:
                CurrencyUSDFixing.objects.update_or_create(
                    currencyId=usd_currency,
                    currencyFixingDate=dt,
                    defaults={"rate_from_usd": Decimal("1")},
                )
                written_rows += 1

        for currency in currencies:
            if currency.currency == "USD":
                continue

            ticker = self._resolve_currency_ticker(currency)
            series = self._download_close_series(ticker=ticker, start_date=start_date, end_date=end_date)
            if not series:
                continue
            for fixing_date, close_value in series:
                rate_from_usd = self._normalize_rate_from_usd(
                    currency_code=currency.currency,
                    ticker=ticker,
                    close_value=close_value,
                )
                CurrencyUSDFixing.objects.update_or_create(
                    currencyId=currency,
                    currencyFixingDate=fixing_date,
                    defaults={"rate_from_usd": rate_from_usd},
                )
                written_rows += 1
        # region agent log
        _debug_log(
            "market-debug-1",
            "H4",
            "fixings/services/market_data.py:_upsert_currency_quotes",
            "Currency quotes upsert summary",
            {"currencies": len(currencies), "written_rows": written_rows},
        )
        # endregion

    def _upsert_metal_quotes(self, quote_date, start_date, end_date):
        metals = list(Metal.objects.all())
        if not metals:
            return
        written_rows = 0
        non_empty = 0
        for metal in metals:
            ticker = self.METAL_TICKERS.get(metal.code)
            if not ticker:
                continue
            series = self._download_close_series(ticker=ticker, start_date=start_date, end_date=end_date)
            if not series:
                continue
            non_empty += 1
            for fixing_date, close_price in series:
                MetalUSDFixing.objects.update_or_create(
                    metal=metal,
                    fixingDate=fixing_date,
                    # We store USD price per 1 unit of metal.
                    defaults={"rate_from_usd": close_price},
                )
                written_rows += 1
        # region agent log
        _debug_log(
            "market-debug-1",
            "H2",
            "fixings/services/market_data.py:_upsert_metal_quotes",
            "Metal quotes upsert summary",
            {"metals": len(metals), "non_empty_series": non_empty, "written_rows": written_rows},
        )
        # endregion

    def _resolve_stock_ticker(self, raw_ticker):
        return self.STOCK_TICKER_OVERRIDES.get(raw_ticker, raw_ticker)

    def _upsert_stock_history(self, start_date, end_date):
        stocks = list(Index.objects.select_related("ccyId").all())
        non_empty = 0
        written_rows = 0
        sample_empty = None
        sample_non_empty = None
        for stock in stocks:
            if not stock.indexISIN or not stock.ccyId:
                continue
            ticker = self._resolve_stock_ticker(stock.indexISIN)
            series = self._download_close_series(ticker=ticker, start_date=start_date, end_date=end_date)
            if not series:
                if sample_empty is None:
                    sample_empty = ticker
                continue
            non_empty += 1
            if sample_non_empty is None:
                sample_non_empty = ticker
            for fixing_date, close_price in series:
                Fixing.objects.update_or_create(
                    indexId=stock,
                    fixingDate=fixing_date,
                    defaults={
                        "currencyId": stock.ccyId,
                        "value": Decimal(str(close_price)),
                    },
                )
                written_rows += 1
        # region agent log
        _debug_log(
            "market-debug-1",
            "H2",
            "fixings/services/market_data.py:_upsert_stock_history",
            "Stock history upsert summary",
            {
                "stocks": len(stocks),
                "non_empty_series": non_empty,
                "written_rows": written_rows,
                "sample_empty": sample_empty,
                "sample_non_empty": sample_non_empty,
            },
        )
        # endregion

    @transaction.atomic
    def update_market_data(self, days_back=30):
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days_back)
        # region agent log
        _debug_log(
            "market-debug-1",
            "H3",
            "fixings/services/market_data.py:update_market_data",
            "Update market data start",
            {"days_back": days_back, "start_date": str(start_date), "end_date": str(end_date)},
        )
        # endregion
        self._upsert_currency_quotes(quote_date=end_date, start_date=start_date, end_date=end_date)
        self._upsert_metal_quotes(quote_date=end_date, start_date=start_date, end_date=end_date)
        self._upsert_stock_history(start_date=start_date, end_date=end_date)
        # region agent log
        _debug_log(
            "market-debug-1",
            "H3",
            "fixings/services/market_data.py:update_market_data",
            "Update market data end counts",
            {
                "fixing_count": Fixing.objects.count(),
                "currency_fixing_count": CurrencyUSDFixing.objects.count(),
                "metal_fixing_count": MetalUSDFixing.objects.count(),
            },
        )
        # endregion
        print("Fixings:", Fixing.objects.count())
        print("FX:", CurrencyUSDFixing.objects.count())
        print("Metals:", MetalUSDFixing.objects.count())
