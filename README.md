# NotebookLLM

NotebookLLM is a conversation-first AI assistant where each notebook has isolated chat history, memory, and auto-generated notes.

## Stack

- Backend: FastAPI, async SQLAlchemy, Alembic
- LLM: Gemini via the official `google-genai` SDK
- Embeddings: OpenAI `text-embedding-3-small` to match the required 1536-dimensional Qdrant vectors
- Vector DB: Qdrant
- Jobs: Celery and Redis
- Frontend: React, Vite, TailwindCSS
- Auth: Supabase Auth JWTs

## Setup

1. Copy environment values.

   ```bash
   cp .env.example .env
   ```

2. Start infrastructure.

   ```bash
   docker compose up -d
   ```

3. Install backend dependencies.

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Run migrations.

   ```bash
   alembic -c backend/alembic.ini upgrade head
   ```

5. Start the backend.

   ```bash
   uvicorn backend.main:app --reload
   ```

6. Start the worker in another terminal.

   ```bash
   celery -A backend.workers.tasks.celery_app worker --loglevel=info
   ```

7. Install and run the frontend.

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

The app runs at `http://localhost:5173`; the API runs at `http://localhost:8000`.

## API Summary

- `POST /auth/signup`
- `POST /auth/login`
- `GET|POST /notebooks`
- `GET|PUT|DELETE /notebooks/{id}`
- `POST /chat/{notebook_id}` streams SSE chunks
- `GET /chat/{notebook_id}/history`
- `POST /chat/{notebook_id}/end-session`
- `GET|POST /notes/{notebook_id}`
- `PUT|DELETE /notes/{note_id}`
- `GET /memory/{notebook_id}`
- `DELETE /memory/{memory_id}`

## Notes

All notebook-scoped queries verify notebook ownership. Summarization tasks are idempotent via `chat_sessions.is_summarized`, and Qdrant collection names are sanitized per notebook.
