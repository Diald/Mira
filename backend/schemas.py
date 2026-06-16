from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(SignupRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr


class NotebookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    persona: str = ""
    color: str = "#6366f1"


class NotebookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    persona: str | None = None
    color: str | None = None


class NotebookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    persona: str
    color: str
    created_at: datetime
    note_count: int = 0
    last_active_at: datetime | None = None


class NotebookDetail(NotebookOut):
    recent_note_titles: list[str] = []


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    created_at: datetime


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    content: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    content: str | None = None
    is_pinned: bool | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notebook_id: UUID
    session_id: UUID | None
    title: str
    content: str
    is_auto: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime


class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notebook_id: UUID
    content: str
    source_type: str | None
    created_at: datetime
