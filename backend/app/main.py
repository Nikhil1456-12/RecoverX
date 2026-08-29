from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RecoverX...")
    logger.info(f"Demo mode: {settings.is_demo_mode}")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down RecoverX...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "recoverx", "demo_mode": settings.is_demo_mode}

@app.get("/ready")
async def ready():
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    return {"status": "ok", "version": settings.VERSION}

# Import and include routers
from app.api.dashboard import router as dashboard_router
from app.api.transactions import router as transactions_router
from app.api.experiments import router as experiments_router
from app.api.audit import router as audit_router
from app.api.webhooks import router as webhooks_router
from app.api.ml_api import router as ml_router
from app.api.admin import router as admin_router
from app.api.recovery_actions import router as recovery_actions_router

app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["transactions"])
app.include_router(experiments_router, prefix="/api/experiments", tags=["experiments"])
app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(ml_router, prefix="/api/ml", tags=["ml"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(recovery_actions_router, prefix="/api/recovery-actions", tags=["recovery-actions"])

# Revenue leakage uses dashboard leakage endpoint
from app.api.dashboard import router as leakage_alias_router
app.include_router(leakage_alias_router, prefix="/api/revenue-leakage", tags=["revenue-leakage"])

# Serve frontend build if available
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
assets_dir = os.path.join(frontend_dist, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
        return {"error": "Not Found"}
    file_path = os.path.join(frontend_dist, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "healthy", "service": "RecoverX Backend API", "frontend": "dist not built"}

