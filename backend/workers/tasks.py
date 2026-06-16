import asyncio

from celery import Celery
from sqlalchemy import select

from backend.config import get_settings
from backend.database import AsyncSessionLocal
from backend.models.memory_entry import MemoryEntry
from backend.models.message import Message
from backend.models.note import Note
from backend.models.session import ChatSession
from backend.services.llm import gemini_client
from backend.services.summarizer import AUTO_NOTE_PROMPT, SUMMARIZE_PROMPT, note_title
from backend.services.vector_store import vector_store

settings = get_settings()
celery_app = Celery("notebookllm", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="tasks.summarize_session")
def summarize_session(session_id: str) -> None:
    asyncio.run(_summarize_session(session_id))


async def _summarize_session(session_id: str) -> None:
    async with AsyncSessionLocal() as db:
        session = await db.get(ChatSession, session_id)
        if session is None or session.is_summarized:
            return

        result = await db.execute(select(Message).where(Message.session_id == session.id).order_by(Message.created_at))
        messages = result.scalars().all()
        if not messages:
            return

        transcript = "\n".join(f"{message.role}: {message.content}" for message in messages)
        summary_data = await gemini_client.complete_json(SUMMARIZE_PROMPT, transcript)
        summary = summary_data.get("summary", "")
        facts = summary_data.get("facts", [])[:5]

        session.summary = summary
        for fact in facts:
            memory = MemoryEntry(notebook_id=session.notebook_id, content=fact, source_type="extracted_fact")
            db.add(memory)
            await db.flush()
            memory.qdrant_id = await vector_store.upsert_memory(session.notebook_id, fact, memory.id)

        note_markdown = await gemini_client.complete(AUTO_NOTE_PROMPT, [{"role": "user", "content": summary}], max_tokens=1024)
        db.add(
            Note(
                notebook_id=session.notebook_id,
                session_id=session.id,
                title=note_title(note_markdown),
                content=note_markdown,
                is_auto=True,
            )
        )
        session.is_summarized = True
        await db.commit()
