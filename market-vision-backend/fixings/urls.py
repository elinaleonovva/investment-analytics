from django.urls import path

from .views import (
    CurrenciesReferenceView,
    MarketCurrenciesListView,
    MarketMetalsListView,
    StocksListView,
    StocksReferenceView,
    UpdateMarketDataView,
)

urlpatterns = [
    path("stocks/", StocksListView.as_view(), name="stocks-list"),
    path("market/currencies/", MarketCurrenciesListView.as_view(), name="market-currencies"),
    path("market/metals/", MarketMetalsListView.as_view(), name="market-metals"),
    path("market/update/", UpdateMarketDataView.as_view(), name="update-market"),
    path("reference/currencies/", CurrenciesReferenceView.as_view(), name="currencies-reference"),
    path("reference/stocks/", StocksReferenceView.as_view(), name="stocks-reference"),
]
