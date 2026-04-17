from decimal import Decimal

from portfolio.models import Portfolio


def build_portfolio_analytics(portfolio: Portfolio, currency: str = "USD"):
    positions_payload = []
    summary = portfolio.get_portfolio_summary(currency=currency)

    for position in portfolio.get_positions_analytics(currency=currency).values():
        stock = position["stock"]
        quantity = position["quantity"]
        invested = position["invested"]
        realized_cost = position["realized_cost"]
        current_value = position["current_value"]
        pnl = position["total_pnl"]
        total_cost_basis = invested + realized_cost
        pnl_percent = Decimal("0") if total_cost_basis == 0 else (pnl / total_cost_basis) * 100

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

    top_gainers = sorted(positions_payload, key=lambda x: x["pnl_percent"], reverse=True)[:3]
    top_losers = sorted(positions_payload, key=lambda x: x["pnl_percent"])[:3]

    return {
        "totalCurrentValue": summary["currentValue"],
        "totalInvestedValue": summary["investedValue"],
        "totalPnL": summary["pnl"],
        "totalPnLPercent": summary["pnlPercent"],
        "positions": positions_payload,
        "topGainers": top_gainers,
        "topLosers": top_losers,
        "benchmark": {
            "name": "S&P 500 (SPY)",
            "period": "30d",
            "note": "Базовое сравнение можно расширить отдельным endpoint для benchmark history.",
        },
    }
