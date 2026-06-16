import { Home, Plus } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

export default function NotebookSidebar({ notebooks }) {
  const navigate = useNavigate();
  const { id } = useParams();
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white md:block">
      <div className="flex items-center justify-between border-b border-slate-200 p-3">
        <button onClick={() => navigate("/")} className="grid h-9 w-9 place-items-center rounded border border-slate-300" title="Home"><Home size={17} /></button>
        <button onClick={() => navigate("/")} className="grid h-9 w-9 place-items-center rounded bg-slate-900 text-white" title="New notebook"><Plus size={17} /></button>
      </div>
      <nav className="space-y-1 p-3">
        {notebooks.map((notebook) => (
          <button key={notebook.id} onClick={() => navigate(`/notebook/${notebook.id}`)} className={`flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm ${notebook.id === id ? "bg-slate-100 font-medium" : "hover:bg-slate-50"}`}>
            <span className="h-3 w-3 rounded-full" style={{ backgroundColor: notebook.color }} />
            <span className="truncate">{notebook.name}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
