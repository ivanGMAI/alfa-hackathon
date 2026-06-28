import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export const chatService = {
  async createChat(chatData) {
    const response = await api.post("/chats/", chatData);
    return response.data;
  },

  async getChatById(chatId) {
    const response = await api.get(`/chats/${chatId}/`);
    return response.data;
  },

  async updateChat(chatId, chatData) {
    const response = await api.patch(`/chats/${chatId}/`, chatData);
    return response.data;
  },

  async deleteChat(chatId) {
    await api.delete(`/chats/${chatId}/`);
  },
};
