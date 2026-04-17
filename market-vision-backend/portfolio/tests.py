import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from authentication.models import User
from fixings.models import Currency, Index
from portfolio.models import Portfolio, Trade
from portfolio.serializers import TradeSerializer
from portfolio.services.analytics import build_portfolio_analytics


class PortfolioAnalyticsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="tester@example.com", password="secret123")
        self.usd = Currency.objects.create(currency="USD", symbol="$", ticker="USD")
        self.stock = Index.objects.create(indexName="Test Asset", indexISIN="TST", ccyId=self.usd)
        self.portfolio = Portfolio.objects.create(userId=self.user, name="Main")

    @patch("fixings.models.Index.get_price")
    def test_summary_keeps_realized_pnl_for_closed_position(self, mock_get_price):
        mock_get_price.return_value = Decimal("120")

        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 1, 10),
        )
        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.SELL,
            quantity=Decimal("10"),
            price_per_share=Decimal("120"),
            tradeDate=datetime.date(2026, 1, 11),
        )

        summary = self.portfolio.get_portfolio_summary(currency="USD")

        self.assertEqual(summary["currentValue"], Decimal("0"))
        self.assertEqual(summary["investedValue"], Decimal("0"))
        self.assertEqual(summary["pnl"], Decimal("200"))
        self.assertEqual(summary["pnlPercent"], Decimal("20"))
        self.assertEqual(self.portfolio.get_pnl(currency="USD"), Decimal("200"))

    @patch("fixings.models.Index.get_price")
    def test_analytics_uses_total_position_pnl_with_realized_component(self, mock_get_price):
        mock_get_price.return_value = Decimal("120")

        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 1, 10),
        )
        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.SELL,
            quantity=Decimal("4"),
            price_per_share=Decimal("130"),
            tradeDate=datetime.date(2026, 1, 11),
        )

        analytics = build_portfolio_analytics(self.portfolio, currency="USD")

        self.assertEqual(analytics["totalCurrentValue"], Decimal("720"))
        self.assertEqual(analytics["totalInvestedValue"], Decimal("600"))
        self.assertEqual(analytics["totalPnL"], Decimal("240"))
        self.assertEqual(analytics["positions"][0]["pnl"], Decimal("240"))
        self.assertEqual(analytics["totalPnLPercent"], Decimal("24"))
        self.assertEqual(analytics["positions"][0]["pnl_percent"], Decimal("24"))

    def test_trade_serializer_includes_price_per_share(self):
        trade = Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("1"),
            price_per_share=Decimal("123.45"),
            tradeDate=datetime.date(2026, 4, 17),
        )

        serialized = TradeSerializer(trade).data

        self.assertIn("price_per_share", serialized)
        self.assertEqual(Decimal(str(serialized["price_per_share"])), Decimal("123.45"))

    def test_trade_serializer_allows_create_without_price_per_share(self):
        serializer = TradeSerializer(
            data={
                "stockId": self.stock.id,
                "side": Trade.Side.BUY,
                "quantity": "1",
                "tradeDate": "2026-04-17",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
