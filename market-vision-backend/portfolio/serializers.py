from rest_framework import serializers

from fixings.models import Currency
from fixings.serializers import CurrencySerializer, StockSerializer
from .models import Portfolio, Trade


class PortfolioListSerializer(serializers.ModelSerializer):
    currentValue = serializers.SerializerMethodField()
    investedValue = serializers.SerializerMethodField()
    pnl = serializers.SerializerMethodField()
    pnlPercent = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ["id", "name", "currentValue", "investedValue", "pnl", "pnlPercent"]

    def get_currentValue(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_current_value(currency=currency)

    def get_investedValue(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_invested_value(currency=currency)

    def get_pnl(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_pnl(currency=currency)

    def get_pnlPercent(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_pnl_percent(currency=currency)


class TradeSerializer(serializers.ModelSerializer):
    stock = StockSerializer(source="stockId", read_only=True)
    price_per_share = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = [
            "id",
            "stockId",
            "stock",
            "side",
            "quantity",
            "price_per_share",
            "tradeDate",
            "created_at",
        ]
        read_only_fields = ["id", "stock", "price_per_share", "created_at"]

    def get_price_per_share(self, obj):
        request_currency = self.context.get("currency")
        if not request_currency or not obj.stockId or not obj.stockId.ccyId:
            return obj.price_per_share

        stock_currency = obj.stockId.ccyId.currency
        if request_currency == stock_currency:
            return obj.price_per_share

        fx = obj.stockId.ccyId.get_rate_to(
            request_currency=request_currency,
            date=obj.tradeDate,
        )
        return obj.price_per_share * fx


class PortfolioDetailSerializer(serializers.ModelSerializer):
    currentValue = serializers.SerializerMethodField()
    investedValue = serializers.SerializerMethodField()
    pnl = serializers.SerializerMethodField()
    pnlPercent = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "name",
            "created_at",
            "currentValue",
            "investedValue",
            "pnl",
            "pnlPercent",
            "currency",
        ]

    def get_currentValue(self, obj):
        return obj.get_current_value(currency=self.context.get("currency", "USD"))

    def get_investedValue(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_invested_value(currency=currency)

    def get_pnl(self, obj):
        return obj.get_pnl(currency=self.context.get("currency", "USD"))

    def get_pnlPercent(self, obj):
        return obj.get_pnl_percent(currency=self.context.get("currency", "USD"))

    def get_currency(self, _obj):
        code = self.context.get("currency", "USD")
        currency = Currency.objects.filter(currency=code).first()
        if not currency:
            return None
        return CurrencySerializer(currency).data


class BenchmarkSerializer(serializers.Serializer):
    name = serializers.CharField()
    period = serializers.CharField()
    note = serializers.CharField()


class PortfolioPositionAnalyticsSerializer(serializers.Serializer):
    stock = StockSerializer()
    quantity = serializers.DecimalField(max_digits=20, decimal_places=6)
    invested = serializers.DecimalField(max_digits=20, decimal_places=2)
    current_value = serializers.DecimalField(max_digits=20, decimal_places=2)
    pnl = serializers.DecimalField(max_digits=20, decimal_places=2)
    pnl_percent = serializers.DecimalField(max_digits=10, decimal_places=2)


class PortfolioAnalyticsSerializer(serializers.Serializer):
    totalCurrentValue = serializers.DecimalField(max_digits=20, decimal_places=2)
    totalInvestedValue = serializers.DecimalField(max_digits=20, decimal_places=2)
    totalPnL = serializers.DecimalField(max_digits=20, decimal_places=2)
    totalPnLPercent = serializers.DecimalField(max_digits=10, decimal_places=2)

    positions = PortfolioPositionAnalyticsSerializer(many=True)
    topGainers = PortfolioPositionAnalyticsSerializer(many=True)
    topLosers = PortfolioPositionAnalyticsSerializer(many=True)

    benchmark = BenchmarkSerializer()
