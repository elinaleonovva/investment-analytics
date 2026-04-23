import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

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

    @patch("fixings.models.Index.get_price")
    def test_analytics_ignores_invalid_sell_without_prior_quantity(self, mock_get_price):
        mock_get_price.return_value = Decimal("120")

        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.SELL,
            quantity=Decimal("10"),
            price_per_share=Decimal("120"),
            tradeDate=datetime.date(2026, 1, 9),
        )
        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 1, 10),
        )

        summary = self.portfolio.get_portfolio_summary(currency="USD")

        self.assertEqual(summary["currentValue"], Decimal("1200"))
        self.assertEqual(summary["investedValue"], Decimal("1000"))
        self.assertEqual(summary["pnl"], Decimal("200"))

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

    def test_create_trade_api_rejects_sell_before_first_buy_date(self):
        self.client.force_login(self.user)
        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 4, 17),
        )

        response = self.client.post(
            f"/api/portfolio/portfolios/{self.portfolio.id}/trades/",
            data={
                "stockId": self.stock.id,
                "side": Trade.Side.SELL,
                "quantity": "1",
                "tradeDate": "2026-04-16",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Дата продажи не может быть раньше даты покупки.")

    def test_create_trade_api_rejects_sell_more_than_available_on_trade_date(self):
        self.client.force_login(self.user)
        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("1"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 4, 16),
        )
        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("9"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 4, 17),
        )

        response = self.client.post(
            f"/api/portfolio/portfolios/{self.portfolio.id}/trades/",
            data={
                "stockId": self.stock.id,
                "side": Trade.Side.SELL,
                "quantity": "2",
                "tradeDate": "2026-04-16",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Недостаточно количества для продажи на выбранную дату. Доступно: 1, попытка продать: 2.",
        )

    @patch("fixings.models.Currency.get_rate_to")
    def test_trade_serializer_converts_price_per_share_to_requested_currency(self, mock_get_rate_to):
        mock_get_rate_to.return_value = Decimal("80")
        trade = Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("1"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 4, 17),
        )

        serialized = TradeSerializer(trade, context={"currency": "RUB"}).data

        self.assertEqual(Decimal(str(serialized["price_per_share"])), Decimal("8000"))

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

    def test_trade_serializer_rejects_fractional_quantity(self):
        serializer = TradeSerializer(
            data={
                "stockId": self.stock.id,
                "side": Trade.Side.BUY,
                "quantity": "1.5",
                "tradeDate": "2026-04-17",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["quantity"][0], "Количество должно быть целым числом.")

    def test_trade_serializer_rejects_future_trade_date(self):
        future_date = timezone.localdate() + datetime.timedelta(days=1)
        serializer = TradeSerializer(
            data={
                "stockId": self.stock.id,
                "side": Trade.Side.BUY,
                "quantity": "1",
                "tradeDate": future_date.isoformat(),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["tradeDate"][0], "Дата сделки не может быть в будущем.")

    def test_create_trade_api_rejects_future_trade_date(self):
        self.client.force_login(self.user)
        future_date = timezone.localdate() + datetime.timedelta(days=1)

        response = self.client.post(
            f"/portfolio/portfolios/{self.portfolio.id}/trades/",
            data={
                "stockId": self.stock.id,
                "side": Trade.Side.BUY,
                "quantity": "1",
                "tradeDate": future_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["tradeDate"][0], "Дата сделки не может быть в будущем.")

    @patch("fixings.models.Currency.get_rate_to")
    @patch("fixings.models.Index.get_price")
    def test_positions_analytics_converts_trade_cost_to_requested_currency(self, mock_get_price, mock_get_rate_to):
        def get_price_side_effect(request_currency=None, date=None):
            return Decimal("9600") if request_currency == "RUB" else Decimal("120")

        def get_rate_side_effect(request_currency="USD", date=None):
            return Decimal("80") if request_currency == "RUB" else Decimal("1")

        mock_get_price.side_effect = get_price_side_effect
        mock_get_rate_to.side_effect = get_rate_side_effect

        Trade.objects.create(
            portfolioId=self.portfolio,
            stockId=self.stock,
            side=Trade.Side.BUY,
            quantity=Decimal("1"),
            price_per_share=Decimal("100"),
            tradeDate=datetime.date(2026, 4, 17),
        )

        summary = self.portfolio.get_portfolio_summary(currency="RUB")

        self.assertEqual(summary["currentValue"], Decimal("9600"))
        self.assertEqual(summary["investedValue"], Decimal("8000"))
        self.assertEqual(summary["pnl"], Decimal("1600"))
        self.assertEqual(summary["pnlPercent"], Decimal("20"))
