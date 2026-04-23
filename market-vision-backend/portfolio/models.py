from decimal import Decimal

from django.db import models

from authentication.models import User
from fixings.models import Index


class Portfolio(models.Model):
    userId = models.ForeignKey(User, verbose_name="Владелец портфеля", on_delete=models.PROTECT)
    name = models.CharField(max_length=255, verbose_name="Название портфеля")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Портфель акций"
        verbose_name_plural = "Портфели акций"

    def __str__(self):
        return f"{self.name} ({self.userId.username})"

    def get_positions_analytics(self, currency="USD"):
        """
        Считает позиции по методу средней стоимости (Average Cost).
        Это решает проблему отрицательных "вложенных" средств при продаже.
        """
        positions = {}
        trades = self.trades.select_related("stockId").order_by("tradeDate", "id")

        for trade in trades:
            stock_id = trade.stockId_id
            if stock_id not in positions:
                positions[stock_id] = {
                    "stock": trade.stockId,
                    "quantity": Decimal("0"),
                    "average_cost": Decimal("0"),
                    "realized_pnl": Decimal("0"),
                    "realized_cost": Decimal("0"),
                }

            pos = positions[stock_id]
            trade_qty = trade.quantity
            trade_price = trade.price_per_share
            if trade.stockId.ccyId and currency != trade.stockId.ccyId.currency:
                trade_price *= trade.stockId.ccyId.get_rate_to(
                    request_currency=currency,
                    date=trade.tradeDate,
                )

            if trade.side == Trade.Side.BUY:
                total_cost_before = pos["quantity"] * pos["average_cost"]
                new_cost = trade_qty * trade_price
                pos["quantity"] += trade_qty
                pos["average_cost"] = (total_cost_before + new_cost) / pos["quantity"]
            elif trade.side == Trade.Side.SELL:
                if trade_qty > pos["quantity"]:
                    continue
                realized_cost = trade_qty * pos["average_cost"]
                pos["quantity"] -= trade_qty
                realized = trade_qty * (trade_price - pos["average_cost"])
                pos["realized_cost"] += realized_cost
                pos["realized_pnl"] += realized

        active_positions = {}
        for stock_id, data in positions.items():
            if data["quantity"] > 0 or data["realized_pnl"] != 0:
                current_price = data["stock"].get_price(request_currency=currency)
                current_value = data["quantity"] * current_price
                invested = data["quantity"] * data["average_cost"]
                unrealized_pnl = current_value - invested

                active_positions[stock_id] = {
                    "stock": data["stock"],
                    "quantity": data["quantity"],
                    "invested": invested,
                    "current_value": current_value,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": data["realized_pnl"],
                    "realized_cost": data["realized_cost"],
                    "total_pnl": unrealized_pnl + data["realized_pnl"],
                }

        return active_positions

    def get_portfolio_summary(self, currency="USD"):
        positions = self.get_positions_analytics(currency)

        current_value = sum((p["current_value"] for p in positions.values()), Decimal("0"))
        invested_value = sum((p["invested"] for p in positions.values()), Decimal("0"))
        realized_cost = sum((p["realized_cost"] for p in positions.values()), Decimal("0"))
        realized_pnl = sum((p["realized_pnl"] for p in positions.values()), Decimal("0"))
        unrealized_pnl = sum((p["unrealized_pnl"] for p in positions.values()), Decimal("0"))

        total_pnl = unrealized_pnl + realized_pnl
        total_cost_basis = invested_value + realized_cost
        pnl_percent = (total_pnl / total_cost_basis * 100) if total_cost_basis > 0 else Decimal("0")

        return {
            "currentValue": current_value,
            "investedValue": invested_value,
            "pnl": total_pnl,
            "pnlPercent": pnl_percent,
        }

    def get_current_value(self, currency="USD"):
        return self.get_portfolio_summary(currency=currency)["currentValue"]

    def get_invested_value(self, currency="USD"):
        return self.get_portfolio_summary(currency=currency)["investedValue"]

    def get_pnl(self, currency="USD"):
        return self.get_portfolio_summary(currency=currency)["pnl"]

    def get_pnl_percent(self, currency="USD"):
        return self.get_portfolio_summary(currency=currency)["pnlPercent"]


class Trade(models.Model):
    class Side(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"

    portfolioId = models.ForeignKey(Portfolio, related_name="trades", on_delete=models.CASCADE)
    stockId = models.ForeignKey(Index, verbose_name="Акция", on_delete=models.PROTECT)
    side = models.CharField(max_length=4, choices=Side.choices, default=Side.BUY)
    quantity = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="Количество")
    price_per_share = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="Цена за акцию")
    tradeDate = models.DateField(verbose_name="Дата сделки")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сделка"
        verbose_name_plural = "Сделки"
        ordering = ["-tradeDate", "-id"]

    def __str__(self):
        return f"{self.side} {self.quantity} {self.stockId} @ {self.price_per_share}"
