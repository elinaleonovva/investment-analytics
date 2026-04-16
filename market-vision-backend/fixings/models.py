import datetime
from decimal import Decimal

from django.db import models


class Currency(models.Model):
    currency = models.CharField(verbose_name="ISO код валюты", max_length=50, default="RUB", unique=True)
    symbol = models.CharField(verbose_name="Символ валюты", max_length=10, default="RUB", blank=True)
    ticker = models.CharField(verbose_name="Служебный тикер", max_length=50, blank=True)

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"

    def __str__(self):
        return self.currency

    def get_rate_to(self, request_currency="USD", date=None):
        """
        Возвращает курс 1 единицы self.currency в request_currency.
        Хранение в CurrencyUSDFixing: сколько target_currency за 1 USD (USDEUR=0.92).
        """
        if date is None:
            date = datetime.date.today()

        if self.currency == request_currency:
            return Decimal("1")

        # 1. Получаем курс исходной валюты к доллару
        if self.currency == "USD":
            source_rate = Decimal("1")
        else:
            source_quote = CurrencyUSDFixing.objects.filter(
                currencyId=self,
                currencyFixingDate__lte=date,
            ).order_by("-currencyFixingDate").first()
            if not source_quote or not source_quote.rate_from_usd:
                return Decimal("0")
            source_rate = Decimal(str(source_quote.rate_from_usd))

        # 2. Получаем курс целевой валюты к доллару
        if request_currency == "USD":
            target_rate = Decimal("1")
        else:
            target_currency = Currency.objects.filter(currency=request_currency).first()
            if not target_currency:
                return Decimal("0")
            target_quote = CurrencyUSDFixing.objects.filter(
                currencyId=target_currency,
                currencyFixingDate__lte=date,
            ).order_by("-currencyFixingDate").first()
            if not target_quote or not target_quote.rate_from_usd:
                return Decimal("0")
            target_rate = Decimal(str(target_quote.rate_from_usd))

        if source_rate == 0:
            return Decimal("0")

        # Кросс-курс: (USD -> target) / (USD -> source)
        return target_rate / source_rate

    def get_dynamic(self, days=30, request_currency="USD"):
        today = datetime.date.today()
        past = today - datetime.timedelta(days=days)
        current = self.get_rate_to(request_currency=request_currency, date=today)
        previous = self.get_rate_to(request_currency=request_currency, date=past)
        if previous == 0:
            return Decimal("0")
        return ((current - previous) / previous) * 100


class CurrencyUSDFixing(models.Model):
    currencyId = models.ForeignKey(Currency, verbose_name="Валюта", on_delete=models.CASCADE, null=True, blank=True)
    currencyFixingDate = models.DateField(verbose_name="Дата валютного фиксинга", null=True, blank=True)
    rate_from_usd = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        verbose_name="Курс USD -> валюта",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Фиксинг валюты"
        verbose_name_plural = "Фиксинги валют"
        constraints = []

    def __str__(self):
        return f"{self.currencyId}_{self.currencyFixingDate}"


class Metal(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Код металла")
    name = models.CharField(max_length=100, verbose_name="Название")
    symbol = models.CharField(max_length=10, blank=True, verbose_name="Символ")

    class Meta:
        verbose_name = "Драгоценный металл"
        verbose_name_plural = "Драгоценные металлы"

    def __str__(self):
        return self.code


class MetalUSDFixing(models.Model):
    metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="fixings")
    fixingDate = models.DateField(verbose_name="Дата фиксинга")
    rate_from_usd = models.DecimalField(max_digits=30, decimal_places=12, verbose_name="Курс USD -> металл")

    class Meta:
        verbose_name = "Фиксинг металла"
        verbose_name_plural = "Фиксинги металлов"
        constraints = []

    def __str__(self):
        return f"{self.metal.code}_{self.fixingDate}"


class Index(models.Model):
    # Сохраняем имя модели для совместимости с текущим проектом и БД.
    indexName = models.CharField(max_length=200, unique=True, blank=True, verbose_name="Название акции")
    ccyId = models.ForeignKey(Currency, on_delete=models.SET_NULL, verbose_name="Валюта акции", null=True)
    indexISIN = models.CharField(max_length=200, blank=True, verbose_name="Тикер")

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return self.indexName

    def get_price(self, request_currency=None, date=None):
        if date is None:
            date = datetime.date.today()
        if not self.ccyId:
            return Decimal("0")
        if request_currency is None:
            request_currency = self.ccyId.currency

        fixing = Fixing.objects.filter(
            fixingDate__lte=date,
            indexId=self,
        ).order_by("-fixingDate").first()
        if not fixing:
            return Decimal("0")
        return fixing.get_value(currency=request_currency)

    def get_dynamic(self, days=30, request_currency=None):
        today = datetime.date.today()
        past = today - datetime.timedelta(days=days)
        current = self.get_price(request_currency=request_currency, date=today)
        previous = self.get_price(request_currency=request_currency, date=past)
        if previous == 0:
            return Decimal("0")
        return ((current - previous) / previous) * 100


class Fixing(models.Model):
    fixingDate = models.DateField(verbose_name="Дата фиксинга", null=True, blank=True)
    indexId = models.ForeignKey(
        Index,
        verbose_name="Акция",
        on_delete=models.PROTECT,
        related_name="fixings",
        null=True,
        blank=True,
    )
    currencyId = models.ForeignKey(
        Currency,
        verbose_name="Валюта",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    value = models.DecimalField(verbose_name="Цена закрытия", max_digits=30, decimal_places=12, null=True, blank=True)

    class Meta:
        verbose_name = "Фиксинг акции"
        verbose_name_plural = "Фиксинги акций"
        constraints = []

    def __str__(self):
        return f"{self.indexId}_{self.fixingDate}"

    def get_value(self, currency=None):
        if not self.value:
            return Decimal("0")

        # Если целевая валюта не указана, нет валюты у фиксинга или они совпадают
        if currency is None or not self.currencyId or self.currencyId.currency == currency:
            return self.value

        # Запрашиваем кросс-курс у объекта валюты
        fx = self.currencyId.get_rate_to(request_currency=currency, date=self.fixingDate)

        if fx == 0:
            return Decimal("0")

        return self.value * fx
