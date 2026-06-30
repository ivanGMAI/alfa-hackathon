import React, { createContext, useState, useContext, useEffect } from "react";
import { chatService } from "../services/chatService";
import { messageService } from "../services/messageService";

const ChatContext = createContext();

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

// Функция для нормализации сообщений при загрузке из localStorage
const normalizeMessages = (chats) => {
  return chats.map((chat) => {
    if (chat.messages) {
      chat.messages = chat.messages.map((message) => ({
        ...message,
        // Убеждаемся, что created_at существует
        created_at: message.created_at || new Date().toISOString(),
      }));
    }
    return chat;
  });
};

export const ChatProvider = ({ children }) => {
  const [chats, setChats] = useState(() => {
    const savedChats = localStorage.getItem("chats");
    if (savedChats) {
      try {
        const parsedChats = JSON.parse(savedChats);
        return normalizeMessages(parsedChats);
      } catch (error) {
        console.error("Error parsing chats from localStorage:", error);
        return [];
      }
    }
    return [];
  });

  const [currentChat, setCurrentChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  // Documents (PDF) attached to the current chat for RAG grounding.
  const [chatDocuments, setChatDocuments] = useState([]);
  const [isUploadingDocument, setIsUploadingDocument] = useState(false);

  // Сохраняем чаты в localStorage при изменении
  useEffect(() => {
    localStorage.setItem("chats", JSON.stringify(chats));
  }, [chats]);

  // Восстанавливаем текущий чат при загрузке
  useEffect(() => {
    if (chats.length > 0 && !currentChat) {
      const lastChat = chats[0];
      setCurrentChat(lastChat);
      setMessages(lastChat.messages || []);
    }
  }, [chats, currentChat]);

  // Загружаем список прикреплённых документов при смене активного чата
  useEffect(() => {
    const chatId = currentChat?.id;
    if (!chatId) {
      setChatDocuments([]);
      return;
    }
    let cancelled = false;
    messageService
      .listDocuments(chatId)
      .then((docs) => {
        if (!cancelled) setChatDocuments(docs || []);
      })
      .catch(() => {
        if (!cancelled) setChatDocuments([]);
      });
    return () => {
      cancelled = true;
    };
  }, [currentChat?.id]);

  const createNewChat = async (chatData = {}) => {
    try {
      setIsLoading(true);
      const newChat = await chatService.createChat({
        title: "Новый чат",
        ...chatData,
      });

      console.log("✅ New chat created:", newChat);

      // Сразу устанавливаем новый чат как текущий
      setCurrentChat(newChat);
      setMessages(newChat.messages || []);

      // Добавляем в список чатов
      setChats((prev) => [newChat, ...prev]);

      return newChat;
    } catch (error) {
      console.error("❌ Failed to create chat:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const loadChatById = async (chatId) => {
    try {
      setIsLoadingChat(true);
      console.log("🔄 Loading chat:", chatId);

      const chatData = await chatService.getChatById(chatId);

      // Убедимся, что у всех сообщений есть created_at
      if (chatData.messages) {
        chatData.messages = chatData.messages.map((message) => ({
          ...message,
          created_at: message.created_at || new Date().toISOString(),
        }));
      }

      console.log("✅ Chat data loaded:", chatData);

      setCurrentChat(chatData);
      setMessages(chatData.messages || []);

      // Обновляем чат в списке
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === chatId ? { ...chat, ...chatData } : chat,
        ),
      );

      return chatData;
    } catch (error) {
      console.error(`❌ Failed to load chat ${chatId}:`, error);
      throw error;
    } finally {
      setIsLoadingChat(false);
    }
  };

  const selectChat = async (chat) => {
    try {
      console.log(
        "🖱️ Selecting chat:",
        chat.id,
        "Current chat:",
        currentChat?.id,
      );

      if (currentChat?.id === chat.id) {
        console.log("⚡ Same chat, skipping");
        return;
      }

      await loadChatById(chat.id);
      console.log("✅ Chat selected successfully");
    } catch (error) {
      console.error("❌ Failed to select chat:", error);
      // При ошибке все равно переключаемся на базовые данные
      setCurrentChat(chat);
      setMessages([]);
      console.log("🔄 Fallback: using basic chat data");
    }
  };

  const sendMessage = async (content) => {
    if (!currentChat || !content.trim()) {
      return;
    }

    const text = content.trim();
    const stamp = Date.now();
    const userId = `temp-user-${stamp}`;
    const aiId = `temp-ai-${stamp}`;

    // Обновляет растущее сообщение ассистента по его временному id.
    const updateAi = (updater) =>
      setMessages((prev) =>
        prev.map((msg) => (msg.id === aiId ? updater(msg) : msg)),
      );

    try {
      setIsSendingMessage(true);

      // Временное сообщение пользователя + плейсхолдер ассистента,
      // который будет наполняться токенами по мере стриминга.
      setMessages((prev) => [
        ...prev,
        {
          id: userId,
          content: text,
          sender: "user",
          created_at: new Date().toISOString(),
          isTemp: true,
        },
        {
          id: aiId,
          content: "",
          sender: "ai",
          created_at: new Date().toISOString(),
          isTemp: true,
          steps: [],
          sources: null,
        },
      ]);

      await messageService.streamMessage(
        { chat_id: currentChat.id, content: text },
        (event, data) => {
          if (event === "user_message") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === userId
                  ? {
                      ...msg,
                      id: data.id ?? msg.id,
                      content: data.content ?? msg.content,
                      created_at: data.created_at ?? msg.created_at,
                      isTemp: false,
                    }
                  : msg,
              ),
            );
          } else if (event === "sources") {
            updateAi((msg) => ({ ...msg, sources: data }));
          } else if (event === "step") {
            updateAi((msg) => ({ ...msg, steps: [...(msg.steps || []), data] }));
          } else if (event === "token") {
            updateAi((msg) => ({ ...msg, content: msg.content + (data.delta || "") }));
          } else if (event === "done") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiId
                  ? {
                      ...msg,
                      id: data.id ?? msg.id,
                      content: data.content ?? msg.content,
                      created_at: data.created_at ?? msg.created_at,
                      steps: data.steps?.length ? data.steps : msg.steps || null,
                      sources: data.sources?.length
                        ? data.sources
                        : msg.sources || null,
                      isTemp: false,
                    }
                  : msg,
              ),
            );
          }
        },
      );

      console.log("✅ Message streamed successfully");

      // Обновляем последнее сообщение в чате
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === currentChat.id
            ? {
                ...chat,
                last_message: text,
                updated_at: new Date().toISOString(),
              }
            : chat,
        ),
      );
    } catch (error) {
      console.error("❌ Failed to send message:", error);

      // Удаляем временные сообщения и показываем ошибку
      setMessages((prev) => [
        ...prev.filter((msg) => msg.id !== userId && msg.id !== aiId),
        {
          id: `error-${Date.now()}`,
          content: "Ошибка при отправке сообщения. Попробуйте еще раз.",
          sender: "system",
          created_at: new Date().toISOString(),
          isError: true,
        },
      ]);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const updateChat = async (chatId, chatData) => {
    try {
      console.log("🔄 Updating chat:", chatId, chatData);

      const updatedChat = await chatService.updateChat(chatId, chatData);

      // Обновляем чат в списке
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === chatId ? { ...chat, ...updatedChat } : chat,
        ),
      );

      // Если это текущий чат, обновляем его тоже
      if (currentChat?.id === chatId) {
        setCurrentChat((prev) => ({ ...prev, ...updatedChat }));
      }

      console.log("✅ Chat updated successfully");
      return updatedChat;
    } catch (error) {
      console.error("❌ Failed to update chat:", error);
      throw error;
    }
  };

  const deleteChat = async (chatId) => {
    try {
      console.log("🗑️ Deleting chat:", chatId);

      await chatService.deleteChat(chatId);

      // Удаляем чат из списка
      setChats((prev) => prev.filter((chat) => chat.id !== chatId));

      // Если удаляем текущий чат, очищаем текущий чат
      if (currentChat?.id === chatId) {
        setCurrentChat(null);
        setMessages([]);
      }

      console.log("✅ Chat deleted successfully");
    } catch (error) {
      console.error("❌ Failed to delete chat:", error);
      throw error;
    }
  };

  const addMessage = (message) => {
    setMessages((prev) => [...prev, message]);

    if (currentChat) {
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === currentChat.id
            ? {
                ...chat,
                last_message: message.content,
                messages: [...(chat.messages || []), message],
              }
            : chat,
        ),
      );
    }
  };

  const refreshChats = async () => {
    console.log("🔄 Refresh chats - not implemented");
    // Здесь можно добавить логику для загрузки всех чатов с сервера,
    // когда появится соответствующий endpoint
  };

  const clearCurrentChat = () => {
    setCurrentChat(null);
    setMessages([]);
  };

  const uploadDocument = async (file) => {
    if (!currentChat || !file) return;

    try {
      setIsUploadingDocument(true);
      const summary = await messageService.uploadDocument(currentChat.id, file);

      // Refresh the attached-documents list (dedupe by filename).
      setChatDocuments((prev) => {
        const others = prev.filter((doc) => doc.filename !== summary.filename);
        return [
          ...others,
          { filename: summary.filename, chunks: summary.chunks },
        ].sort((a, b) => a.filename.localeCompare(b.filename));
      });

      // Confirmation message in the chat thread.
      setMessages((prev) => [
        ...prev,
        {
          id: `doc-${Date.now()}`,
          content: `📄 Документ «${summary.filename}» загружен (${summary.pages} стр., ${summary.chunks} фрагм.). Теперь можно задавать вопросы по нему.`,
          sender: "system",
          created_at: new Date().toISOString(),
        },
      ]);

      return summary;
    } catch (error) {
      console.error("❌ Failed to upload document:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: `doc-error-${Date.now()}`,
          content: `Не удалось загрузить документ: ${error.message}`,
          sender: "system",
          created_at: new Date().toISOString(),
          isError: true,
        },
      ]);
    } finally {
      setIsUploadingDocument(false);
    }
  };

  const value = {
    // State
    chats,
    currentChat,
    messages,
    isLoading,
    isLoadingChat,
    isSendingMessage,
    chatDocuments,
    isUploadingDocument,

    // Chat actions
    createNewChat,
    selectChat,
    loadChatById,
    updateChat,
    deleteChat,
    refreshChats,
    clearCurrentChat,

    // Message actions
    sendMessage,
    addMessage,
    uploadDocument,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
