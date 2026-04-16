export interface Currency {
  id: number;
  currency: string;
  symbol: string;
}

export interface Stock {
  id: number;
  indexName: string;
  indexISIN: string;
  currency: Currency;
  currentPrice: number | string;
  currentConvertedPrice: number | string;
  monthlyDynamic: number | string;
}

export interface MarketCurrency {
  id: number;
  currency: string;
  symbol: string;
  rateToRequestedCurrency: number | string;
  monthlyDynamic: number | string;
}

export interface Metal {
  id: number;
  code: string;
  name: string;
  symbol: string;
  currentConvertedPrice: number | string;
  monthlyDynamic: number | string;
}

export interface Portfolio {
  id: number;
  name: string;
  currentValue: number | string;
  investedValue: number | string;
  pnl: number | string;
  pnlPercent: number | string;
}

export interface Trade {
  id: number;
  stockId: number;
  stock?: Stock;
  side: "BUY" | "SELL";
  quantity: number | string;
  price_per_share: number | string;
  tradeDate: string;
  created_at: string;
}

export interface PortfolioDetail extends Portfolio {
  created_at: string;
  currency?: Currency | null;
}

export interface AnalyticsPosition {
  stock: Stock;
  quantity: number | string;
  invested: number | string;
  current_value: number | string;
  pnl: number | string;
  pnl_percent: number | string;
}

export interface PortfolioAnalytics {
  totalCurrentValue: number | string;
  totalInvestedValue: number | string;
  totalPnL: number | string;
  totalPnLPercent: number | string;
  positions: AnalyticsPosition[];
  topGainers: AnalyticsPosition[];
  topLosers: AnalyticsPosition[];
  benchmark: {
    name: string;
    period: string;
    note: string;
  };
}
