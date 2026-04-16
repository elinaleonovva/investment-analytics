import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError

from fixings.models import Currency, Index, Fixing, CurrencyUSDFixing, Metal, MetalUSDFixing

METAL_TICKERS = {
    "XAU": "GC=F",
    "XAG": "SI=F",
    "XPT": "PL=F",
    "XPD": "PA=F",
}


def chunk_list(lst, chunk_size):
    """Разбивает список на куски заданного размера"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


class Command(BaseCommand):
    help = "Загружает фиксинги валют, акций и металлов с 2026-01-01 до вчера."

    def extract_close_series(self, data, expected_tickers):
        """
        Безопасно извлекает pd.Series для каждого тикера,
        справляясь с любой структурой (MultiIndex / SingleIndex) yfinance.
        """
        results = {}
        if data is None or data.empty:
            return results

        try:
            if isinstance(data.columns, pd.MultiIndex):
                if 'Close' not in data.columns.levels[0]:
                    return results

                close_data = data['Close']
                if isinstance(close_data, pd.DataFrame):
                    for ticker in expected_tickers:
                        if ticker in close_data.columns:
                            results[ticker] = close_data[ticker].dropna()
                elif isinstance(close_data, pd.Series):
                    ticker = close_data.name if close_data.name in expected_tickers else expected_tickers[0]
                    results[ticker] = close_data.dropna()

            else:
                if 'Close' in data.columns:
                    close_data = data['Close']
                    if isinstance(close_data, pd.DataFrame):
                        for ticker in expected_tickers:
                            if ticker in close_data.columns:
                                results[ticker] = close_data[ticker].dropna()
                    elif isinstance(close_data, pd.Series):
                        ticker = expected_tickers[0] if len(expected_tickers) == 1 else close_data.name
                        results[ticker] = close_data.dropna()

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Ошибка при парсинге DataFrame: {e}"))

        return results

    def download_single_ticker(self, ticker, start_date, end_date):
        """Резервная загрузка одиночного тикера, строго возвращающая pd.Series"""
        try:
            data = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
            extracted = self.extract_close_series(data, [ticker])
            return extracted.get(ticker)
        except Exception:
            return None

    def handle(self, *args, **kwargs):
        try:
            processed_tickers = 0
            failed_tickers = 0
            failed_downloads = []

            start_date = datetime(2026, 1, 1).strftime("%Y-%m-%d")
            yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

            # 1. Кешируем объекты БД (избавляемся от N+1 проблемы)
            currency_map = {c.ticker: c for c in Currency.objects.exclude(ticker__isnull=True).exclude(ticker='')}
            index_map = {i.indexISIN: i for i in Index.objects.exclude(indexISIN__isnull=True).exclude(indexISIN='')}
            metal_map = {m.code: m for m in Metal.objects.filter(code__in=METAL_TICKERS.keys())}

            # Обратный маппинг для металлов (Yahoo Ticker -> Metal Code)
            reverse_metal_map = {v: k for k, v in METAL_TICKERS.items() if k in metal_map}

            currency_tickers = list(currency_map.keys())
            index_tickers = list(index_map.keys())
            metal_tickers = list(reverse_metal_map.keys())

            tickers = currency_tickers + index_tickers + metal_tickers
            self.stdout.write(f"Начинаем загрузку данных для {len(tickers)} тикеров...")

            closing_prices = {}
            chunk_size = 10

            # 2. Загружаем данные
            for chunk in chunk_list(tickers, chunk_size):
                try:
                    data = yf.download(
                        tickers=chunk,
                        start=start_date,
                        end=yesterday,
                        interval="1d",
                        progress=False
                    )
                    extracted = self.extract_close_series(data, chunk)

                    for ticker in chunk:
                        series = extracted.get(ticker)
                        if series is not None and not series.empty:
                            closing_prices[ticker] = series
                            processed_tickers += 1
                        else:
                            # Fallback на одиночную загрузку, если тикер выпал из батча
                            single_series = self.download_single_ticker(ticker, start_date, yesterday)
                            if single_series is not None and not single_series.empty:
                                closing_prices[ticker] = single_series
                                processed_tickers += 1
                            else:
                                failed_downloads.append(ticker)
                                failed_tickers += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Ошибка при загрузке пакета: {e}. Переключаемся на поштучную загрузку."))
                    for ticker in chunk:
                        single_series = self.download_single_ticker(ticker, start_date, yesterday)
                        if single_series is not None and not single_series.empty:
                            closing_prices[ticker] = single_series
                            processed_tickers += 1
                        else:
                            failed_downloads.append(ticker)
                            failed_tickers += 1

            if not closing_prices:
                self.stderr.write(self.style.ERROR("Не удалось получить данные ни для одного тикера."))
                return

            # 3. Подготавливаем объекты для БД
            fixings = []
            currency_fixings = []
            metal_prices = []

            for ticker, series in closing_prices.items():
                # ЖЕСТКАЯ ПРОВЕРКА ТИПА - предостерегаемся от повторения бага
                if not isinstance(series, pd.Series):
                    self.stdout.write(self.style.WARNING(
                        f"Пропуск {ticker}: ожидался pd.Series, получен {type(series)}. Данные сломаны."))
                    continue

                for date_obj, close_val in series.items():
                    # Безопасное извлечение даты в строку
                    if isinstance(date_obj, pd.Timestamp):
                        date_str = date_obj.strftime("%Y-%m-%d")
                    else:
                        date_str = str(date_obj)[:10]

                    try:
                        val = float(close_val)
                    except (ValueError, TypeError):
                        continue  # Игнорируем NaN и кривые значения

                    if ticker in index_map:
                        index_obj = index_map[ticker]
                        fixings.append(Fixing(
                            fixingDate=date_str,
                            indexId=index_obj,
                            currencyId=index_obj.ccyId,
                            value=val
                        ))

                    elif ticker in currency_map:
                        currency_fixings.append(CurrencyUSDFixing(
                            currencyFixingDate=date_str,
                            currencyId=currency_map[ticker],
                            rate_from_usd=1/val
                        ))

                    elif ticker in reverse_metal_map:
                        metal_code = reverse_metal_map[ticker]
                        metal_prices.append(MetalUSDFixing(
                            fixingDate=date_str,
                            metal=metal_map[metal_code],
                            rate_from_usd=val
                        ))

            # 4. Транзакционное сохранение
            if fixings or currency_fixings or metal_prices:
                try:
                    with transaction.atomic():
                        self.stdout.write("Очистка старых данных и сохранение новых...")
                        if currency_fixings:
                            CurrencyUSDFixing.objects.all().delete()
                            CurrencyUSDFixing.objects.bulk_create(currency_fixings, batch_size=1000)

                        if fixings:
                            Fixing.objects.all().delete()
                            Fixing.objects.bulk_create(fixings, batch_size=1000)

                        if metal_prices:
                            MetalUSDFixing.objects.all().delete()
                            MetalUSDFixing.objects.bulk_create(metal_prices, batch_size=1000)

                except IntegrityError as e:
                    self.stderr.write(self.style.ERROR(f"Ошибка целостности данных БД: {e}"))
                    return
            else:
                self.stderr.write(self.style.ERROR("Нет валидных фиксингов для сохранения."))
                return

            # Отчет
            self.stdout.write(self.style.SUCCESS(
                f"Загрузка завершена:\n"
                f"- Обработано тикеров: {processed_tickers} из {len(tickers)}\n"
                f"- Создано акций: {len(fixings)}\n"
                f"- Создано валют: {len(currency_fixings)}\n"
                f"- Создано металлов: {len(metal_prices)}\n"
            ))
            if failed_downloads:
                self.stdout.write(self.style.WARNING(f"Не скачались: {', '.join(failed_downloads)}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Критическая ошибка: {e}"))
