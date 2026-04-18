import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { login } from '../api/auth';
import '../styles/auth.css';

const LOGIN_ERROR_MESSAGE = 'Не удалось выполнить вход';
const EMAIL_VALIDATION_MESSAGE = 'Введите корректный email с @';

const LoginPage: React.FC = () => {
  const location = useLocation();
  const navigationState = location.state as { registeredEmail?: string; successMessage?: string } | null;
  const [email, setEmail] = useState(navigationState?.registeredEmail || '');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login({ email, password });
      navigate('/');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail || LOGIN_ERROR_MESSAGE);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">Вход в систему</h1>
        {navigationState?.successMessage && <div className="auth-success">{navigationState.successMessage}</div>}
        <form className="auth-form" onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="auth-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onInvalid={(e) => {
                e.currentTarget.setCustomValidity(EMAIL_VALIDATION_MESSAGE);
              }}
              onInput={(e) => {
                e.currentTarget.setCustomValidity('');
              }}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              type="password"
              className="auth-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="auth-button">
            Войти
          </button>
        </form>
        <Link to="/register" className="auth-link">
          Создать аккаунт
        </Link>
      </div>
    </div>
  );
};

export default LoginPage;
