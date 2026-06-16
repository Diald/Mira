import axios from "axios";

export const tokenStore = {
  get: () => localStorage.getItem("notebookllm_token"),
  set: (token) => localStorage.setItem("notebookllm_token", token),
  clear: () => localStorage.removeItem("notebookllm_token")
};

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || ""
});

const apiBaseUrl = import.meta.env.VITE_API_URL || "";

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function streamChat(notebookId, message, onEvent) {
  const response = await fetch(`${apiBaseUrl}/chat/${notebookId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${tokenStore.get()}`
    },
    body: JSON.stringify({ message })
  });
  if (!response.ok || !response.body) {
    throw new Error("Chat request failed");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const event of events) {
      const line = event.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      const data = line.slice(6);
      if (data === "[DONE]") return;
      onEvent(JSON.parse(data));
    }
  }
}
