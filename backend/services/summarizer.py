import re

AUTO_NOTE_PROMPT = """
Based on this conversation summary, write a structured markdown note.
Include: a clear title, key points as bullet lists, and any action items.
Keep it concise - max 300 words.
Return only the markdown, no preamble.
"""

SUMMARIZE_PROMPT = """
Analyze this conversation and extract:
1. A 2-3 sentence summary of what was discussed
2. Key facts to remember (max 5 bullet points)
3. Any decisions made or action items

Return as JSON:
{
  "summary": "...",
  "facts": ["...", "..."],
  "action_items": ["..."]
}
"""


def note_title(markdown: str) -> str:
    first_line = next((line.strip() for line in markdown.splitlines() if line.strip()), "Session notes")
    return re.sub(r"^#+\s*", "", first_line)[:180] or "Session notes"
