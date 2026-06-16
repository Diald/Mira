import { Settings } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, streamChat } from "../api/client.js";
import ChatWindow from "../components/ChatWindow.jsx";
import NotebookSidebar from "../components/NotebookSidebar.jsx";
import NotePanel from "../components/NotePanel.jsx";

export default function Chat() {
  const { id } = useParams();
  const [notebooks, setNotebooks] = useState([]);
  const [notebook, setNotebook] = useState(null);
  const [messages, setMessages] = useState([]);
  const [notes, setNotes] = useState([]);
  const [memories, setMemories] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [activeTab, setActiveTab] = useState("notes");

  async function loadNotebookShell() {
    const [{ data: list }, { data: detail }] = await Promise.all([api.get("/notebooks"), api.get(`/notebooks/${id}`)]);
    setNotebooks(list);
    setNotebook(detail);
  }

  async function loadPanels() {
    const [{ data: noteData }, { data: memoryData }] = await Promise.all([api.get(`/notes/${id}`), api.get(`/memory/${id}`)]);
    setNotes(noteData);
    setMemories(memoryData);
  }

  async function loadHistory() {
    const { data } = await api.get(`/chat/${id}/history`);
    setMessages(data);
  }

  useEffect(() => {
    loadNotebookShell();
    loadPanels();
    loadHistory();
  }, [id]);

  async function send(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    const userMessage = { localId: crypto.randomUUID(), role: "user", content: text };
    const assistantId = crypto.randomUUID();
    setMessages((current) => [...current, userMessage, { localId: assistantId, role: "assistant", content: "", memoriesUsed: 0 }]);
    try {
      await streamChat(id, text, (eventData) => {
        if (eventData.meta) {
          setMessages((current) => current.map((message) => message.localId === assistantId ? { ...message, memoriesUsed: eventData.meta.memories_used } : message));
        }
        if (eventData.text) {
          setMessages((current) => current.map((message) => message.localId === assistantId ? { ...message, content: message.content + eventData.text } : message));
        }
      });
      loadPanels();
    } finally {
      setBusy(false);
    }
  }

  async function createNote(payload) {
    await api.post(`/notes/${id}`, payload);
    loadPanels();
  }

  async function updateNote(noteId, payload) {
    await api.put(`/notes/${noteId}`, payload);
    loadPanels();
  }

  async function deleteNote(noteId) {
    await api.delete(`/notes/${noteId}`);
    loadPanels();
  }

  async function deleteMemory(memoryId) {
    await api.delete(`/memory/${memoryId}`);
    loadPanels();
  }

  async function endSession() {
    await api.post(`/chat/${id}/end-session`);
  }

  return (
    <main className="flex h-screen bg-[#f6f7f9] text-slate-900">
      <NotebookSidebar notebooks={notebooks} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4">
          <div className="min-w-0">
            <h1 className="truncate font-semibold">{notebook?.name || "Notebook"}</h1>
            <p className="truncate text-xs text-slate-500">{notebook?.persona || "General assistant"}</p>
          </div>
          <button onClick={endSession} className="flex items-center gap-2 rounded border border-slate-300 px-3 py-2 text-sm">
            <Settings size={16} /> End session
          </button>
        </header>
        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          <ChatWindow messages={messages} input={input} setInput={setInput} onSend={send} busy={busy} />
          <NotePanel
            notes={notes}
            memories={memories}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            onCreateNote={createNote}
            onUpdateNote={updateNote}
            onDeleteNote={deleteNote}
            onDeleteMemory={deleteMemory}
          />
        </div>
      </div>
    </main>
  );
}
