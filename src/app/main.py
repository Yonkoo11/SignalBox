import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("true", "1")
STATIC_DIR = Path(__file__).parent / "static"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if DEMO_MODE:
        logger.info("Running in DEMO MODE")
        # Start social collector (uses Reddit public JSON, no API key needed)
        _scheduler = None
        try:
            import asyncio
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from app.services.social_collector import collect_all_projects

            logger.info("Starting live social collector (Reddit public JSON)")
            _scheduler = AsyncIOScheduler()
            _scheduler.add_job(
                collect_all_projects,
                trigger=IntervalTrigger(minutes=5),
                id="social_collector",
                replace_existing=True,
            )
            _scheduler.start()
            # Run initial collection
            asyncio.create_task(collect_all_projects())
        except Exception as e:
            logger.warning(f"Social collector init failed: {e}")
        yield
        if _scheduler:
            _scheduler.shutdown()
        return

    # Production mode: initialize all services
    from app.database import init_db
    from app.tasks.scheduler import start_scheduler, stop_scheduler
    from app.services.telegram_bot import start_bot, stop_bot
    from app.config import config

    await init_db()
    if config.X_BOT_BEARER_TOKEN:
        start_scheduler()
    else:
        logger.info("Scheduler disabled: X API not configured")
    await start_bot()
    yield
    await stop_bot()
    if config.X_BOT_BEARER_TOKEN:
        stop_scheduler()


app = FastAPI(
    title="SignalBox",
    description="Catch feedback that matters",
    version="0.1.0",
    lifespan=lifespan,
)

secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
app.add_middleware(SessionMiddleware, secret_key=secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if DEMO_MODE:
    from app.routers.demo import router as demo_router
    app.include_router(demo_router)
    logger.info("Demo router mounted")
else:
    from app.config import config
    from app.routers import auth, feedback, settings, billing, sentiment
    app.include_router(auth.router)
    app.include_router(feedback.router)
    app.include_router(settings.router)
    app.include_router(billing.router)
    app.include_router(sentiment.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dashboard")
async def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "demo" if DEMO_MODE else "production"}
