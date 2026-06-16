from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user, get_owned_notebook
from backend.models.note import Note
from backend.models.notebook import Notebook
from backend.models.session import ChatSession
from backend.models.user import User
from backend.schemas import NotebookCreate, NotebookDetail, NotebookOut, NotebookUpdate

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


async def _decorate_notebook(db: AsyncSession, notebook: Notebook) -> NotebookOut:
    note_count = await db.scalar(select(func.count(Note.id)).where(Note.notebook_id == notebook.id))
    last_active_at = await db.scalar(
        select(func.max(ChatSession.ended_at)).where(ChatSession.notebook_id == notebook.id)
    )
    return NotebookOut.model_validate(notebook).model_copy(
        update={"note_count": note_count or 0, "last_active_at": last_active_at}
    )


@router.get("", response_model=list[NotebookOut])
async def list_notebooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotebookOut]:
    result = await db.execute(select(Notebook).where(Notebook.user_id == current_user.id).order_by(desc(Notebook.created_at)))
    return [await _decorate_notebook(db, notebook) for notebook in result.scalars().all()]


@router.post("", response_model=NotebookOut, status_code=status.HTTP_201_CREATED)
async def create_notebook(
    payload: NotebookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotebookOut:
    notebook = Notebook(user_id=current_user.id, name=payload.name, persona=payload.persona, color=payload.color)
    db.add(notebook)
    await db.commit()
    await db.refresh(notebook)
    return await _decorate_notebook(db, notebook)


@router.get("/{notebook_id}", response_model=NotebookDetail)
async def get_notebook(
    notebook: Notebook = Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> NotebookDetail:
    recent_titles = (
        await db.execute(
            select(Note.title).where(Note.notebook_id == notebook.id).order_by(desc(Note.created_at)).limit(2)
        )
    ).scalars().all()
    base = await _decorate_notebook(db, notebook)
    return NotebookDetail(**base.model_dump(), recent_note_titles=list(recent_titles))


@router.put("/{notebook_id}", response_model=NotebookOut)
async def update_notebook(
    payload: NotebookUpdate,
    notebook: Notebook = Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> NotebookOut:
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None:
            setattr(notebook, key, value)
    await db.commit()
    await db.refresh(notebook)
    return await _decorate_notebook(db, notebook)


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notebook(
    notebook: Notebook = Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.delete(notebook)
    await db.commit()
