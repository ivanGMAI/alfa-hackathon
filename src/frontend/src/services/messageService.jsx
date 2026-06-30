import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export const messageService = {
  async sendMessage(messageData) {
    const response = await api.post("/messages/send", messageData);
    return response.data;
  },

  /**
   * Stream the agent's tool steps and answer via Server-Sent Events.
   * Calls `onEvent(eventName, data)` for each event: "user_message", "step",
   * "token", "done". Returns when the stream closes.
   */
  async streamMessage(messageData, onEvent) {
    const response = await fetch(`${API_BASE_URL}/messages/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(messageData),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? ""; // keep the last partial frame

      for (const frame of frames) {
        if (!frame.trim()) continue;

        let eventName = "message";
        const dataLines = [];
        for (const line of frame.split("\n")) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        }

        if (dataLines.length === 0) continue;
        try {
          onEvent(eventName, JSON.parse(dataLines.join("\n")));
        } catch {
          // ignore malformed frame
        }
      }
    }
  },

  /**
   * Render `content` to a DOCX or PDF file on the backend and trigger a download.
   * `format` is "docx" | "pdf". `title`/`filename` are optional (used for the
   * file name and document heading).
   */
  async exportDocument({ format, content, title, filename }) {
    const response = await fetch(`${API_BASE_URL}/documents/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ format, content, title, filename }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename || title || "document"}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  /**
   * Upload a PDF to a chat for RAG grounding. Returns {filename, pages, chunks}.
   * Throws an Error with the backend message on failure (e.g. non-PDF, a scan).
   */
  async uploadDocument(chatId, file) {
    const form = new FormData();
    form.append("chat_id", String(chatId));
    form.append("file", file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: "POST",
      credentials: "include",
      body: form,
    });

    if (!response.ok) {
      let detail = `Upload failed: ${response.status}`;
      try {
        const body = await response.json();
        if (body?.detail) detail = body.detail;
      } catch {
        // keep the generic message
      }
      throw new Error(detail);
    }
    return response.json();
  },

  /** List documents attached to a chat: [{filename, chunks}]. */
  async listDocuments(chatId) {
    const response = await api.get("/documents", { params: { chat_id: chatId } });
    return response.data;
  },
};
