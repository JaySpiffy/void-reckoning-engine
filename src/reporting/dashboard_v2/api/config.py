from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):    # API Setup
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Context
    # Try to load from active configuration, fallback to environment or default
    from src.core.config import get_active_universe
    _active = get_active_universe()
    
    UNIVERSE: str = _active if _active else "void_reckoning"
    RUN_ID: str = "run_1"
    # DB_PATH is now dynamic, resolved by dependencies or service
    # DB_PATH: str = "reports/campaign_data.db"
    
    # Static Files for Health Checks
    STATIC_FOLDER: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../reporting/static"))
    
    LOG_LEVEL: str = "INFO"
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    WEBSOCKET_PING_TIMEOUT: int = 60
    WEBSOCKET_PING_INTERVAL: int = 25
    EVENT_BATCH_SIZE: int = 50
    METRICS_UPDATE_INTERVAL: float = 2.0

    class Config:
        env_file = ".env"
        env_prefix = "DASHBOARD_"
        case_sensitive = False

    def validate_config(self):
        """Validate configuration integrity."""
        if self.PORT < 1024 and self.PORT != 80:
            # Simple validation example
            pass
        return True

settings = Settings()
settings.validate_config()
