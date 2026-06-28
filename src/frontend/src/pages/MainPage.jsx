import React from "react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

const MainPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (user) {
      navigate("/chat");
    }
  }, [user, navigate]);

  return (
    <div className="main-page">
      <div className="hero-section">
        <div className="container">
          <h1 className="hero-title">Ваш AI Помощник</h1>
          <p className="hero-subtitle">
            Современный искусственный интеллект для решения ваших задач
          </p>
          <div className="hero-buttons">
            <button
              className="btn btn-primary"
              onClick={() => navigate("/auth?tab=login")}
            >
              Войти
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => navigate("/auth?tab=signup")}
            >
              Зарегистрироваться
            </button>
          </div>
        </div>
      </div>

      <div className="features-section">
        <div className="container">
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Быстрые ответы</h3>
              <p>Мгновенные решения ваших вопросов</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Точные решения</h3>
              <p>Качественные и релевантные ответы</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Безопасность</h3>
              <p>Ваши данные защищены</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainPage;
