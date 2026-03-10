import logging
import os
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db
from config import settings
from services.scanner import run_scan
from routers import markets, opportunities, bets, settings_router, signals

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _load_secrets_from_db():
    """Load API keys persisted in DB into the runtime secrets store."""
    from database import AsyncSessionLocal
    from models import AppSecret
    import config
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(AppSecret))
        for row in result.scalars().all():
            config._secrets[row.key] = row.value
    logger.info(f"Loaded {len(config._secrets)} secret(s) from DB")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")
    await _load_secrets_from_db()

    # Schedule periodic scan
    scheduler.add_job(
        run_scan,
        "interval",
        minutes=settings.scan_interval_minutes,
        id="market_scan",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — scanning every {settings.scan_interval_minutes} min")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Polymarket AI Trader",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-App-Password"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    pwd = settings.app_password
    # Only protect /api/* routes; skip /api/health (used by Railway healthcheck)
    if pwd and request.url.path.startswith("/api/") and request.url.path != "/api/health":
        provided = request.headers.get("X-App-Password", "")
        if provided != pwd:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

# API routes
app.include_router(markets.router)
app.include_router(opportunities.router)
app.include_router(bets.router)
app.include_router(settings_router.router)
app.include_router(signals.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "auto_bet_enabled": settings.auto_bet_enabled,
        "scan_interval_minutes": settings.scan_interval_minutes,
    }


# Serve React frontend (after build)
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
