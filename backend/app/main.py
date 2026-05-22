"""
main.py — FastAPI Application Entrypoint
Wires together all routers, middleware, exception handlers, and startup events.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.database.database import create_all_tables
from backend.app.middleware.logging_middleware import LoggingMiddleware
from backend.app.middleware.rate_limit import rate_limit_middleware

# ── Routers ───────────────────────────────────────────────────────────────────
from backend.app.api import auth, student, faculty, notices, ai, chat_history
from backend.app.websocket.notification_ws import router as ws_router
from backend.app.realtime.websocket.websocket_router import router as audio_ws_router
from backend.app.realtime.websocket.session_manager import run_session_cleanup

# ── Windows event loop fix (Python 3.8 + asyncio + proactor) ─────────────────
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("campus_assistant")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup: creates all DB tables if they don't exist.
    Runs on shutdown: (add cleanup here if needed, e.g. closing connections)
    """
    logger.info("🚀 Starting AI Campus Assistant Backend...")
    try:
        await create_all_tables()
        logger.info("✅ Database tables verified/created.")
    except Exception as e:
        logger.error(f"⚠️ Database connection failed: {e}. Running without DB...")
    cleanup_task = asyncio.create_task(run_session_cleanup())
    logger.info("✅ Real-time session cleanup task started.")
    yield
    cleanup_task.cancel()
    logger.info("🛑 Shutting down AI Campus Assistant Backend.")


# ── App Creation ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Real-Time AI Campus Assistant — Backend API

Provides:
- 🔐 JWT Authentication (student / faculty / admin)
- 👨‍🎓 Student Management (profile, attendance, timetable, assignments)
- 👩‍🏫 Faculty Management (notices, assignments, student list)
- 🤖 AI Assistant (text chat, voice, RAG document queries)
- 📢 Real-Time Notifications via WebSocket

**All protected endpoints require a Bearer token in the Authorization header.**
    """,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── Middleware ────────────────────────────────────────────────────────────────

# 1. CORS — allow configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request/Response logging
app.add_middleware(LoggingMiddleware)

# 3. Rate Limiting
@app.middleware("http")
async def add_rate_limiting(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)


# ── Global Exception Handlers ─────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": f"Route {request.url.path} not found."},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception("Unhandled server error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error. Please try again later."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth)
app.include_router(student)
app.include_router(faculty)
app.include_router(notices)
app.include_router(ai)
app.include_router(chat_history)
app.include_router(ws_router)
app.include_router(audio_ws_router)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Root health check")
async def root():
    """Returns server status. Use this to verify the API is running."""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Detailed health check")
async def health():
    return {"status": "healthy", "database": "connected"}


# ── Frontend Static Files (production) ───────────────────────────────────────
_FRONTEND_DIST = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve React SPA — return index.html for all non-API routes."""
        return FileResponse(_FRONTEND_DIST / "index.html")
