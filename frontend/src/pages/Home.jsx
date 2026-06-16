import { LogOut, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, tokenStore } from "../api/client.js";

export default function Home() {
  const navigate = useNavigate();
  const [notebooks, setNotebooks] = useState([]);
  const [form, setForm] = useState({ name: "", persona: "", color: "#10b981" });
  const [showModal, setShowModal] = useState(false);

  async function load() {
    const { data } = await api.get("/notebooks");
    setNotebooks(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function createNotebook(event) {
    event.preventDefault();
    const { data } = await api.post("/notebooks", form);
    setShowModal(false);
    setForm({ name: "", persona: "", color: "#10b981" });
    navigate(`/notebook/${data.id}`);
  }

  return (
    <main className="min-h-screen bg-[#f6f7f9] text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <h1 className="text-xl font-semibold">NotebookLLM</h1>
          <div className="flex gap-2">
            <button onClick={() => setShowModal(true)} className="flex items-center gap-2 rounded bg-emerald-600 px-3 py-2 text-sm font-medium text-white">
              <Plus size={17} /> New Notebook
            </button>
            <button onClick={() => { tokenStore.clear(); navigate("/login"); }} className="grid h-9 w-9 place-items-center rounded border border-slate-300 bg-white" title="Log out">
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </header>
      <section className="mx-auto max-w-6xl px-5 py-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {notebooks.map((notebook) => (
            <button key={notebook.id} onClick={() => navigate(`/notebook/${notebook.id}`)} className="min-h-36 rounded border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
              <span className="mb-4 block h-1.5 w-16 rounded" style={{ backgroundColor: notebook.color }} />
              <h2 className="text-lg font-semibold">{notebook.name}</h2>
              <p className="mt-2 line-clamp-2 text-sm text-slate-600">{notebook.persona || "General assistant notebook"}</p>
              <p className="mt-5 text-xs text-slate-500">{notebook.note_count} notes</p>
            </button>
          ))}
        </div>
      </section>
      {showModal ? (
        <div className="fixed inset-0 grid place-items-center bg-slate-900/35 p-4">
          <form onSubmit={createNotebook} className="w-full max-w-md rounded border border-slate-200 bg-white p-5 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold">New notebook</h2>
            <input className="mb-3 w-full rounded border border-slate-300 px-3 py-2" placeholder="Name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
            <textarea className="mb-3 min-h-24 w-full rounded border border-slate-300 px-3 py-2" placeholder="Persona prompt" value={form.persona} onChange={(event) => setForm({ ...form, persona: event.target.value })} />
            <input className="mb-4 h-10 w-16 rounded border border-slate-300 p-1" type="color" value={form.color} onChange={(event) => setForm({ ...form, color: event.target.value })} />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowModal(false)} className="rounded border border-slate-300 px-3 py-2">Cancel</button>
              <button className="rounded bg-emerald-600 px-3 py-2 font-medium text-white">Create</button>
            </div>
          </form>
        </div>
      ) : null}
    </main>
  );
}
