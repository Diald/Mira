import MemoryBadge from "./MemoryBadge.jsx";

export default function MessageBubble({ message }) {
  const isAssistant = message.role === "assistant";
  return (
    <div className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}>
      <div className={`max-w-[78%] rounded px-3 py-2 text-sm leading-6 ${isAssistant ? "border border-slate-200 bg-white" : "bg-slate-900 text-white"}`}>
        <div className="whitespace-pre-wrap">{message.content}</div>
        {isAssistant ? <div className="mt-2"><MemoryBadge count={message.memoriesUsed} /></div> : null}
      </div>
    </div>
  );
}
