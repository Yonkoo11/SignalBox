import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import config
from app.database import init_db
from app.routers import auth, feedback, settings, billing, sentiment
from app.tasks.scheduler import start_scheduler, stop_scheduler
from app.services.telegram_bot import start_bot, stop_bot

# Static files path
STATIC_DIR = Path(__file__).parent / "static"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    start_scheduler()
    await start_bot()
    yield
    # Shutdown
    await stop_bot()
    stop_scheduler()


app = FastAPI(
    title="SignalBox",
    description="Catch feedback that matters",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(feedback.router)
app.include_router(settings.router)
app.include_router(billing.router)
app.include_router(sentiment.router)

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serve landing page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dashboard")
async def dashboard():
    """Serve sentiment oracle dashboard."""
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/health")
async def health():
    return {"status": "healthy"}
