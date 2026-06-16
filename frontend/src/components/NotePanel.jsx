import { Pin, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

export default function NotePanel({ notes, memories, activeTab, setActiveTab, onCreateNote, onUpdateNote, onDeleteNote, onDeleteMemory }) {
  const [draft, setDraft] = useState({ title: "", content: "" });
  return (
    <aside className="flex w-full flex-col border-l border-slate-200 bg-white lg:w-80">
      <div className="grid grid-cols-2 border-b border-slate-200 p-2">
        <button onClick={() => setActiveTab("notes")} className={`rounded px-3 py-2 text-sm ${activeTab === "notes" ? "bg-slate-900 text-white" : "text-slate-600"}`}>Notes</button>
        <button onClick={() => setActiveTab("memory")} className={`rounded px-3 py-2 text-sm ${activeTab === "memory" ? "bg-slate-900 text-white" : "text-slate-600"}`}>Memory</button>
      </div>
      <div className="scrollbar-thin flex-1 overflow-y-auto p-3">
        {activeTab === "notes" ? (
          <div className="space-y-3">
            <form onSubmit={(event) => { event.preventDefault(); onCreateNote(draft); setDraft({ title: "", content: "" }); }} className="rounded border border-slate-200 p-3">
              <input className="mb-2 w-full rounded border border-slate-300 px-2 py-1.5 text-sm" placeholder="Title" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} required />
              <textarea className="mb-2 min-h-20 w-full rounded border border-slate-300 px-2 py-1.5 text-sm" placeholder="Markdown note" value={draft.content} onChange={(event) => setDraft({ ...draft, content: event.target.value })} required />
              <button className="flex items-center gap-1 rounded bg-emerald-600 px-2 py-1.5 text-sm font-medium text-white"><Plus size={14} /> Add</button>
            </form>
            {notes.map((note) => (
              <article key={note.id} className="rounded border border-slate-200 p-3">
                <div className="mb-2 flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold">{note.title}</h3>
                  <div className="flex gap-1">
                    <button onClick={() => onUpdateNote(note.id, { is_pinned: !note.is_pinned })} className="grid h-7 w-7 place-items-center rounded border border-slate-200" title="Pin"><Pin size={14} /></button>
                    <button onClick={() => onDeleteNote(note.id)} className="grid h-7 w-7 place-items-center rounded border border-slate-200 text-red-600" title="Delete"><Trash2 size={14} /></button>
                  </div>
                </div>
                <p className="whitespace-pre-wrap text-sm text-slate-600">{note.content}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {memories.map((memory) => (
              <article key={memory.id} className="flex gap-2 rounded border border-slate-200 p-3 text-sm">
                <p className="flex-1 text-slate-700">{memory.content}</p>
                <button onClick={() => onDeleteMemory(memory.id)} className="grid h-7 w-7 shrink-0 place-items-center rounded border border-slate-200 text-red-600" title="Delete"><Trash2 size={14} /></button>
              </article>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
