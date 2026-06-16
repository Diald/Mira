You are building a full-stack AI chatbot application called **NotebookLLM** — a conversation-first AI assistant where users organize chats into isolated "notebooks" (e.g. Gym, Project 1, Project 2). Each notebook has its own memory, conversation history, and auto-generated notes.

Read this entire file before writing any code. Follow the architecture, stack, and sequencing exactly.

---

## What you are building

A web application where:
- Users sign up and create multiple named notebooks
- Each notebook is an isolated AI chat context with its own memory
- The AI remembers past sessions within each notebook via a two-tier memory system
- After every session, the system auto-generates structured notes
- Users can view, edit, and delete their notes and memories

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), Alembic |
| LLM | Gemini API — raw API only, no LangChain |
| Vector DB | Qdrant (local Docker instance) |
| Relational DB | PostgreSQL via asyncpg |
| Background jobs | Celery + Redis |
| Frontend | React (Vite), TailwindCSS |
| Auth | Supabase Auth (JWT-based) |
| File storage | Local filesystem (dev), S3-compatible (prod-ready abstraction) |

---

## Project structure

```
notebookllm/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # Settings from env vars
│   ├── database.py              # Async SQLAlchemy engine + session
│   ├── models/
│   │   ├── user.py
│   │   ├── notebook.py
│   │   ├── session.py
│   │   ├── message.py
│   │   └── note.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── notebooks.py
│   │   ├── chat.py
│   │   └── notes.py
│   ├── services/
│   │   ├── llm.py               # Gemini API wrapper
│   │   ├── memory.py            # Short + long-term memory logic
│   │   ├── summarizer.py        # Session summarization
│   │   └── vector_store.py      # Qdrant read/write
│   ├── workers/
│   │   └── tasks.py             # Celery tasks
│   └── alembic/                 # DB migrations
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Home.jsx         # Notebook list
│   │   │   └── Chat.jsx         # Chat + notes panel
│   │   ├── components/
│   │   │   ├── NotebookSidebar.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── NotePanel.jsx
│   │   │   └── MemoryBadge.jsx  # Shows retrieved memories inline
│   │   └── api/
│   │       └── client.js        # Axios instance
│   └── vite.config.js
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Database schema

Create these tables via SQLAlchemy models and Alembic migrations.

### users
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
email       TEXT UNIQUE NOT NULL
created_at  TIMESTAMPTZ DEFAULT now()
```

### notebooks
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID REFERENCES users(id) ON DELETE CASCADE
name        TEXT NOT NULL
persona     TEXT DEFAULT ''          -- custom system prompt addendum
color       TEXT DEFAULT '#6366f1'   -- UI accent color
created_at  TIMESTAMPTZ DEFAULT now()
```

### chat_sessions
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
notebook_id     UUID REFERENCES notebooks(id) ON DELETE CASCADE
started_at      TIMESTAMPTZ DEFAULT now()
ended_at        TIMESTAMPTZ
summary         TEXT          -- populated after session ends
is_summarized   BOOLEAN DEFAULT false
```

### messages
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id  UUID REFERENCES chat_sessions(id) ON DELETE CASCADE
role        TEXT CHECK (role IN ('user', 'assistant'))
content     TEXT NOT NULL
created_at  TIMESTAMPTZ DEFAULT now()
```

### notes
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
notebook_id     UUID REFERENCES notebooks(id) ON DELETE CASCADE
session_id      UUID REFERENCES chat_sessions(id)
title           TEXT NOT NULL
content         TEXT NOT NULL       -- markdown
is_auto         BOOLEAN DEFAULT true
is_pinned       BOOLEAN DEFAULT false
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

### memory_entries
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
notebook_id     UUID REFERENCES notebooks(id) ON DELETE CASCADE
content         TEXT NOT NULL       -- compressed fact or summary
source_type     TEXT                -- 'session_summary' | 'extracted_fact'
qdrant_id       TEXT                -- corresponding vector ID in Qdrant
created_at      TIMESTAMPTZ DEFAULT now()
```

---

## Core logic: how the chat endpoint works

Every message to `POST /chat/{notebook_id}` must follow this exact flow:

### 1. Load context
```python
# a. Get the active session (create one if none exists)
# b. Load the last 20 messages from this session (short-term buffer)
# c. Retrieve top-3 semantically relevant memory_entries from Qdrant
#    using the user's current message as the query
```

