import uvicorn
import logging
import argparse
from src.reporting.dashboard_v2.api.main import app
from src.reporting.dashboard_v2.api.config import settings
from src.reporting.dashboard_v2.api.dependencies import set_global_context

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI Dashboard Server")
    parser.add_argument("--universe", type=str, help="Universe name")
    parser.add_argument("--run-id", type=str, help="Run ID")
    parser.add_argument("--host", type=str, default=settings.HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Store context globally so dependencies.py can pick it up
    # Note: Dependencies need a way to know these args.
    # We'll use a simple global set function in dependencies.
    if args.universe:
        set_global_context(args.universe, args.run_id)

    logger.info(f"Starting Dashboard API on {args.host}:{args.port}")
    if args.universe:
        logger.info(f"Targeting Universe: {args.universe}, Run ID: {args.run_id or 'latest'}")

    uvicorn.run(
        "src.reporting.dashboard_v2.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
