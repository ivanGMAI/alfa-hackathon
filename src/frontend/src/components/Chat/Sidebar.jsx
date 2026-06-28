import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { useChat } from "../../contexts/ChatContext";
import ChatSettingsModal from "./ChatSettingsModal";

const Sidebar = () => {
  const { user, logout } = useAuth();
  const { chats, currentChat, isLoading, createNewChat, selectChat } =
    useChat();

  const [settingsModal, setSettingsModal] = useState({
    isOpen: false,
    chat: null,
  });

  const handleNewChat = async () => {
    try {
      await createNewChat();
    } catch (error) {
      console.error("Failed to create new chat:", error);
    }
  };

  const handleChatSelect = (chat) => {
    selectChat(chat);
  };

  const handleSettingsClick = (chat, e) => {
    e.stopPropagation(); // Предотвращаем выбор чата
    setSettingsModal({
      isOpen: true,
      chat: chat,
    });
  };

  const closeSettingsModal = () => {
    setSettingsModal({
      isOpen: false,
      chat: null,
    });
  };

  const handleLogout = () => {
    logout();
  };

  const truncatePreview = (text, maxLength = 30) => {
    if (!text) return "Нет сообщений";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  const getChatPreview = (chat) => {
    if (chat.messages && chat.messages.length > 0) {
      const lastMessage = chat.messages[chat.messages.length - 1];
      return truncatePreview(lastMessage.content);
    }
    if (chat.last_message) {
      return truncatePreview(chat.last_message);
    }
    return "Начните общение...";
  };

  return (
    <>
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="user-info">
            <div className="user-info-main">
              <h3>{user?.name || "Пользователь"}</h3>
              <p className="user-email">{user?.email || "Email не указан"}</p>
            </div>
          </div>
        </div>

        <div className="sidebar-content">
          <button
            className="btn btn-primary full-width new-chat-btn"
            onClick={handleNewChat}
            disabled={isLoading}
          >
            {isLoading ? "Создание..." : "+ Новый чат"}
          </button>

          <div className="chat-history-section">
            <div className="section-header">
              <h4>Мои чаты</h4>
              <span className="chats-count">({chats.length})</span>
            </div>

            <div className="chat-history">
              {chats.length > 0 ? (
                chats.map((chat) => (
                  <div
                    key={chat.id}
                    className={`chat-item ${currentChat?.id === chat.id ? "active" : ""}`}
                    onClick={() => handleChatSelect(chat)}
                  >
                    <div className="chat-icon">💬</div>
                    <div className="chat-content">
                      <div className="chat-title">
                        {chat.title || `Чат ${chat.id}`}
                      </div>
                      <div className="chat-preview">{getChatPreview(chat)}</div>
                    </div>

                    {/* Кнопка настроек */}
                    <button
                      className="chat-settings-btn"
                      onClick={(e) => handleSettingsClick(chat, e)}
                      title="Настройки чата"
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
                      </svg>
                    </button>

                    {currentChat?.id === chat.id && (
                      <div className="active-indicator"></div>
                    )}
                  </div>
                ))
              ) : (
                <div className="no-chats">
                  <p>Нет чатов</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="sidebar-footer">
          <button
            className="btn btn-secondary full-width logout-btn"
            onClick={handleLogout}
          >
            Выйти
          </button>
        </div>
      </div>

      {/* Модальное окно настроек */}
      <ChatSettingsModal
        chat={settingsModal.chat}
        isOpen={settingsModal.isOpen}
        onClose={closeSettingsModal}
      />
    </>
  );
};

export default Sidebar;