### 2. Build the prompt
```python
system_prompt = f"""
You are a helpful AI assistant for the notebook: "{notebook.name}".
{notebook.persona}

[LONG-TERM MEMORY — from past sessions]
{format_memories(retrieved_memories)}

[RECENT AUTO-NOTES]
{format_note_titles(last_2_notes)}
""".strip()

messages = [
    *format_message_history(last_20_messages),
    {"role": "user", "content": user_message}
]
```

### 3. Call the LLM
```python
# Use the latest Gemini Python SDK
# Stream the response back to the client via SSE (Server-Sent Events)
# Model: best gemini model
# max_tokens: 2048
```

### 4. Persist
```python
# Save the user message and assistant response to the messages table
# Update session.ended_at to now() on every message (rolling window)
```

### 5. Trigger background job
```python
# After every 10 messages in a session, enqueue a Celery task:
# tasks.summarize_session.delay(session_id)
# Also enqueue on explicit session end
```

---

## Memory pipeline (Celery task)

This runs asynchronously after sessions accumulate enough messages.

```python
# tasks.summarize_session(session_id)

# 1. Fetch all unsummarized messages for this session
# 2. Call Gemini with a summarization prompt:

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

# 3. Parse the JSON response
# 4. Store summary in chat_sessions.summary
# 5. For each fact, create a memory_entry row and upsert its embedding into Qdrant
# 6. Generate a note using the auto_note prompt (see below)
# 7. Mark session as is_summarized = true
```

### Auto-note generation prompt
```python
AUTO_NOTE_PROMPT = """
Based on this conversation summary, write a structured markdown note.
Include: a clear title, key points as bullet lists, and any action items.
Keep it concise — max 300 words.
Return only the markdown, no preamble.
"""
```

---

## Vector store (Qdrant)

### Collection setup
```python
# Collection name: f"notebook_{notebook_id}"  (one collection per notebook)
# Vector size: 1536 (use text-embedding-3-small from Gemini embeddings)
# Distance: Cosine
```

### On write (new memory entry)
```python
# Embed the memory content
# Upsert into the notebook's Qdrant collection
# Store the qdrant_id back in the memory_entries table
```

### On read (retrieving context)
```python
# Embed the current user message
# Search top_k=3 in the notebook's Qdrant collection
# Return the content of matching memory_entries
```

---

## API routes

### Auth
```
POST   /auth/signup          body: { email, password }
POST   /auth/login           body: { email, password }  → returns JWT
```

### Notebooks
```
GET    /notebooks            → list all notebooks for current user
POST   /notebooks            body: { name, persona?, color? }
GET    /notebooks/{id}       → notebook detail + recent note titles
PUT    /notebooks/{id}       body: { name?, persona?, color? }
DELETE /notebooks/{id}
```

### Chat
```
POST   /chat/{notebook_id}   body: { message }  → SSE stream of assistant response
GET    /chat/{notebook_id}/history   → last 50 messages across sessions
POST   /chat/{notebook_id}/end-session   → manually trigger summarization
```

### Notes
```
GET    /notes/{notebook_id}         → all notes, sorted by pinned then recent
POST   /notes/{notebook_id}         body: { title, content }  → manual note
PUT    /notes/{note_id}             body: { title?, content?, is_pinned? }
DELETE /notes/{note_id}
```

### Memory
```
GET    /memory/{notebook_id}        → list all memory entries
DELETE /memory/{memory_id}          → user can delete a specific memory
```

---

## Frontend pages

### `/` — Home (Notebook list)
- Grid of notebook cards (name, color accent, last active time, note count)
- "New Notebook" button opens a modal (name + optional persona)
- Clicking a card navigates to `/notebook/{id}`

### `/notebook/{id}` — Chat view
- Left sidebar: list of all notebooks (for switching)
- Center: chat window with streaming message display
- Right panel: tabbed between "Notes" and "Memory"
  - Notes tab: list of auto and manual notes, pinning, editing
  - Memory tab: list of memory entries with delete option
- Bottom: message input with send button
- Show a subtle badge on assistant messages when memories were retrieved (e.g. "2 memories used")

---

## Streaming (SSE)

The chat endpoint must stream the assistant response using Server-Sent Events.

