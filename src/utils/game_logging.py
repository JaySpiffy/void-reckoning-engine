import os
import logging
import logging.handlers
import json
import threading
import time
from typing import Optional, Dict, Any
from enum import Enum
from src.reporting.telemetry import EventCategory

class LogCategory(Enum):
    SYSTEM = "SYSTEM"
    CAMPAIGN = "CAMPAIGN"
    COMBAT = "COMBAT"
    ECONOMY = "ECONOMY"
    DIPLOMACY = "DIPLOMACY"
    AI = "AI"
    ERROR = "ERROR"
    ENVIRONMENT = "ENVIRONMENT"
    DEBUG = "DEBUG"
    # New Phase 6 Categories
    INTELLIGENCE = "INTELLIGENCE"
    MISSION = "MISSION"
    RESEARCH = "RESEARCH"
    STRATEGY = "STRATEGY"
    PORTAL = "PORTAL"
    OPTIMIZATION = "OPTIMIZATION"
    HERO = "HERO"

class LogContext:
    """Thread-local storage for correlation IDs."""
    _local = threading.local()

    @classmethod
    def get(cls) -> Dict[str, Any]:
        if not hasattr(cls._local, 'context'):
            cls._local.context = {
                "run_id": None,
                "turn": None,
                "faction": None,
                "battle_id": None
            }
        return cls._local.context

    @classmethod
    def update(cls, **kwargs):
        ctx = cls.get()
        ctx.update(kwargs)

    @classmethod
    def clear(cls):
        cls._local.context = {
            "run_id": None,
            "turn": None,
            "faction": None,
            "battle_id": None
        }

class JSONFormatter(logging.Formatter):
    def format(self, record):
        ctx = getattr(record, "context", {})
        
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "category": getattr(record, "category", "SYSTEM"),
            "message": record.getMessage(),
            "run_id": ctx.get("run_id"),
            "turn": ctx.get("turn"),
            "faction": ctx.get("faction"),
            "battle_id": ctx.get("battle_id"),
            "context": ctx,
            "performance": getattr(record, "performance", None)
        }
        # Filter None values BUT preserve correlation IDs for stable formatting
        required_keys = {"run_id", "turn", "faction", "battle_id"}
        return json.dumps({k: v for k, v in log_record.items() if v is not None or k in required_keys})

class AlertLogHandler(logging.Handler):
    """Bridge between standard logging and AlertManager."""
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            try:
                from src.reporting.alert_manager import AlertManager
                am = AlertManager()
                context = getattr(record, "context", {})
                am.process_log_event(record.levelno, record.getMessage(), context)
            except ImportError:
                pass
            except Exception:
                pass

class CategoryFilter(logging.Filter):
    """
    Ensures that log records have a 'category' attribute.
    This is required because we attached our custom formatter (which uses %(category)s)
    to the Root Logger, but standard module loggers don't provide this attribute.
    """
    def filter(self, record):
        if not hasattr(record, 'category'):
            record.category = 'SYSTEM'
        return True

