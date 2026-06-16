from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.memory_entry import MemoryEntry
from backend.services.vector_store import vector_store


async def retrieve_memories(db: AsyncSession, notebook_id: UUID, query: str, top_k: int = 3) -> list[MemoryEntry]:
    hits = await vector_store.search(notebook_id, query, top_k=top_k)
    memory_ids = [hit.get("payload", {}).get("memory_id") for hit in hits if hit.get("payload", {}).get("memory_id")]
    if not memory_ids:
        return []
    result = await db.execute(
        select(MemoryEntry).where(MemoryEntry.notebook_id == notebook_id, MemoryEntry.id.in_(memory_ids))
    )
    by_id = {str(memory.id): memory for memory in result.scalars().all()}
    return [by_id[memory_id] for memory_id in memory_ids if memory_id in by_id]


def format_memories(memories: list[MemoryEntry]) -> str:
    if not memories:
        return "No relevant long-term memories found."
    return "\n".join(f"- {memory.content}" for memory in memories)


def format_note_titles(titles: list[str]) -> str:
    if not titles:
        return "No recent auto-notes yet."
    return "\n".join(f"- {title}" for title in titles)


def format_message_history(messages) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]
