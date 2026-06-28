import React from "react";

const Button = ({
  children,
  variant = "primary",
  disabled = false,
  loading = false,
  fullWidth = false,
  onClick,
  type = "button",
  className = "",
  ...props
}) => {
  const baseClasses = "btn";
  const variantClasses = {
    primary: "btn-primary",
    secondary: "btn-secondary",
  };

  const classes = [
    baseClasses,
    variantClasses[variant],
    fullWidth && "btn-full-width",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading ? "Загрузка..." : children}
    </button>
  );
};

export default Button;
