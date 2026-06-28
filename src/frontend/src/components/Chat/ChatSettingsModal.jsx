import React, { useState, useEffect } from "react";
import { useChat } from "../../contexts/ChatContext";

const ChatSettingsModal = ({ chat, isOpen, onClose }) => {
  const { updateChat, deleteChat } = useChat();
  const [title, setTitle] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (chat) {
      setTitle(chat.title || "");
    }
  }, [chat]);

  const handleUpdate = async (e) => {
    e.preventDefault();

    if (!title.trim()) {
      setError("Название чата не может быть пустым");
      return;
    }

    try {
      setIsLoading(true);
      setError("");

      await updateChat(chat.id, { title: title.trim() });
      onClose();
    } catch (error) {
      console.error("Failed to update chat:", error);
      setError("Ошибка при обновлении чата");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (
      !window.confirm(
        "Вы уверены, что хотите удалить этот чат? Все сообщения будут потеряны.",
      )
    ) {
      return;
    }

    try {
      setIsLoading(true);
      await deleteChat(chat.id);
      onClose();
    } catch (error) {
      console.error("Failed to delete chat:", error);
      setError("Ошибка при удалении чата");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen || !chat) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Настройки чата</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-content">
          <form onSubmit={handleUpdate}>
            <div className="form-group">
              <label className="input-label">Название чата</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="input"
                placeholder="Введите название чата..."
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="error-text" style={{ marginBottom: "1rem" }}>
                {error}
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
                disabled={isLoading}
              >
                Отмена
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isLoading || !title.trim()}
              >
                {isLoading ? "Сохранение..." : "Сохранить"}
              </button>
            </div>
          </form>

          <div
            style={{
              marginTop: "2rem",
              paddingTop: "1rem",
              borderTop: "1px solid #2d2d2d",
            }}
          >
            <button
              type="button"
              className="btn"
              onClick={handleDelete}
              disabled={isLoading}
              style={{
                background: "#e53e3e",
                color: "white",
                width: "100%",
              }}
            >
              {isLoading ? "Удаление..." : "Удалить чат"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatSettingsModal;
