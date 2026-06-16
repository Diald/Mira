from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user, get_owned_notebook
from backend.models.memory_entry import MemoryEntry
from backend.models.user import User
from backend.schemas import MemoryOut
from backend.services.vector_store import vector_store

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{notebook_id}", response_model=list[MemoryOut])
async def list_memory(
    notebook=Depends(get_owned_notebook),
    db: AsyncSession = Depends(get_db),
) -> list[MemoryEntry]:
    result = await db.execute(
        select(MemoryEntry).where(MemoryEntry.notebook_id == notebook.id).order_by(desc(MemoryEntry.created_at))
    )
    return list(result.scalars().all())


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    memory = await db.get(MemoryEntry, memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    await get_owned_notebook(memory.notebook_id, current_user, db)
    if memory.qdrant_id:
        await vector_store.delete_point(memory.notebook_id, memory.qdrant_id)
    await db.delete(memory)
    await db.commit()
