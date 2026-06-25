from django.contrib import admin

from .models import JournalOption, Trade


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("trade_date", "symbol", "direction", "result", "pnl", "r_multiple")
    list_filter = ("trade_date", "direction", "result", "planned_trade", "followed_plan")
    search_fields = ("symbol", "setup", "market", "account")


@admin.register(JournalOption)
class JournalOptionAdmin(admin.ModelAdmin):
    list_display = ("label", "kind")
    list_filter = ("kind",)
