from decimal import Decimal

from portfolio.models import Portfolio


def build_portfolio_analytics(portfolio: Portfolio, currency: str = "USD"):
    positions_payload = []
    total_current = Decimal("0")
    total_invested = Decimal("0")

    for position in portfolio.get_positions_analytics().values():
        stock = position["stock"]
        quantity = position["quantity"]
        invested = position["invested"]
        current_price = stock.get_price(request_currency=currency)
        current_value = quantity * current_price
        pnl = current_value - invested
        pnl_percent = Decimal("0") if invested == 0 else (pnl / invested) * 100

        total_current += current_value
        total_invested += invested

        positions_payload.append(
            {
                "stock": stock,
                "quantity": quantity,
                "invested": invested,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
            }
        )

    total_pnl = total_current - total_invested
    total_pnl_percent = Decimal("0") if total_invested == 0 else (total_pnl / total_invested) * 100

    top_gainers = sorted(positions_payload, key=lambda x: x["pnl_percent"], reverse=True)[:3]
    top_losers = sorted(positions_payload, key=lambda x: x["pnl_percent"])[:3]

    return {
        "totalCurrentValue": total_current,
        "totalInvestedValue": total_invested,
        "totalPnL": total_pnl,
        "totalPnLPercent": total_pnl_percent,
        "positions": positions_payload,
        "topGainers": top_gainers,
        "topLosers": top_losers,
        "benchmark": {
            "name": "S&P 500 (SPY)",
            "period": "30d",
            "note": "Базовое сравнение можно расширить отдельным endpoint для benchmark history.",
        },
    }
