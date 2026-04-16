from django.contrib import admin

from .models import Currency, Index, Fixing, CurrencyUSDFixing, Metal, MetalUSDFixing


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["currency", "symbol"]
    search_fields = ["currency",]


@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    list_display = ["indexName", "ccyId", "indexISIN"]
    search_fields = ["indexName", "indexISIN"]


@admin.register(Fixing)
class FixingAdmin(admin.ModelAdmin):
    list_display = ["indexId", "fixingDate", "value", "currencyId"]
    search_fields = ["indexId__indexName"]


@admin.register(CurrencyUSDFixing)
class CurrencyUSDFixingAdmin(admin.ModelAdmin):
    list_display = ["currencyId", "currencyFixingDate", "rate_from_usd"]
    search_fields = ["currencyId__currency"]


@admin.register(Metal)
class MetalAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "symbol"]
    search_fields = ["code", "name"]


@admin.register(MetalUSDFixing)
class MetalUSDFixingAdmin(admin.ModelAdmin):
    list_display = ["metal", "fixingDate", "rate_from_usd"]
    search_fields = ["metal__code", "metal__name"]
