import React, { createContext, useState, useContext, useEffect } from "react";
import { authService } from "../services/authService";
import axios from "axios";

axios.defaults.withCredentials = true;

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  // Загружаем сохраненные данные пользователя (имя, email) для отображения в UI
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Эффект только для сохранения данных ЮЗЕРА в localStorage (чтобы не слетало имя при F5)
  // Токен мы здесь больше не трогаем — он живет в защищенной куке
  useEffect(() => {
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    } else {
      localStorage.removeItem("user");
    }
    // Мы убрали отсюда axios.defaults.headers...
    // так как браузер теперь сам прикрепляет куку
  }, [user]);

  const login = async (credentials) => {
    try {
      setIsLoading(true);
      setError(null);
      console.log("[AuthProvider] Logging in with credentials:", credentials);

      // authService делает запрос, и браузер автоматически сохраняет полученную куку
      const response = await authService.login(credentials);

      // Так как бекенд возвращает UserResponseSchema, скорее всего данные пользователя
      // лежат либо в корне ответа, либо в поле user.
      // Проверяем оба варианта для надежности:
      const loggedUser = response.user || response;

      console.log("[AuthProvider] Login success, user:", loggedUser);

      // Сохраняем только данные пользователя, токен нам в стейте не нужен
      setUser(loggedUser);
      return loggedUser;
    } catch (err) {
      console.error(
        "[AuthProvider] Login error:",
        err.response?.data || err.message,
      );
      setError(err.response?.data?.detail || "Ошибка входа");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (userData) => {
    try {
      setIsLoading(true);
      setError(null);
      console.log("[AuthProvider] Signing up with userData:", userData);

      const response = await authService.signup(userData);

      const newUser = response.user || response;
      console.log("[AuthProvider] Signup success, user:", newUser);

      setUser(newUser);
      return newUser;
    } catch (err) {
      console.error(
        "[AuthProvider] Signup error:",
        err.response?.data || err.message,
      );
      setError(err.response?.data?.detail || "Ошибка регистрации");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Желательно сделать запрос на бекенд, чтобы он очистил куку (set-cookie max-age=0)
      // Если у тебя есть такой эндпоинт, раскомментируй строку ниже:
      // await axios.post("http://localhost:8000/auth/logout");
    } catch (e) {
      console.error("Logout warning:", e);
    }

    // Очищаем локальное состояние
    setUser(null);
    setError(null);
    localStorage.removeItem("user");
    localStorage.removeItem("chats");
    window.location.href = "/login";
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    user,
    isLoading,
    error,
    login,
    signup,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};