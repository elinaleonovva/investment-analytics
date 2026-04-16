from django.urls import path
from .views import (
    PortfolioAnalyticsView,
    PortfolioDetailView,
    PortfolioListView,
    PortfolioReportPdfView,
    PortfolioTradesView,
    TradeDetailView,
)

urlpatterns = [
    path("portfolios/", PortfolioListView.as_view(), name="portfolio-list"),
    path("portfolios/<int:pk>/", PortfolioDetailView.as_view(), name="portfolio-detail"),
    path("portfolios/<int:pk>/trades/", PortfolioTradesView.as_view(), name="portfolio-trades"),
    path("trades/<int:trade_id>/", TradeDetailView.as_view(), name="trade-detail"),
    path("portfolios/<int:pk>/analytics/", PortfolioAnalyticsView.as_view(), name="portfolio-analytics"),
    path("portfolios/<int:pk>/report/pdf/", PortfolioReportPdfView.as_view(), name="portfolio-report-pdf"),
]
