import React, { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';
import { Currency, Portfolio } from '../types';
import '../styles/portfolios.css';

const PortfoliosPage: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [currency, setCurrency] = useState<Currency | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [availableCurrencies, setAvailableCurrencies] = useState<Currency[]>([]);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [currenciesResponse, portfoliosResponse] = await Promise.all([
        api.get('/fixings/reference/currencies/'),
        api.get('/portfolio/portfolios/', { params: { currency: selectedCurrency } }),
      ]);
      setAvailableCurrencies(currenciesResponse.data || []);
      setPortfolios(portfoliosResponse.data.portfolios || []);
      setCurrency(portfoliosResponse.data.currency || null);
    } catch (_error) {
      setError('Не удалось загрузить портфели. Проверь, что backend запущен и ты авторизована.');
      setPortfolios([]);
    } finally {
      setLoading(false);
    }
  }, [selectedCurrency]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const handleCreatePortfolio = async () => {
    if (!newPortfolioName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const response = await api.post('/portfolio/portfolios/', { name: newPortfolioName.trim() });
      setNewPortfolioName('');
      navigate(`/portfolio/${response.data.id}`);
    } catch (_error) {
      setError('Ошибка создания портфеля.');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/portfolio/portfolios/${id}/`);
      await fetchData();
    } catch (_error) {
      setError('Ошибка удаления портфеля.');
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Портфели</h1>
        <select
          className="select"
          value={selectedCurrency}
          onChange={(e) => setSelectedCurrency(e.target.value)}
        >
          {availableCurrencies.map((item) => (
            <option key={item.id} value={item.currency}>
              {item.currency}
            </option>
          ))}
        </select>
      </div>

      <section className="panel">
        <h2>Создать портфель</h2>
        <div className="inline-form">
          <input
            className="input"
            value={newPortfolioName}
            onChange={(e) => setNewPortfolioName(e.target.value)}
            placeholder="Название портфеля"
          />
          <button className="button" onClick={handleCreatePortfolio} disabled={creating}>
            {creating ? 'Создание...' : 'Создать'}
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Список портфелей</h2>
        {error && <p className="negative">{error}</p>}
        {loading ? (
          <p>Загрузка...</p>
        ) : (
          <div className="portfolio-grid">
            {portfolios.map((portfolio) => (
              <article key={portfolio.id} className="portfolio-card">
                <h3>{portfolio.name}</h3>
                <p>Текущая стоимость: {Number(portfolio.currentValue).toFixed(2)} {currency?.symbol || ''}</p>
                <p>Вложено: {Number(portfolio.investedValue).toFixed(2)}</p>
                <p className={Number(portfolio.pnlPercent) >= 0 ? 'positive' : 'negative'}>
                  PnL: {Number(portfolio.pnl).toFixed(2)} ({Number(portfolio.pnlPercent).toFixed(2)}%)
                </p>
                <div className="card-actions">
                  <button className="button" onClick={() => navigate(`/portfolio/${portfolio.id}`)}>
                    Открыть
                  </button>
                  <button className="button button-danger" onClick={() => handleDelete(portfolio.id)}>
                    Удалить
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default PortfoliosPage;
