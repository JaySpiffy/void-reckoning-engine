import sys
import os

print("Starting verification...", flush=True)

try:
    print("Importing utils...", flush=True)
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from src.utils.unit_parser import load_all_units
    print("Utils imported.", flush=True)
    
    print("Loading Config...", flush=True)
    from src.core.config import get_universe_config
    print("Config Loaded.", flush=True)

except Exception as e:
    print(f"Error: {e}", flush=True)
