from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user, get_owned_notebook
from backend.models.note import Note
from backend.models.user import User
from backend.schemas import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/{notebook_id}", response_model=list[NoteOut])
async def list_notes(
    notebook=Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> list[Note]:
    result = await db.execute(
        select(Note).where(Note.notebook_id == notebook.id).order_by(desc(Note.is_pinned), desc(Note.created_at))
    )
    return list(result.scalars().all())


@router.post("/{notebook_id}", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    notebook=Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> Note:
    note = Note(notebook_id=notebook.id, title=payload.title, content=payload.content, is_auto=False)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def _owned_note(note_id: UUID, user: User, db: AsyncSession) -> Note:
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await get_owned_notebook(note.notebook_id, user, db)
    return note


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: UUID,
    payload: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Note:
    note = await _owned_note(note_id, current_user, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(note, key, value)
    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    note = await _owned_note(note_id, current_user, db)
    await db.delete(note)
    await db.commit()
