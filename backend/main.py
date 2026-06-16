from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routers import auth, chat, memory, notebooks, notes

settings = get_settings()

app = FastAPI(title="NotebookLLM", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(notebooks.router)
app.include_router(chat.router)
app.include_router(notes.router)
app.include_router(memory.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
