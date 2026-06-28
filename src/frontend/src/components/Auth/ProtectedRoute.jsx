import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();

  // Если пользователь есть в localStorage, но нет в состоянии
  // (например, после обновления страницы)
  React.useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser && !user) {
      // Можно автоматически восстановить пользователя
      console.log("User found in localStorage");
    }
  }, [user]);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
