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
};
