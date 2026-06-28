import React from "react";

const Input = ({
  label,
  error,
  fullWidth = false,
  className = "",
  ...props
}) => {
  return (
    <div className={`form-group ${fullWidth ? "full-width" : ""}`}>
      {label && (
        <label htmlFor={props.id} className="input-label">
          {label}
        </label>
      )}

      <input
        className={`input ${error ? "input-error" : ""} ${className}`}
        {...props}
      />

      {error && <span className="error-text">{error}</span>}
    </div>
  );
};

export default Input;
