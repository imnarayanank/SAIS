"""
main.py
--------
FastAPI application entry point.
- Serves the React frontend from ../frontend/dist (or next to the .exe)
- Registers all API routers
- Creates database tables on startup
- Opens the browser automatically when run as a .exe
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys

from app.core.config import settings
from app.core.database import create_tables
from app.api import auth, courses, timetable, tasks, dashboard, academic, notes, planner


def get_base_dir():
    """Return the correct base directory whether running as script or .exe."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()

# Look for the frontend dist folder in the repository first.
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
if not os.path.isdir(FRONTEND_DIST):
    FRONTEND_DIST = os.path.join(BASE_DIR, "..", "frontend", "dist")
if not os.path.isdir(FRONTEND_DIST):
    # When packaged as .exe, dist is placed next to the exe.
    FRONTEND_DIST = os.path.join(BASE_DIR, "dist")

# Lifespan context manager (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app):
    """Create all database tables on startup."""
    create_tables()
    print(f"\n[OK] {settings.APP_NAME} v{settings.APP_VERSION} is running!")
    print(f"  -> Open:     http://localhost:8000")
    print(f"  -> API Docs: http://localhost:8000/docs\n")
    yield

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal academic management platform for college students.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow all origins so the hosted version and local version both work
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(timetable.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)
app.include_router(academic.router)
app.include_router(notes.router)
app.include_router(planner.router)

# Serve uploaded files statically
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/health")
def health():
    return {"status": "healthy"}


# Serve React frontend — catch-all so client-side routing works
if os.path.isdir(FRONTEND_DIST):
    # Static assets (JS, CSS, icons, etc.)
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    icons_dir = os.path.join(FRONTEND_DIST, "icons")
    if os.path.isdir(icons_dir):
        app.mount("/icons", StaticFiles(directory=icons_dir), name="icons")

    @app.get("/sw.js")
    def sw():
        return FileResponse(os.path.join(FRONTEND_DIST, "sw.js"))

    @app.get("/manifest.json")
    def manifest():
        return FileResponse(os.path.join(FRONTEND_DIST, "manifest.json"))

    # SPA catch-all — return index.html for every non-API route
    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        index = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index)


if __name__ == "__main__":
    import uvicorn
    import threading
    import webbrowser
    import time

    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
