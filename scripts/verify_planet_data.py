
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.universe_data import UniverseDataManager
from src.core.config import set_active_universe, get_universe_config

def verify_planet_data():
    universe = "eternal_crusade"
    set_active_universe(universe)
    
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data(universe)
    
    classes = udm.get_planet_classes()
    
    print(f"Loaded {len(classes)} planet classes.")
    
    required = ["Agri-World", "Hive World", "Forge World", "Shattered World"]
    
    failed = False
    
    for req in required:
        if req not in classes:
            print(f"[FAIL] Missing {req}")
            failed = True
        else:
            data = classes[req]
            slots = data.get("slots", 0)
            if slots <= 0:
                 print(f"[FAIL] {req} has {slots} slots (Expected > 0)")
                 failed = True
            else:
                 print(f"[PASS] {req}: {slots} slots, Modifiers: req={data.get('req_mod')}, def={data.get('def_mod')}")
                 
    if failed:
        sys.exit(1)
        
    print("\nAll planet data checks passed.")

if __name__ == "__main__":
    verify_planet_data()
