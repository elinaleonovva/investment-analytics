import datetime

from _decimal import Decimal
from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from fixings.models import Index, Currency
from fixings.serializers import CurrencySerializer
from .models import Portfolio, Trade
from .serializers import PortfolioListSerializer, PortfolioDetailSerializer, TradeSerializer, \
    PortfolioAnalyticsSerializer
from .services.analytics import build_portfolio_analytics
from .services.reports import build_portfolio_pdf_report


class PortfolioListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        currency = request.query_params.get("currency", "USD")
        portfolios = Portfolio.objects.filter(userId=request.user).prefetch_related("trades__stockId")

        serializer = PortfolioListSerializer(
            portfolios,
            many=True,
            context={"currency": currency},
        )
        response = {"portfolios": serializer.data}
        currency_instance = Currency.objects.filter(currency=currency).first()
        if currency_instance:
            response["currency"] = CurrencySerializer(currency_instance).data
        return Response(response)

    def post(self, request):
        name = request.data.get("name") or f"Новый портфель от {datetime.date.today()}"
        portfolio = Portfolio.objects.create(userId=request.user, name=name)
        serializer = PortfolioDetailSerializer(portfolio, context={"currency": "USD"})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PortfolioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        currency = request.query_params.get("currency", "USD")
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        serializer = PortfolioDetailSerializer(portfolio, context={"currency": currency})
        return Response(serializer.data)

    def patch(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        new_name = request.data.get("name")
        if not new_name:
            return Response({"error": "Необходимо указать название портфеля"}, status=status.HTTP_400_BAD_REQUEST)
        portfolio.name = new_name
        portfolio.save(update_fields=["name"])
        return Response({"success": True, "name": portfolio.name})

    def delete(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        portfolio.delete()
        return Response({"success": True})


class PortfolioTradesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        trades = portfolio.trades.select_related("stockId__ccyId").all()
        serializer = TradeSerializer(trades, many=True, context={"currency": request.query_params.get("currency", "USD")})
        return Response({"trades": serializer.data})

    def post(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        serializer = TradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stock = get_object_or_404(Index, pk=serializer.validated_data["stockId"].id)
        quantity = serializer.validated_data["quantity"]
        trade_date = serializer.validated_data["tradeDate"]
        side = serializer.validated_data["side"]
        currency = request.query_params.get("currency", "USD")

        if quantity <= 0:
            return Response({"error": "Количество должно быть больше нуля"}, status=status.HTTP_400_BAD_REQUEST)

        if side == Trade.Side.SELL:
            first_buy = portfolio.trades.filter(
                stockId=stock,
                side=Trade.Side.BUY,
            ).order_by("tradeDate", "id").first()

            if not first_buy or trade_date < first_buy.tradeDate:
                return Response(
                    {"error": "Дата продажи не может быть раньше даты покупки"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            historical_quantity = Decimal("0")
            historical_trades = portfolio.trades.filter(
                stockId=stock,
                tradeDate__lte=trade_date,
            ).order_by("tradeDate", "id")
            for historical_trade in historical_trades:
                if historical_trade.side == Trade.Side.BUY:
                    historical_quantity += historical_trade.quantity
                elif historical_trade.side == Trade.Side.SELL:
                    historical_quantity -= historical_trade.quantity

            if quantity > historical_quantity:
                current_qty_int = int(historical_quantity)
                quantity_int = int(quantity)
                return Response(
                    {"error": f"Недостаточно количества для продажи на выбранную дату. Доступно: {current_qty_int}, попытка продать: {quantity_int}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            positions = portfolio.get_positions_analytics(currency=currency)
            current_qty = positions.get(stock.id, {}).get("quantity", Decimal("0"))
            if quantity > current_qty:
                current_qty_int = int(current_qty)
                quantity_int = int(quantity)
                return Response(
                    {"error": f"Недостаточно количества для продажи. Доступно: {current_qty_int}, попытка продать: {quantity_int}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        price_per_share = stock.get_price(date=trade_date)

        if not price_per_share or price_per_share <= 0:
            return Response({"error": "Не удалось получить цену инструмента на выбранную дату"}, status=status.HTTP_400_BAD_REQUEST)

        trade = Trade.objects.create(
            portfolioId=portfolio,
            stockId=stock,
            side=side,
            quantity=quantity,
            price_per_share=price_per_share,
            tradeDate=trade_date,
        )
        return Response(
            TradeSerializer(trade, context={"currency": currency}).data,
            status=status.HTTP_201_CREATED,
        )


class TradeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, trade_id):
        trade = get_object_or_404(Trade, pk=trade_id, portfolioId__userId=request.user)
        trade.delete()
        return Response({"success": True})


class PortfolioAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioAnalyticsSerializer

    def get(self, request, pk):
        currency = request.query_params.get("currency", "USD")
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)

        analytics_payload = build_portfolio_analytics(
            portfolio=portfolio,
            currency=currency
        )

        serializer = self.serializer_class(analytics_payload)
        return Response(serializer.data)


class PortfolioReportPdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        currency = request.query_params.get("currency", "USD")
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        analytics_payload = build_portfolio_analytics(portfolio=portfolio, currency=currency)
        pdf_stream = build_portfolio_pdf_report(portfolio, analytics_payload, currency=currency)

        response = HttpResponse(pdf_stream.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="portfolio_{pk}_report.pdf"'
        return response
