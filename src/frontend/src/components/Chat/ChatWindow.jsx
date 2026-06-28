import React, { useState, useRef, useEffect } from "react";
import { useChat } from "../../contexts/ChatContext";
import MarkdownRenderer from "../MarkdownRenderer";

const ChatWindow = () => {
  const { currentChat, messages, isSendingMessage, sendMessage } = useChat();
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!inputValue.trim() || isSendingMessage || !currentChat) {
      return;
    }

    await sendMessage(inputValue);
    setInputValue("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (createdAt) => {
    if (!createdAt) return "";

    try {
      const date = new Date(createdAt);

      if (isNaN(date.getTime())) {
        return "";
      }

      return date.toLocaleTimeString("ru-RU", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (error) {
      return "";
    }
  };

  if (!currentChat) {
    return (
      <div className="chat-window">
        <div className="no-chat-selected">
          <h2>Выберите чат или создайте новый</h2>
          <p>Начните общение с нейросетью</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      {/* Заголовок чата */}
      <div className="chat-header">
        <div className="chat-title">
          <h2>{currentChat.title || `Чат ${currentChat.id}`}</h2>
          {currentChat.created_at && (
            <span className="chat-date">
              Создан:{" "}
              {new Date(currentChat.created_at).toLocaleDateString("ru-RU")}
            </span>
          )}
        </div>
      </div>

      {/* Область сообщений */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-icon">💬</div>
            <h3>Начните диалог</h3>
            <p>Задайте вопрос нейросети чтобы начать общение</p>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.sender} ${message.isError ? "error" : ""}`}
              >
                <div className="message-avatar">
                  {message.sender === "user"
                    ? "👤"
                    : message.sender === "ai"
                      ? "🤖"
                      : "⚡"}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {message.sender === "ai" && !message.isTemp ? (
                      <MarkdownRenderer content={message.content} />
                    ) : (
                      <>
                        {message.content}
                        {message.isTemp && (
                          <span className="typing-indicator">
                            <span>.</span>
                            <span>.</span>
                            <span>.</span>
                          </span>
                        )}
                      </>
                    )}
                  </div>
                  {message.steps && message.steps.length > 0 && (
                    <div className="agent-steps">
                      {message.steps.map((step, idx) => (
                        <details key={idx} className="agent-step">
                          <summary>🔧 {step.tool}</summary>
                          <pre className="agent-step-body">
                            {JSON.stringify(step.arguments, null, 2)}
                            {"\n→ "}
                            {step.result}
                          </pre>
                        </details>
                      ))}
                    </div>
                  )}
                  {message.sources && message.sources.length > 0 && (
                    <div className="agent-sources">
                      <span className="agent-sources-label">📚 Источники:</span>
                      {message.sources.map((src, idx) => (
                        <span key={idx} className="agent-source">
                          [{idx + 1}] {src.title}
                        </span>
                      ))}
                    </div>
                  )}
                  {message.created_at && (
                    <div className="message-time">
                      {formatTime(message.created_at)}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Форма ввода */}
      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <div className="input-wrapper">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите ваше сообщение..."
              disabled={isSendingMessage}
              rows="1"
              className="message-input"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isSendingMessage}
              className="send-button"
            >
              {isSendingMessage ? (
                <div className="spinner"></div>
              ) : (
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              )}
            </button>
          </div>
          <div className="input-hint">
            Нажмите Enter для отправки, Shift+Enter для новой строки
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatWindow;
