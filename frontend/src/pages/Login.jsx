import { Brain, LogIn, UserPlus } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, tokenStore } from "../api/client.js";

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post(`/auth/${mode}`, { email, password });
      tokenStore.set(data.access_token);
      navigate("/");
    } catch {
      setError("Authentication failed. Check your credentials and Supabase settings.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f6f7f9] text-slate-900">
      <div className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-5">
        <div className="mb-7 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded bg-emerald-600 text-white">
            <Brain size={22} />
          </span>
          <div>
            <h1 className="text-2xl font-semibold">NotebookLLM</h1>
            <p className="text-sm text-slate-600">Isolated memory for every project.</p>
          </div>
        </div>
        <form onSubmit={submit} className="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 grid grid-cols-2 rounded border border-slate-200 p-1">
            <button type="button" onClick={() => setMode("login")} className={`rounded px-3 py-2 text-sm ${mode === "login" ? "bg-slate-900 text-white" : "text-slate-600"}`}>
              Login
            </button>
            <button type="button" onClick={() => setMode("signup")} className={`rounded px-3 py-2 text-sm ${mode === "signup" ? "bg-slate-900 text-white" : "text-slate-600"}`}>
              Sign up
            </button>
          </div>
          <label className="mb-3 block text-sm font-medium">
            Email
            <input className="mt-1 w-full rounded border border-slate-300 px-3 py-2 outline-none focus:border-emerald-600" value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
          </label>
          <label className="mb-4 block text-sm font-medium">
            Password
            <input className="mt-1 w-full rounded border border-slate-300 px-3 py-2 outline-none focus:border-emerald-600" value={password} onChange={(event) => setPassword(event.target.value)} type="password" required minLength={6} />
          </label>
          {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
          <button disabled={busy} className="flex w-full items-center justify-center gap-2 rounded bg-emerald-600 px-4 py-2.5 font-medium text-white disabled:opacity-60">
            {mode === "login" ? <LogIn size={18} /> : <UserPlus size={18} />}
            {busy ? "Working..." : mode === "login" ? "Login" : "Create account"}
          </button>
        </form>
      </div>
    </main>
  );
}
