import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { logout } from '../api/auth';
import '../styles/header.css';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const isAuthed = Boolean(localStorage.getItem('access_token'));

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="header">
      <nav className="nav-container">
        <Link to={isAuthed ? '/' : '/login'} className="brand-link">
          Investment Analyst
        </Link>
        {isAuthed && (
          <div className="nav-links">
            <Link to="/" className="nav-link">
              Рынок
            </Link>
            <Link to="/portfolios" className="nav-link">
              Портфели
            </Link>
            <button onClick={handleLogout} className="logout-button">
              Выйти
            </button>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;