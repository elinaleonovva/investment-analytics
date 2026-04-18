import React, { useCallback, useEffect, useState } from 'react';
import api, { toNumber } from '../api/client';
import { Currency, MarketCurrency, Metal, Stock } from '../types';
import '../styles/market.css';

const EXCLUDED_STOCK_TICKERS = new Set(['BRK.B']);

const MarketPage: React.FC = () => {
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [availableCurrencies, setAvailableCurrencies] = useState<Currency[]>([]);
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [currencies, setCurrencies] = useState<MarketCurrency[]>([]);
  const [metals, setMetals] = useState<Metal[]>([]);
  const [sectionsOpen, setSectionsOpen] = useState({
    stocks: false,
    currencies: false,
    metals: false,
  });
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleSection = (section: 'stocks' | 'currencies' | 'metals') => {
    setSectionsOpen((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [currRef, stocksRes, marketCurrenciesRes, metalsRes] = await Promise.all([
        api.get('/fixings/reference/currencies/'),
        api.get('/fixings/stocks/', { params: { currency: selectedCurrency, page_size: 200 } }),
        api.get('/fixings/market/currencies/', { params: { currency: selectedCurrency, page_size: 200 } }),
        api.get('/fixings/market/metals/', { params: { currency: selectedCurrency, page_size: 200 } }),
      ]);
      setAvailableCurrencies(currRef.data || []);
      const rawStocks = stocksRes.data.results || stocksRes.data || [];
      setStocks(rawStocks.filter((stock: Stock) => !EXCLUDED_STOCK_TICKERS.has(stock.indexISIN)));
      setCurrencies(marketCurrenciesRes.data.results || marketCurrenciesRes.data || []);
      setMetals(metalsRes.data.results || metalsRes.data || []);
    } catch (_error) {
      setError('Не удалось загрузить данные рынка. Проверь, запущен ли backend на порту 8000.');
      setStocks([]);
      setCurrencies([]);
      setMetals([]);
    } finally {
      setLoading(false);
    }
  }, [selectedCurrency]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const handleMarketUpdate = async () => {
    setUpdating(true);
    setError(null);
    try {
      await api.post('/fixings/market/update/', { days_back: 30 });
      await loadAll();
    } catch (_error) {
      setError('Ошибка обновления рынка. Проверь доступность backend и интернет для yfinance.');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Рынок</h1>
        <div className="header-actions">
          <select
            className="select"
            value={selectedCurrency}
            onChange={(e) => setSelectedCurrency(e.target.value)}
          >
            {availableCurrencies.map((currency) => (
              <option key={currency.id} value={currency.currency}>
                {currency.currency}
              </option>
            ))}
          </select>
          <button className="button button-secondary" onClick={handleMarketUpdate} disabled={updating}>
            {updating ? 'Обновление...' : 'Обновить рынок'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="panel">Загрузка данных...</div>
      ) : (
        <>
          {error && <section className="panel"><p className="negative">{error}</p></section>}

          <section className="panel">
            <button type="button" className="section-toggle" onClick={() => toggleSection('stocks')}>
              <span>Акции</span>
              <span>{sectionsOpen.stocks ? 'Скрыть' : 'Показать'}</span>
            </button>
            {sectionsOpen.stocks && (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Название</th>
                      <th>Тикер</th>
                      <th>Цена</th>
                      <th>Цена в {selectedCurrency}</th>
                      <th>30д, %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stocks.map((stock) => {
                      const dynamic = toNumber(stock.monthlyDynamic);
                      return (
                        <tr key={stock.id}>
                          <td>{stock.indexName}</td>
                          <td>{stock.indexISIN}</td>
                          <td>{toNumber(stock.currentPrice).toFixed(2)} {stock.currency?.symbol || ''}</td>
                          <td>{toNumber(stock.currentConvertedPrice).toFixed(2)}</td>
                          <td className={dynamic >= 0 ? 'positive' : 'negative'}>{dynamic.toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="panel">
            <button type="button" className="section-toggle" onClick={() => toggleSection('currencies')}>
              <span>Валюты</span>
              <span>{sectionsOpen.currencies ? 'Скрыть' : 'Показать'}</span>
            </button>
            {sectionsOpen.currencies && (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Код</th>
                      <th>Символ</th>
                      <th>Курс к {selectedCurrency}</th>
                      <th>30д, %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currencies.map((item) => {
                      const dynamic = toNumber(item.monthlyDynamic);
                      return (
                        <tr key={item.id}>
                          <td>{item.currency}</td>
                          <td>{item.symbol}</td>
                          <td>{toNumber(item.rateToRequestedCurrency).toFixed(4)}</td>
                          <td className={dynamic >= 0 ? 'positive' : 'negative'}>{dynamic.toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="panel">
            <button type="button" className="section-toggle" onClick={() => toggleSection('metals')}>
              <span>Драгоценные металлы</span>
              <span>{sectionsOpen.metals ? 'Скрыть' : 'Показать'}</span>
            </button>
            {sectionsOpen.metals && (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Код</th>
                      <th>Название</th>
                      <th>Цена в {selectedCurrency}</th>
                      <th>30д, %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metals.map((metal) => {
                      const dynamic = toNumber(metal.monthlyDynamic);
                      return (
                        <tr key={metal.id}>
                          <td>{metal.code}</td>
                          <td>{metal.name}</td>
                          <td>{toNumber(metal.currentConvertedPrice).toFixed(4)}</td>
                          <td className={dynamic >= 0 ? 'positive' : 'negative'}>{dynamic.toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
};

export default MarketPage;
