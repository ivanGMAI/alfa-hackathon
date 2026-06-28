import React from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import Login from "../components/Auth/Login";
import Signup from "../components/Auth/Signup";

const AuthPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const currentTab = searchParams.get("tab") || "login";

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>Добро пожаловать</h1>
          <p>Войдите или создайте аккаунт</p>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${currentTab === "login" ? "active" : ""}`}
            onClick={() => navigate("/auth?tab=login")}
          >
            Вход
          </button>
          <button
            className={`auth-tab ${currentTab === "signup" ? "active" : ""}`}
            onClick={() => navigate("/auth?tab=signup")}
          >
            Регистрация
          </button>
        </div>

        <div className="auth-content">
          {currentTab === "login" ? <Login /> : <Signup />}
        </div>

        <div className="auth-footer">
          <button
            className="btn btn-secondary full-width"
            onClick={() => navigate("/")}
          >
            Назад на главную
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
