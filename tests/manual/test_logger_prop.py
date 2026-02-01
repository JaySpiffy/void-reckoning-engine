
import logging
import sys
# Configure Root Logger EXACTLY as the app does
from src.utils.game_logging import GameLogger

gl = GameLogger(log_dir="test_logs_debug")

# Get the logger that combat_phases uses
logger = logging.getLogger("src.combat.combat_phases")

print(f"Logger Name: {logger.name}")
print(f"Logger Level: {logger.level}")
print(f"Logger Effective Level: {logger.getEffectiveLevel()}")
print(f"Logger Propagate: {logger.propagate}")
print(f"Root Logger Handlers: {logging.getLogger().handlers}")

# Try to log
logger.info("TEST LOG - INFO - Should appear")
logger.warning("TEST LOG - WARNING - Should appear")
