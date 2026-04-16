from django.contrib import admin
from portfolio.models import Portfolio, Trade


class TradeInline(admin.TabularInline):
    model = Trade
    extra = 1
    fields = ("stockId", "side", "quantity", "price_per_share", "tradeDate")
    show_change_link = True


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["userId", "name", "created_at"]
    inlines = [TradeInline]


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ["portfolioId", "stockId", "side", "quantity", "price_per_share", "tradeDate"]
    search_fields = ["portfolioId__name", "stockId__indexName", "stockId__indexISIN"]
