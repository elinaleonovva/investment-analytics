from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from .models import Currency, CurrencyUSDFixing, Fixing, Index, Metal, MetalUSDFixing


def round_decimal(value):
    if value is None:
        return Decimal("0")
    rounded = Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return rounded.normalize()


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "currency", "symbol"]


class StockSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer(source="ccyId", read_only=True)
    currentPrice = serializers.SerializerMethodField()
    currentConvertedPrice = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()

    class Meta:
        model = Index
        fields = [
            "id",
            "indexName",
            "indexISIN",
            "currency",
            "currentPrice",
            "currentConvertedPrice",
            "monthlyDynamic",
        ]

    def get_currentPrice(self, instance):
        return round_decimal(instance.get_price())

    def get_currentConvertedPrice(self, instance):
        request_currency = self.context.get("currency", "USD")
        return round_decimal(instance.get_price(request_currency=request_currency))

    def get_monthlyDynamic(self, instance):
        request_currency = self.context.get("currency", "USD")
        return round_decimal(instance.get_dynamic(request_currency=request_currency))


class MarketCurrencySerializer(serializers.ModelSerializer):
    rateToRequestedCurrency = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = ["id", "currency", "symbol", "rateToRequestedCurrency", "monthlyDynamic"]

    def get_rateToRequestedCurrency(self, instance):
        request_currency = self.context.get("currency", "USD")
        return round_decimal(instance.get_rate_to(request_currency=request_currency))

    def get_monthlyDynamic(self, instance):
        request_currency = self.context.get("currency", "USD")
        return round_decimal(instance.get_dynamic(request_currency=request_currency))


class MarketMetalSerializer(serializers.ModelSerializer):
    currentConvertedPrice = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()

    class Meta:
        model = Metal
        fields = ["id", "code", "name", "symbol", "currentConvertedPrice", "monthlyDynamic"]

    def _get_latest_fixing(self, instance, date):
        return MetalUSDFixing.objects.filter(
            metal=instance,
            fixingDate__lte=date,
        ).order_by("-fixingDate").first()

    def get_currentConvertedPrice(self, instance):
        date = self.context.get("date")
        request_currency = self.context.get("currency", "USD")
        current_fixing = self._get_latest_fixing(instance, date)
        if not current_fixing:
            return Decimal("0")
        if request_currency == "USD":
            return round_decimal(current_fixing.rate_from_usd)
        target_currency = Currency.objects.filter(currency=request_currency).first()
        if not target_currency:
            return Decimal("0")
        target_fixing = CurrencyUSDFixing.objects.filter(
            currencyId=target_currency,
            currencyFixingDate__lte=date,
        ).order_by("-currencyFixingDate").first()
        if not target_fixing or target_fixing.rate_from_usd == 0:
            return Decimal("0")
        return round_decimal(current_fixing.rate_from_usd * target_fixing.rate_from_usd)

    def get_monthlyDynamic(self, instance):
        date = self.context.get("date")
        month_ago = date - self.context.get("monthly_delta")
        latest = self._get_latest_fixing(instance, date)
        old = self._get_latest_fixing(instance, month_ago)
        if not latest or not old or old.rate_from_usd == 0:
            return Decimal("0")
        dynamic = ((latest.rate_from_usd - old.rate_from_usd) / old.rate_from_usd) * 100
        return round_decimal(dynamic)


class StockFixingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fixing
        fields = ["fixingDate", "value"]
