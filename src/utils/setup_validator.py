
import os
import json
import sys
from collections import defaultdict

# Add src to path if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.config import get_universe_config, list_available_universes
from src.core.universe_data import UniverseDataManager

def validate_cpu_affinity(config_path):
    print("\n--- Validating CPU Affinity ---")
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        universes = data.get("universes", [])
        core_map = defaultdict(list)
        
        for u in universes:
            if not u.get("enabled", False): continue
            
            name = u.get("name")
            affinity = u.get("processor_affinity", [])
            
            for core in affinity:
                core_map[core].append(name)
                
        errors = []
        for core, names in core_map.items():
            if len(names) > 1:
                errors.append(f"Core {core} assigned to multiple universes: {names}")
                
        if errors:
            print("FAIL: Overlapping CPU assignments found:")
            for e in errors: print(f"  - {e}")
            return False
        else:
            print("PASS: CPU Affinity is valid.")
            return True
            
    except Exception as e:
        print(f"FAIL: Could not read config file: {e}")
        return False

def validate_universe_integrity(universe_name):
    print(f"\n--- Validating Universe: {universe_name} ---")
    try:
        conf = get_universe_config(universe_name)
        
        # 1. Check Directories
        required_dirs = ["factions", "technology", "infrastructure"]
        missing_dirs = []
        for d in required_dirs:
            path = conf.universe_root / d
            if not path.exists():
                missing_dirs.append(d)
        
        if missing_dirs:
            print(f"FAIL: Missing directories: {missing_dirs}")
            return False
            
        # 2. Check Critical Files
        # game_data.json is critical for planet gen
        gd_path = conf.universe_root / "game_data.json"
        if not gd_path.exists():
            print(f"FAIL: Missing game_data.json (Required for Planet Generation)")
            return False
            
        with open(gd_path, 'r') as f:
            gd = json.load(f)
            if "planet_classes" not in gd or not gd["planet_classes"]:
                print(f"FAIL: game_data.json missing 'planet_classes'")
                return False
                
        print(f"PASS: Structure and Critical Data valid.")
        return True
        
    except Exception as e:
        print(f"FAIL: Exception checking universe: {e}")
        return False

def validate_critical_code_patches():
    print("\n--- Validating Critical Code Patches ---")
    
    success = True
    # 1. Galaxy Ready Signal (Deadlock Fix)
    sim_runner_path = os.path.join("src", "engine", "simulation_runner.py")
    if os.path.exists(sim_runner_path):
        with open(sim_runner_path, 'r') as f:
            content = f.read()
            if 'ALWAYS signal ready' in content:
                 print("PASS: Simulation Runner Deadlock Fix detected.")
            else:
                 print("WARN: Simulation Runner Deadlock Fix NOT detected (Check line ~100).")
    
    # 2. Atomic Phase (Combat Logic Fix)
    combat_phases_path = os.path.join("src", "combat", "combat_phases.py")
    if os.path.exists(combat_phases_path):
        with open(combat_phases_path, 'r') as f:
            content = f.read()
            if 'def resolve_atomic_phase' in content:
                print("PASS: Atomic Combat Phase detected.")
            else:
                print("FAIL: Atomic Combat Phase MISSING from combat_phases.py")
                success = False
    return success

def run_validations(config_path=None):
    if not config_path:
        root_dir = os.getcwd()
        config_path = os.path.join(root_dir, "config", "unified_simulation_config.json")
        
    print(f"Running Validation Suite...")
    
    all_passed = True
    
    # 1. Config Check
    if os.path.exists(config_path):
        if not validate_cpu_affinity(config_path):
            all_passed = False
    else:
        print(f"FAIL: Config not found at {config_path}")
        all_passed = False
        
    # 2. Universe Check
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        for u in data.get("universes", []):
            if u.get("enabled"):
                if not validate_universe_integrity(u.get("name")):
                    all_passed = False
    except:
        pass
        
    # 3. Code Check
    if not validate_critical_code_patches():
        all_passed = False
        
    return all_passed

def main():
    if not run_validations():
        sys.exit(1)

if __name__ == "__main__":
    main()
