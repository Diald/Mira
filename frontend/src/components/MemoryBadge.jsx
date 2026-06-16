import { Sparkles } from "lucide-react";

export default function MemoryBadge({ count }) {
  if (!count) return null;
  return (
    <span className="inline-flex items-center gap-1 rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-800">
      <Sparkles size={12} />
      {count} memories used
    </span>
  );
}
