import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

const Signup = () => {
  const [formData, setFormData] = useState({
    name: "",
    surname: "",
    patronymic: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const { signup, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Очищаем ошибку для поля при изменении
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: "",
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Валидация имени
    if (!formData.name.trim()) {
      newErrors.name = "Имя обязательно";
    }

    // Валидация фамилии
    if (!formData.surname.trim()) {
      newErrors.surname = "Фамилия обязательна";
    }

    // Валидация email
    if (!formData.email.trim()) {
      newErrors.email = "Email обязателен";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Некорректный формат email";
    }

    // Валидация пароля
    if (!formData.password) {
      newErrors.password = "Пароль обязателен";
    } else if (formData.password.length < 6) {
      newErrors.password = "Пароль должен быть не менее 6 символов";
    }

    // Подтверждение пароля
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Пароли не совпадают";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      // Подготавливаем данные для отправки (убираем confirmPassword)
      const { confirmPassword, ...userData } = formData;

      await signup(userData);
      navigate("/chat");
    } catch (error) {
      if (error.response?.status === 409) {
        setErrors({ submit: "Пользователь с таким email уже существует" });
      } else {
        setErrors({ submit: "Ошибка регистрации. Попробуйте снова." });
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      {/* Поле имени */}
      <div className="form-group">
        <label htmlFor="name">Имя *</label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className={errors.name ? "error" : ""}
          placeholder="Введите ваше имя"
        />
        {errors.name && <span className="error-text">{errors.name}</span>}
      </div>

      {/* Поле фамилии */}
      <div className="form-group">
        <label htmlFor="surname">Фамилия *</label>
        <input
          type="text"
          id="surname"
          name="surname"
          value={formData.surname}
          onChange={handleChange}
          className={errors.surname ? "error" : ""}
          placeholder="Введите вашу фамилию"
        />
        {errors.surname && <span className="error-text">{errors.surname}</span>}
      </div>

      {/* Поле отчества (необязательное) */}
      <div className="form-group">
        <label htmlFor="patronymic">Отчество</label>
        <input
          type="text"
          id="patronymic"
          name="patronymic"
          value={formData.patronymic}
          onChange={handleChange}
          className={errors.patronymic ? "error" : ""}
          placeholder="Введите ваше отчество (если есть)"
        />
        {errors.patronymic && (
          <span className="error-text">{errors.patronymic}</span>
        )}
      </div>

      {/* Поле email */}
      <div className="form-group">
        <label htmlFor="email">Email *</label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          className={errors.email ? "error" : ""}
          placeholder="your@email.com"
        />
        {errors.email && <span className="error-text">{errors.email}</span>}
      </div>

      {/* Поле пароля */}
      <div className="form-group">
        <label htmlFor="password">Пароль *</label>
        <input
          type="password"
          id="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          className={errors.password ? "error" : ""}
          placeholder="Не менее 6 символов"
        />
        {errors.password && (
          <span className="error-text">{errors.password}</span>
        )}
      </div>

      {/* Подтверждение пароля */}
      <div className="form-group">
        <label htmlFor="confirmPassword">Подтвердите пароль *</label>
        <input
          type="password"
          id="confirmPassword"
          name="confirmPassword"
          value={formData.confirmPassword}
          onChange={handleChange}
          className={errors.confirmPassword ? "error" : ""}
          placeholder="Повторите пароль"
        />
        {errors.confirmPassword && (
          <span className="error-text">{errors.confirmPassword}</span>
        )}
      </div>

      {/* Общая ошибка */}
      {errors.submit && <div className="error-message">{errors.submit}</div>}

      {/* Кнопка отправки */}
      <button
        type="submit"
        className="btn btn-primary full-width"
        disabled={isLoading}
      >
        {isLoading ? "Регистрация..." : "Зарегистрироваться"}
      </button>
    </form>
  );
};

export default Signup;
