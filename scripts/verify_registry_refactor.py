
import os
import sys
import json

# Add source root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.registry_builder import build_all_registries
from src.core.config import UNIVERSE_ROOT

def verify():
    print("Starting Registry Verification...")
    universe_name = "eternal_crusade"
    universe_path = os.path.join(UNIVERSE_ROOT, universe_name)
    
    print(f"Target Universe: {universe_path}")
    
    try:
        build_all_registries(universe_name, verbose=True)
        print("Build completed without exception.")
    except Exception as e:
        print(f"Build FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return

    # Check Artifacts
    b_path = os.path.join(universe_path, "infrastructure", "building_registry.json")
    t_path = os.path.join(universe_path, "technology", "technology_registry.json")
    
    if os.path.exists(b_path):
        with open(b_path, 'r') as f:
            data = json.load(f)
        print(f"Building Registry: OK ({len(data)} items)")
        # Sample check
        if len(data) > 0:
            print(f"Sample Building: {list(data.keys())[0]}")
    else:
        print("Building Registry: MISSING")
        
    if os.path.exists(t_path):
        with open(t_path, 'r') as f:
            data = json.load(f)
        print(f"Technology Registry: OK ({len(data)} items)")
        # Sample check
        if len(data) > 0:
            print(f"Sample Tech: {list(data.keys())[0]}")
    else:
        print("Technology Registry: MISSING")

if __name__ == "__main__":
    verify()