### Backend (FastAPI)
```python
from fastapi.responses import StreamingResponse

async def stream_response(notebook_id, message, user):
    async def generate():
        async with gemini_client.messages.stream(...) as stream:
            async for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Frontend (React)
```javascript
const response = await fetch(`/chat/${notebookId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ message })
});

const reader = response.body.getReader();
// Read chunks and append to the current assistant message bubble
```

---

## Environment variables

```env
# LLM
GEMINI_API_KEY=

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/notebookllm

# Vector DB
QDRANT_URL=http://localhost:6333

# Redis / Celery
REDIS_URL=redis://localhost:6379

# Auth
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=

# Embeddings (for Qdrant)
OPENAI_API_KEY=        # used only for text-embedding-3-small

# App
SECRET_KEY=            # for signing internal tokens
ENVIRONMENT=development
```

---

## docker-compose.yml

Include services for:
- `postgres` (image: postgres:16)
- `redis` (image: redis:7-alpine)
- `qdrant` (image: qdrant/qdrant)

Do not containerize the backend or frontend for development — run them locally with `uvicorn` and `vite`.

---

## Build sequence

Build in this exact order. Do not proceed to the next step until the current one works end-to-end.

**Step 1 — Infrastructure**
- Set up docker-compose with Postgres, Redis, Qdrant
- Create FastAPI app skeleton with health check route
- Set up SQLAlchemy async engine and session dependency
- Create all models and run initial Alembic migration
- Verify DB tables exist

**Step 2 — Auth**
- Implement signup and login routes using Supabase Auth
- Add JWT middleware to FastAPI
- Test with curl: signup → login → get token → call protected route

**Step 3 — Notebooks CRUD**
- Implement all notebook routes
- Add notebook ownership check middleware (users can only access their own)
- Test creating, listing, updating, deleting notebooks

**Step 4 — Basic chat (no memory)**
- Implement the chat endpoint with short-term buffer only (last 20 messages)
- No streaming yet — return full response
- Persist messages to DB
- Test: send 5 messages in a notebook, verify history endpoint returns them

**Step 5 — Streaming**
- Convert chat endpoint to SSE streaming
- Update frontend to consume the stream and render progressively
- Test streaming works in the browser

**Step 6 — Session summarization**
- Set up Celery worker with Redis
- Implement `summarize_session` task
- Call it after every 10 messages (counter in session table) and on manual end
- Verify summaries appear in `chat_sessions.summary`

**Step 7 — Vector memory**
- Set up Qdrant collection creation (auto-create per notebook on first message)
- Implement embedding + upsert in the summarization task
- Implement retrieval at chat time
- Inject retrieved memories into the system prompt
- Test: have a conversation about a topic, end session, start new session, ask about same topic — verify the AI recalls it

**Step 8 — Auto-notes**
- Generate notes inside the summarization task
- Implement notes CRUD routes
- Add notes panel to the frontend

**Step 9 — Memory management UI**
- Add memory list route and UI panel
- Allow users to delete individual memory entries (delete from both Postgres and Qdrant)

**Step 10 — Polish**
- Add memory badge on assistant messages
- Add notebook color picker
- Add persona field in notebook settings
- Handle errors gracefully (LLM failures, Qdrant down, etc.)
- Write a README with setup instructions

---

## Key implementation rules

- **Never use LangChain or LlamaIndex.** Call the Gemini SDK directly.
- **All DB queries must be async.** Use `async with session` everywhere.
- **Notebook isolation is non-negotiable.** All queries must filter by `notebook_id` AND verify `notebook.user_id == current_user.id`.
- **Never expose raw DB IDs in error messages.**
- **Keep the LLM prompt under 6000 tokens.** Short-term buffer = last 20 messages max. If a session is very long, truncate from the oldest end.
- **Celery tasks must be idempotent.** Check `is_summarized` before running summarization.
- **Qdrant collection names** must be sanitized: `re.sub(r'[^a-z0-9_]', '_', f"notebook_{notebook_id}")`.
- **SSE connections** must close cleanly on client disconnect — use `asyncio.CancelledError` handling.

---

## Definition of done

The project is complete when:
1. A user can sign up, create 3 notebooks with different names
2. Chat in each notebook independently — the AI does not mix context between them
3. After chatting in a notebook and starting a new session, the AI recalls relevant facts from the previous session
4. Auto-notes appear after sessions
5. Users can delete memories and notes
6. The frontend streams responses smoothly with no flicker
7. All routes return proper 401s for unauthenticated requests and 403s for cross-user access attempts

---

## Additional Instructions 

1. always implement latest versions of each 