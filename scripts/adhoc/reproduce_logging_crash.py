
import logging
import sys

# Define a formatter that expects 'category'
formatter = logging.Formatter('%(levelname)s [%(category)s] %(message)s')

# Create a handler with this formatter
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

# Create a standard logger (like the one in GPU utils)
logger = logging.getLogger("standard_logger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

print("--- Attempting invalid log ---")
try:
    # This simulates logger_instance.info(...) which doesn't have 'category'
    logger.info("This should crash because category is missing")
except ValueError as e:
    print(f"Caught expected error: {e}")
except Exception as e:
    print(f"Caught unexpected error: {e}")

print("\n--- Applying Fix ---")
# Define the filter
class CategoryFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'category'):
            record.category = 'SYSTEM'
        return True

# Add filter to handler
handler.addFilter(CategoryFilter())

print("--- Attempting valid log ---")
try:
    logger.info("This should work now")
except Exception as e:
    print(f"Still failed: {e}")
