import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { logout, register } from '../api/auth';
import '../styles/auth.css';

const DUPLICATE_EMAIL_ERRORS = new Set([
  'user with this email already exists.',
  'A user with that email already exists.',
  'Пользователь с таким email уже существует',
]);
const EMAIL_VALIDATION_MESSAGE = 'Введите корректный email';

const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await register({ email, password });
      logout();
      navigate('/login', {
        replace: true,
        state: {
          registeredEmail: email.trim().toLowerCase(),
          successMessage: 'Регистрация прошла успешно',
        },
      });
    } catch (err: any) {
      const emailError = err.response?.data?.email;
      const detail = err.response?.data?.detail;

      if (Array.isArray(emailError) && emailError.length > 0) {
        if (DUPLICATE_EMAIL_ERRORS.has(emailError[0])) {
          setError('Пользователь с таким email уже зарегистрирован');
          return;
        }

        setError(emailError[0]);
        return;
      }

      if (detail && DUPLICATE_EMAIL_ERRORS.has(detail)) {
        setError('Пользователь с таким email уже зарегистрирован');
        return;
      }

      setError(detail || 'Не удалось зарегистрироваться. Проверьте данные');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">Регистрация</h1>
        <p className="auth-subtitle">Доступ к разделам рынка и портфелей</p>
        <form className="auth-form" onSubmit={handleRegister}>
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
            Зарегистрироваться
          </button>
        </form>
        <Link to="/login" className="auth-link">
          Уже есть аккаунт? Войти
        </Link>
      </div>
    </div>
  );
};

export default RegisterPage;
