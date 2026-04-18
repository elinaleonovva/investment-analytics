import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import api, { toNumber } from '../api/client';
import { Currency, PortfolioAnalytics, PortfolioDetail, Stock, Trade } from '../types';
import '../styles/portfolio-details.css';

type TabType = 'overview' | 'trades' | 'reports';
const EXCLUDED_STOCK_TICKERS = new Set(['BRK.B']);

interface Props {
  activeTab?: TabType;
}

const PortfolioDetailsPage: React.FC<Props> = ({ activeTab }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const portfolioId = Number(id);
  const currentTab: TabType = activeTab || 'overview';

  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [stocks, setStocks] = useState<Stock[]>([]);

  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [analytics, setAnalytics] = useState<PortfolioAnalytics | null>(null);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newName, setNewName] = useState('');

  const [tradeForm, setTradeForm] = useState({
    stockId: 0,
    side: 'BUY' as 'BUY' | 'SELL',
    quantity: '1',
    tradeDate: new Date().toISOString().slice(0, 10),
  });

  const tabs = useMemo(
    () => [
      { key: 'overview', label: 'Обзор портфеля', path: `/portfolio/${portfolioId}` },
      { key: 'trades', label: 'Сделки', path: `/portfolio/${portfolioId}/trades` },
      { key: 'reports', label: 'Отчеты', path: `/portfolio/${portfolioId}/reports` },
    ],
    [portfolioId]
  );

  const loadBaseData = useCallback(async () => {
    const [currenciesRes, stocksRes, portfolioRes] = await Promise.all([
      api.get('/fixings/reference/currencies/'),
      api.get('/fixings/reference/stocks/', { params: { currency: selectedCurrency } }),
      api.get(`/portfolio/portfolios/${portfolioId}/`, { params: { currency: selectedCurrency } }),
    ]);
    const currenciesData = currenciesRes.data || [];
    const stocksData = (stocksRes.data || []).filter(
      (stock: Stock) => !EXCLUDED_STOCK_TICKERS.has(stock.indexISIN)
    );

    setCurrencies(currenciesData);
    setStocks(stocksData);
    setPortfolio(portfolioRes.data);
    setNewName(portfolioRes.data?.name || '');

    if (!tradeForm.stockId && stocksData.length > 0) {
      setTradeForm((prev) => ({ ...prev, stockId: stocksData[0].id }));
    }
  }, [portfolioId, selectedCurrency]);

  const loadTabData = useCallback(async () => {
    if (currentTab === 'trades') {
      const response = await api.get(`/portfolio/portfolios/${portfolioId}/trades/`, {
        params: { currency: selectedCurrency }
      });
      setTrades(response.data?.trades || []);
    } else if (currentTab === 'overview') {
      const response = await api.get(`/portfolio/portfolios/${portfolioId}/analytics/`, {
        params: { currency: selectedCurrency },
      });
      setAnalytics(response.data);
    }
  }, [currentTab, portfolioId, selectedCurrency]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await loadBaseData();
      await loadTabData();
    } catch (_error) {
      setError('Не удалось загрузить данные портфеля. Проверь backend и авторизацию.');
    } finally {
      setLoading(false);
    }
  }, [loadBaseData, loadTabData]);

  useEffect(() => {
    if (!Number.isNaN(portfolioId)) {
      void loadData();
    }
  }, [portfolioId, loadData, selectedCurrency]);

  const handleRename = async () => {
    if (!newName.trim()) return;
    setSaving(true);
    try {
      await api.patch(`/portfolio/portfolios/${portfolioId}/`, { name: newName.trim() });
      await loadData();
    } catch (_error) {
      setError('Ошибка переименования портфеля.');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateTrade = async () => {
    setSaving(true);
    setError(null);
    try {
      const quantity = Number.parseInt(tradeForm.quantity, 10);

      if (!Number.isInteger(quantity) || quantity <= 0) {
        setError('Количество должно быть целым числом больше нуля.');
        return;
      }

      await api.post(`/portfolio/portfolios/${portfolioId}/trades/`, {
        stockId: tradeForm.stockId,
        side: tradeForm.side,
        quantity,
        tradeDate: tradeForm.tradeDate,
      }, { params: { currency: selectedCurrency } });
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Ошибка создания сделки.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTrade = async (tradeId: number) => {
    try {
      await api.delete(`/portfolio/trades/${tradeId}/`);
      await loadData();
    } catch (_error) {
      setError('Ошибка удаления сделки.');
    }
  };

  const handleDownloadPdf = async () => {
    try {
      const response = await api.get(`/portfolio/portfolios/${portfolioId}/report/pdf/`, {
        params: { currency: selectedCurrency },
        responseType: 'blob',
      });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', `portfolio_${portfolioId}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (_error) {
      setError('Ошибка генерации PDF отчета.');
    }
  };

  if (loading && !portfolio) {
    return <div className="page"><div className="panel">Загрузка...</div></div>;
  }

  if (!portfolio) {
    return <div className="page"><div className="panel">Портфель не найден.</div></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>{portfolio.name}</h1>
        <div className="header-actions">
          <span className="currency-label">Валюта отображения:</span>
          <select
            className="select"
            value={selectedCurrency}
            onChange={(e) => setSelectedCurrency(e.target.value)}
          >
            {currencies.map((item) => (
              <option key={item.id} value={item.currency}>{item.currency}</option>
            ))}
          </select>
          <button className="button button-secondary" onClick={() => navigate('/portfolios')}>
            К списку
          </button>
        </div>
      </div>

      <nav className="subnav">
        {tabs.map((tab) => (
          <Link
            key={tab.key}
            to={tab.path}
            className={`subnav-link ${tab.key === currentTab ? 'active' : ''}`}
          >
            {tab.label}
          </Link>
        ))}
      </nav>

      {error && <section className="panel"><p className="negative">{error}</p></section>}

      {currentTab === 'overview' && (
        <section className="panel">
          <div className="inline-form" style={{ marginBottom: '20px' }}>
            <input className="input" value={newName} onChange={(e) => setNewName(e.target.value)} />
            <button className="button" onClick={handleRename} disabled={saving}>
              {saving ? 'Сохранение...' : 'Переименовать'}
            </button>
          </div>

          <h2>Сводка ({selectedCurrency})</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Текущая стоимость</div>
              <div className="stat-value">{Number(portfolio.currentValue).toFixed(2)} {selectedCurrency}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Вложено в открытые позиции</div>
              <div className="stat-value">{Number(portfolio.investedValue).toFixed(2)} {selectedCurrency}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Общий PnL</div>
              <div className={`stat-value ${Number(portfolio.pnl) >= 0 ? 'positive' : 'negative'}`}>
                {Number(portfolio.pnl).toFixed(2)} {selectedCurrency}
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Доходность</div>
              <div className={`stat-value ${Number(portfolio.pnlPercent) >= 0 ? 'positive' : 'negative'}`}>
                {Number(portfolio.pnlPercent).toFixed(2)}%
              </div>
            </div>
          </div>

          {analytics && analytics.positions.length > 0 && (
            <>
              <h3 style={{ marginTop: '30px' }}>Открытые позиции</h3>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Тикер</th>
                      <th>Количество</th>
                      <th>Вложено ({selectedCurrency})</th>
                      <th>Текущая стоимость ({selectedCurrency})</th>
                      <th>PnL ({selectedCurrency})</th>
                      <th>PnL %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.positions.map((position, idx) => (
                      <tr key={`${position.stock.id}-${idx}`}>
                        <td>{position.stock.indexISIN}</td>
                        <td>{toNumber(position.quantity).toFixed(0)}</td>
                        <td>{Number(position.invested).toFixed(2)}</td>
                        <td>{Number(position.current_value).toFixed(2)}</td>
                        <td className={Number(position.pnl) >= 0 ? 'positive' : 'negative'}>
                          {Number(position.pnl).toFixed(2)}
                        </td>
                        <td className={Number(position.pnl_percent) >= 0 ? 'positive' : 'negative'}>
                          {Number(position.pnl_percent).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      )}

      {currentTab === 'trades' && (
        <>
          <section className="panel">
            <h2>Добавить сделку</h2>
            <div className="trade-form-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
              <select
                className="select"
                value={tradeForm.stockId}
                onChange={(e) => setTradeForm((prev) => ({ ...prev, stockId: Number(e.target.value) }))}
              >
                {stocks.map((stock) => (
                  <option key={stock.id} value={stock.id}>
                    {stock.indexISIN}
                  </option>
                ))}
              </select>
              <select
                className="select"
                value={tradeForm.side}
                onChange={(e) => setTradeForm((prev) => ({ ...prev, side: e.target.value as 'BUY' | 'SELL' }))}
              >
                <option value="BUY">Покупка (BUY)</option>
                <option value="SELL">Продажа (SELL)</option>
              </select>
              <input
                className="input"
                type="number"
                step="1"
                min="1"
                placeholder="Количество"
                value={tradeForm.quantity}
                onChange={(e) => setTradeForm((prev) => ({ ...prev, quantity: e.target.value }))}
              />
              <input
                className="input"
                type="date"
                value={tradeForm.tradeDate}
                onChange={(e) => setTradeForm((prev) => ({ ...prev, tradeDate: e.target.value }))}
              />
              <button className="button" onClick={handleCreateTrade} disabled={saving} style={{ gridColumn: 'span 4' }}>
                {saving ? 'Сохранение...' : 'Зафиксировать сделку'}
              </button>
            </div>
            <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
              *Цена исполнения будет автоматически рассчитана на основе котировок за выбранную дату.
            </p>
          </section>

          <section className="panel">
            <h2>История сделок</h2>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Дата</th>
                    <th>Тикер</th>
                    <th>Операция</th>
                    <th>Кол-во</th>
                    <th>Цена исполнения ({selectedCurrency})</th>
                    <th>Объем ({selectedCurrency})</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {trades.map((trade) => {
                    const quantity = toNumber(trade.quantity);
                    const pricePerShare = toNumber(trade.price_per_share);
                    const volume = quantity * pricePerShare;
                    return (
                      <tr key={trade.id}>
                        <td>{trade.tradeDate}</td>
                        <td><strong>{trade.stock?.indexISIN || '-'}</strong></td>
                        <td className={trade.side === 'BUY' ? 'positive' : 'negative'}>
                          {trade.side === 'BUY' ? 'ПОКУПКА' : 'ПРОДАЖА'}
                        </td>
                        <td>{quantity.toFixed(0)}</td>
                        <td>{pricePerShare.toFixed(2)}</td>
                        <td>{volume.toFixed(2)}</td>
                        <td style={{ textAlign: 'right' }}>
                          <button className="button button-danger" onClick={() => handleDeleteTrade(trade.id)}>
                            Удалить
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {currentTab === 'reports' && (
        <section className="panel">
          <h2>Отчеты</h2>
          <p>Сформировать PDF-отчет по текущему портфелю.</p>
          <button className="button" onClick={handleDownloadPdf}>
            Скачать PDF
          </button>
        </section>
      )}
    </div>
  );
};

export default PortfolioDetailsPage;
