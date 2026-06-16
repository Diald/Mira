import { Send, Square } from "lucide-react";
import MessageBubble from "./MessageBubble.jsx";

export default function ChatWindow({ messages, input, setInput, onSend, busy }) {
  return (
    <section className="flex min-h-0 flex-1 flex-col border-x border-slate-200 bg-[#f6f7f9]">
      <div className="scrollbar-thin flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((message) => <MessageBubble key={message.localId || message.id} message={message} />)}
      </div>
      <form onSubmit={onSend} className="border-t border-slate-200 bg-white p-3">
        <div className="flex gap-2">
          <textarea value={input} onChange={(event) => setInput(event.target.value)} rows={2} className="min-h-12 flex-1 resize-none rounded border border-slate-300 px-3 py-2 outline-none focus:border-emerald-600" placeholder="Ask this notebook..." />
          <button disabled={busy || !input.trim()} className="grid h-12 w-12 place-items-center rounded bg-emerald-600 text-white disabled:opacity-50" title={busy ? "Streaming" : "Send"}>
            {busy ? <Square size={18} /> : <Send size={18} />}
          </button>
        </div>
      </form>
    </section>
  );
}
