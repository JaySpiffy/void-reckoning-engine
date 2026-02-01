
import logging
import sys
# Import actual GameLogger
from src.utils.logging import GameLogger, LogCategory

# initialize
gl = GameLogger(log_dir="test_logs")

# Standard logger test
std_logger = logging.getLogger("StandardModuleLogger")
std_logger.setLevel(logging.INFO)

print("--- Attempting standard log through Root Logger ---")
try:
    # This should now work because Root Logger has handlers with CategoryFilter
    std_logger.info("This is a standard log message")
    print("Success: Standard log processed.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

print("--- Attempting GameLogger log ---")
try:
    gl.info("This is a GameLogger message")
    print("Success: GameLogger log processed.")
except Exception as e:
    print(f"FAILED: {e}")
