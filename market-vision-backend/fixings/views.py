import datetime

from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Currency, Index, Metal
from .serializers import (
    CurrencySerializer,
    MarketCurrencySerializer,
    MarketMetalSerializer,
    StockSerializer,
)
from .services.market_data import MarketUpdaterService


class MarketPaginator(PageNumberPagination):
    page_size = 20

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data["pageSize"] = self.page_size
        return response


class StocksListView(generics.ListAPIView):
    serializer_class = StockSerializer
    queryset = Index.objects.select_related("ccyId").all().order_by("indexISIN")
    pagination_class = MarketPaginator

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["currency"] = self.request.query_params.get("currency", "USD")
        return context


class MarketCurrenciesListView(generics.ListAPIView):
    serializer_class = MarketCurrencySerializer
    queryset = Currency.objects.all().order_by("currency")
    pagination_class = MarketPaginator

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["currency"] = self.request.query_params.get("currency", "USD")
        return context


class MarketMetalsListView(generics.ListAPIView):
    serializer_class = MarketMetalSerializer
    queryset = Metal.objects.all().order_by("code")
    pagination_class = MarketPaginator

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["currency"] = self.request.query_params.get("currency", "USD")
        context["date"] = datetime.date.today()
        context["monthly_delta"] = datetime.timedelta(days=30)
        return context


class UpdateMarketDataView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        days_back = int(request.data.get("days_back", 30))
        updater = MarketUpdaterService()
        updater.update_market_data(days_back=days_back)
        return Response(
            {
                "success": True,
                "message": "Market data updated from external APIs (Yahoo Finance).",
                "days_back": days_back,
            }
        )


class CurrenciesReferenceView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        currencies = Currency.objects.all().order_by("currency")
        return Response(CurrencySerializer(currencies, many=True).data)


class StocksReferenceView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        stocks = Index.objects.select_related("ccyId").all().order_by("indexISIN")
        serializer = StockSerializer(stocks, many=True, context={"currency": request.query_params.get("currency", "USD")})
        return Response(serializer.data)
