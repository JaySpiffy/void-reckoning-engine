import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import time
import asyncio

from src.reporting.dashboard_v2.api.config import settings
from src.reporting.dashboard_v2.api.middleware import RequestLoggingMiddleware
from src.reporting.dashboard_v2.api.routes import (
    status_router, 
    metrics_router,
    economic_router,
    military_router,
    industrial_router,
    galaxy_router,
    alerts_router,
    export_router,
    export_router,
    performance_router,
    diagnostics_router,
    analytics_router,
    research_router,
    control_router,
    runs_router
)
from src.reporting.dashboard_v2.api.websocket import websocket_endpoint, broadcast_metrics_loop, manager
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global Background Tasks
metrics_task = None

app = FastAPI(
    title="Campaign Dashboard API",
    description="Modernized FastAPI backend for the Multi-Universe Campaign Simulator Dashboard.",
    version="2.0.0"
)

# 1. Register Middleware (Order matters: Logging should wrap CORS)
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Register Routers
app.include_router(status_router)
app.include_router(metrics_router)
app.include_router(economic_router)
app.include_router(military_router)
app.include_router(industrial_router)
app.include_router(galaxy_router)
app.include_router(alerts_router)
app.include_router(export_router)
app.include_router(performance_router)
app.include_router(diagnostics_router)
app.include_router(analytics_router)
app.include_router(research_router)
app.include_router(control_router)
app.include_router(runs_router)

# 3. Register WebSocket Route
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    # Retrieve service via dependency manually for WS contexts
    try:
        service = await get_dashboard_service()
        await websocket_endpoint(websocket, service)
    except Exception as e:
        logger.error(f"WebSocket initialization failed: {e}")
        await websocket.close(code=1011)

from fastapi.staticfiles import StaticFiles
import os

# ... imports ...

@app.get("/api")
async def api_root():
    return {
        "message": "Campaign Dashboard API v2 is running",
        "version": "2.0.0",
        "status_url": "/api/status",
        "health_url": "/api/health",
        # ...
    }

# Mount Launcher UI (Shadow UI)
launcher_dir = "src/reporting/dashboard_v2/launcher_ui"
if os.path.exists(launcher_dir):
     app.mount("/launcher", StaticFiles(directory=launcher_dir, html=True), name="launcher")
     logger.info(f"Mounted Launcher UI at /launcher")

# Mount Static Files (Frontend)
# Try multiple paths for robustness (Docker vs Local)
frontend_paths = [
    "frontend/dist",           # Docker / Root execution
    "../frontend/dist",        # Running from src
    "../../frontend/dist"
]

frontend_root = None
for path in frontend_paths:
    if os.path.exists(path):
        frontend_root = path
        logger.info(f"Frontend static files found at: {path}")
        break

if frontend_root:
    # 1. Mount Assets specifically (usually where Vite puts JS/CSS)
    if os.path.exists(os.path.join(frontend_root, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_root, "assets")), name="assets")

    # 2. SPA Fallback: Serve index.html for unknown routes (excluding API)
    from fastapi.responses import FileResponse
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API routes to bubble up (handled by include_router above)
        # But wait, include_router is checked first by FastAPI order? 
        # Actually, FastAPI matches specific routes first. If this is a wildcard catch-all,
        # it should be defined LAST.
        # However, since we defined API routers EARLIER, they take precedence.
        
        # Check if file exists in root (e.g. favicon.ico, manifest.json)
        file_path = os.path.join(frontend_root, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
             return FileResponse(file_path)
        
        # Otherwise serve index.html for client-side routing
        # Disable caching for index.html to ensure new deployments are seen immediately
        return FileResponse(
            os.path.join(frontend_root, "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        
else:
    logger.warning("Frontend static files not found. Dashboard UI will not be served.")
    @app.get("/")
    async def root():
        return {
            "message": "Campaign Dashboard API v2 (Headless Mode)",
            "warning": "Frontend static files not found. Please build frontend or use Docker.",
            "api_docs": "/docs",
            "launcher": "/launcher/"
        }


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Dashboard API v2...")
    global metrics_task
    try:
        service = await get_dashboard_service()
        metrics_task = asyncio.create_task(broadcast_metrics_loop(service))
    except Exception as e:
        logger.warning(f"Could not start background metrics loop on startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Dashboard API v2...")
    if metrics_task:
        metrics_task.cancel()
    # Close all connections in manager
    for conn in list(manager.active_connections):
        await conn.close(code=1001)
