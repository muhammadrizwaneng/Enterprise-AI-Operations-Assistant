"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.chat import router as chat_router
from app.api.db_browser import router as db_browser_router
from app.api.rag import router as rag_router
from app.api.routes import router
from app.api.search import router as search_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import init_db

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure ORM tables exist (including new chat tables) on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Local-first Enterprise AI Operations Assistant. "
        "Phase 1: LLM chat. Phase 2: embeddings ingestion. "
        "Phase 3: semantic search. Phase 4: RAG grounded answers."
    ),
    version="0.4.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(db_browser_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(rag_router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    """Root welcome endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "db_browser": "/db",
        "chat": "/api/v1/chat",
        "semantic_search": "/api/v1/search/semantic",
        "rag_ask": "/api/v1/rag/ask",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/admin/db", include_in_schema=False)
def admin_db_redirect() -> RedirectResponse:
    """Convenience alias for the database browser."""
    return RedirectResponse(url="/db")