class GameLogger:
    """
    Centralized logger for the Warhammer 40k Campaign Simulator.
    Supports structured JSON logging, rotation, and correlation IDs.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GameLogger, cls).__new__(cls)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Clears the singleton instance and resets initialization flag. FOR TESTING ONLY."""
        if cls._instance:
             cls._instance._initialized = False
        cls._instance = None

    def __init__(self, log_dir: str = "logs", console_verbose: bool = True, use_file_logging: bool = True):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.log_dir = log_dir
        self.console_verbose = console_verbose
        self.use_file_logging = use_file_logging
        self.context = LogContext
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        self.logger = logging.getLogger("CampaignLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # 1. Handlers
        if self.use_file_logging:
            # Text Log Handler (Rotating)
            text_path = os.path.join(log_dir, "campaign.log")
            rh = logging.handlers.RotatingFileHandler(
                text_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
            )
            rh.setLevel(logging.DEBUG)
            rh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(category)s] %(message)s', datefmt='%H:%M:%S'))
            rh.addFilter(CategoryFilter())
            self.logger.addHandler(rh)
            
            # JSON Log Handler (Rotating)
            json_path = os.path.join(log_dir, "campaign.json")
            jh = logging.handlers.RotatingFileHandler(
                json_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
            )
            jh.setLevel(logging.DEBUG)
            jh.setFormatter(JSONFormatter(datefmt='%Y-%m-%dT%H:%M:%S'))
            self.logger.addHandler(jh)
        else:
            rh = None
            jh = None

        # 2. Alert Handler
        ah = AlertLogHandler()
        ah.setLevel(logging.ERROR)
        self.logger.addHandler(ah)
        
        # 3. Error Patterns
        self.error_patterns = {}
        
        self._initialized = True
        if self.use_file_logging:
            self.log(LogCategory.SYSTEM, f"Logger initialized. Writing to {text_path}")
        else:
            self.log(LogCategory.SYSTEM, "Logger initialized (Console only mode)")
        
        # 4. Configure Root Logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        if not root_logger.handlers:
             if rh: root_logger.addHandler(rh)
             if jh: root_logger.addHandler(jh)
             root_logger.addHandler(ah)
             
             if self.console_verbose:
                 ch = logging.StreamHandler()
                 ch.setLevel(logging.INFO)
                 ch.setFormatter(logging.Formatter('%(message)s'))
                 root_logger.addHandler(ch)

    def set_context(self, **kwargs):
        self.context.update(**kwargs)

    def log(self, category: LogCategory, message: str, print_to_console: bool = True, level: int = logging.INFO, **kwargs) -> None:
        """
        Logs a message to file and optionally prints it to the console.
        """
        # Merge kwargs into context for this record ONLY
        current_ctx = self.context.get().copy()
        if kwargs:
            current_ctx.update(kwargs)

        extra = {
            "category": category.value,
            "context": current_ctx
        }

        self.logger.log(level, message, extra=extra)

        # Track Error Patterns
        if level >= logging.ERROR:
            # Simplify message for grouping (first 50 chars or before first colon)
            pattern = message.split(':')[0] if ':' in message else message[:50]
            self.error_patterns[pattern] = self.error_patterns.get(pattern, 0) + 1
        
        # Console Output
        if self.console_verbose and print_to_console:
            prefix_map = {
                LogCategory.SYSTEM: "",
                LogCategory.CAMPAIGN: "  > [CAMPAIGN]",
                LogCategory.COMBAT: "  > [COMBAT]",
                LogCategory.ECONOMY: "  > [ECONOMY]",
                LogCategory.DIPLOMACY: "  > [DIPLOMACY]",
                LogCategory.AI: "  > [AI]",
                LogCategory.ERROR: "  !!! [ERROR]",
                LogCategory.ENVIRONMENT: "  > [ENVIRONMENT]",
                LogCategory.DEBUG: "  [DEBUG]",
                # New Phase 6 Prefixes
                LogCategory.INTELLIGENCE: "  > [INTEL]",
                LogCategory.MISSION: "  > [MISSION]",
                LogCategory.RESEARCH: "  > [RESEARCH]",
                LogCategory.STRATEGY: "  > [STRATEGY]",
                LogCategory.PORTAL: "  > [PORTAL]",
                LogCategory.OPTIMIZATION: "  > [OPTIMIZE]",
                LogCategory.HERO: "  > [HERO]"
            }
            prefix = prefix_map.get(category, f"  > [{category.value}]")
            print(f"{prefix} {message}")

    def log_performance(self, operation: str, duration_ms: float, memory_mb: Optional[float] = None):
        perf_data = {"operation": operation, "duration_ms": duration_ms}
        if memory_mb: perf_data["memory_mb"] = memory_mb
        
        self.logger.info(
            f"PERF: {operation} took {duration_ms:.2f}ms", 
            extra={
                "category": "PERFORMANCE",
                "context": self.context.get(),
                "performance": perf_data
            }
        )
    
    def log_error_telemetry(self, engine):
        """Logs recurring error patterns to telemetry (Metric #11)."""
        if not engine or not hasattr(engine, 'telemetry') or not engine.telemetry:
            return
            
        if not self.error_patterns:
            return
            
        # Top 5 error patterns
        sorted_errors = sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
        total_errors = sum(self.error_patterns.values())
        
        engine.telemetry.log_event(
            EventCategory.SYSTEM,
            "error_pattern",
            {
                "total_errors": total_errors,
                "top_patterns": [
                    {"pattern": p, "count": c, "frequency": round(c / total_errors, 3) if total_errors > 0 else 0}
                    for p, c in sorted_errors
                ],
                "turn": getattr(engine, 'turn_counter', 0)
            },
            turn=getattr(engine, 'turn_counter', 0)
        )

    # Shorthand Helpers
    def info(self, message: str, **kwargs) -> None: self.log(LogCategory.SYSTEM, message, **kwargs)
    def system(self, message: str, **kwargs) -> None: self.log(LogCategory.SYSTEM, message, **kwargs)
    def campaign(self, message: str, **kwargs) -> None: self.log(LogCategory.CAMPAIGN, message, **kwargs)
    def combat(self, message: str, **kwargs) -> None: self.log(LogCategory.COMBAT, message, **kwargs)
    def economy(self, message: str, **kwargs) -> None: self.log(LogCategory.ECONOMY, message, **kwargs)
    def diplomacy(self, message: str, **kwargs) -> None: self.log(LogCategory.DIPLOMACY, message, **kwargs)
    def ai(self, message: str, **kwargs) -> None: self.log(LogCategory.AI, message, **kwargs)
    def environment(self, message: str, **kwargs) -> None: self.log(LogCategory.ENVIRONMENT, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None: 
        self.log(LogCategory.ERROR, message, level=logging.ERROR, **kwargs)
        
    def warning(self, message: str, **kwargs) -> None:
        self.log(LogCategory.SYSTEM, message, level=logging.WARNING, **kwargs)

    def debug(self, message: str, print_to_console: bool = False, **kwargs) -> None:
        self.log(LogCategory.DEBUG, message, print_to_console=print_to_console, level=logging.DEBUG, **kwargs)

    # Phase 6 Helpers
    def intelligence(self, message: str, **kwargs) -> None: self.log(LogCategory.INTELLIGENCE, message, **kwargs)
    def mission(self, message: str, **kwargs) -> None: self.log(LogCategory.MISSION, message, **kwargs)
    def research(self, message: str, **kwargs) -> None: self.log(LogCategory.RESEARCH, message, **kwargs)
    def strategy(self, message: str, **kwargs) -> None: self.log(LogCategory.STRATEGY, message, **kwargs)
    def portal(self, message: str, **kwargs) -> None: self.log(LogCategory.PORTAL, message, **kwargs)
    def optimization(self, message: str, **kwargs) -> None: self.log(LogCategory.OPTIMIZATION, message, **kwargs)
    def hero(self, message: str, **kwargs) -> None: self.log(LogCategory.HERO, message, **kwargs)
