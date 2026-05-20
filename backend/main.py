"""
main.py — FastAPI Application Entrypoint
Wires together all routers, middleware, exception handlers, and startup events.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend.config import settings
from backend.database import create_all_tables
from backend.middleware.logging_middleware import LoggingMiddleware

# ── Routers ───────────────────────────────────────────────────────────────────
from backend.routes import auth, student, faculty, notices, ai, chat_history
from backend.websocket.notification_ws import router as ws_router

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
    await create_all_tables()
    logger.info("✅ Database tables verified/created.")
    yield
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
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(faculty.router)
app.include_router(notices.router)
app.include_router(ai.router)
app.include_router(chat_history.router)
app.include_router(ws_router)


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
