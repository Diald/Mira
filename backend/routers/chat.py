import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_owned_notebook
from backend.models.message import Message
from backend.models.note import Note
from backend.models.notebook import Notebook
from backend.models.session import ChatSession
from backend.schemas import ChatRequest, MessageOut
from backend.services.llm import gemini_client
from backend.services.memory import format_memories, format_message_history, format_note_titles, retrieve_memories
from backend.workers.tasks import summarize_session

router = APIRouter(prefix="/chat", tags=["chat"])


async def _active_session(db: AsyncSession, notebook_id: UUID) -> ChatSession:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.notebook_id == notebook_id, ChatSession.is_summarized.is_(False))
        .order_by(desc(ChatSession.started_at))
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if session is None:
        session = ChatSession(notebook_id=notebook_id)
        db.add(session)
        await db.commit()
        await db.refresh(session)
    return session


async def _build_prompt(db: AsyncSession, notebook: Notebook, user_message: str, session: ChatSession) -> tuple[str, list[dict], int]:
    last_messages = (
        await db.execute(
            select(Message).where(Message.session_id == session.id).order_by(desc(Message.created_at)).limit(20)
        )
    ).scalars().all()
    last_messages = list(reversed(last_messages))
    memories = await retrieve_memories(db, notebook.id, user_message, top_k=3)
    note_titles = (
        await db.execute(
            select(Note.title).where(Note.notebook_id == notebook.id, Note.is_auto.is_(True)).order_by(desc(Note.created_at)).limit(2)
        )
    ).scalars().all()
    system_prompt = f"""
You are a helpful AI assistant for the notebook: "{notebook.name}".
{notebook.persona}

[LONG-TERM MEMORY - from past sessions]
{format_memories(memories)}

[RECENT AUTO-NOTES]
{format_note_titles(list(note_titles))}
""".strip()
    messages = [*format_message_history(last_messages), {"role": "user", "content": user_message}]
    return system_prompt, messages, len(memories)


@router.post("/{notebook_id}")
async def chat(
    payload: ChatRequest,
    notebook: Notebook = Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    session = await _active_session(db, notebook.id)
    system_prompt, messages, memories_used = await _build_prompt(db, notebook, payload.message, session)

    async def generate():
        assistant_response = ""
        try:
            yield f"data: {json.dumps({'meta': {'memories_used': memories_used}})}\n\n"
            async for text in gemini_client.stream(system_prompt, messages, max_tokens=2048):
                assistant_response += text
                yield f"data: {json.dumps({'text': text})}\n\n"
            db.add(Message(session_id=session.id, role="user", content=payload.message))
            db.add(Message(session_id=session.id, role="assistant", content=assistant_response))
            session.ended_at = datetime.now(UTC)
            await db.commit()
            message_count = await db.scalar(select(func.count(Message.id)).where(Message.session_id == session.id))
            if message_count and message_count % 10 == 0:
                summarize_session.delay(str(session.id))
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            raise

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{notebook_id}/history", response_model=list[MessageOut])
async def history(
    notebook: Notebook = Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> list[MessageOut]:
    result = await db.execute(
        select(Message)
        .join(ChatSession)
        .where(ChatSession.notebook_id == notebook.id)
        .order_by(desc(Message.created_at))
        .limit(50)
    )
    return list(reversed(result.scalars().all()))


@router.post("/{notebook_id}/end-session")
async def end_session(
    notebook: Notebook = Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    session = await _active_session(db, notebook.id)
    session.ended_at = datetime.now(UTC)
    await db.commit()
    summarize_session.delay(str(session.id))
    return {"status": "queued"}
