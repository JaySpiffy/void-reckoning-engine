import os
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.universal_stats import VALID_METRICS
from src.utils.blueprint_registry import BlueprintRegistry

def validate_blueprint(blueprint: Dict[str, Any], source_label: str) -> List[str]:
    """Validates a single blueprint and returns a list of error messages."""
    errors = []
    b_id = blueprint.get("id")
    
    if not b_id:
        errors.append(f"[{source_label}] Missing 'id' field.")
        return errors # Can't continue without ID
        
    required = ["name", "type", "base_stats", "universal_stats"]
    for field in required:
        if field not in blueprint:
            errors.append(f"[{b_id}] Missing required field: {field}")
            
    # Validate universal_stats keys
    u_stats = blueprint.get("universal_stats", {})
    if isinstance(u_stats, dict):
        for metric in u_stats.keys():
            if metric not in VALID_METRICS:
                errors.append(f"[{b_id}] Invalid universal metric: {metric}")
    else:
        errors.append(f"[{b_id}] 'universal_stats' must be a dictionary.")
        
    # Validate base_stats
    b_stats = blueprint.get("base_stats", {})
    if not isinstance(b_stats, dict):
        errors.append(f"[{b_id}] 'base_stats' must be a dictionary.")
        
    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate Blueprint Registry files.")
    parser.add_argument("--universe", type=str, help="Universe name to validate (e.g., star_wars).")
    parser.add_argument("--all", action="store_true", help="Validate all universes.")
    args = parser.parse_args()
    
    from src.core.config import UNIVERSE_ROOT
    
    universes_to_check = []
    if args.all:
        for item in os.listdir(UNIVERSE_ROOT):
            if os.path.isdir(os.path.join(UNIVERSE_ROOT, item)):
                universes_to_check.append(item)
    elif args.universe:
        universes_to_check.append(args.universe)
    else:
        # Default to base if nothing specified?
        universes_to_check.append("base")
        
    total_blueprints = 0
    total_errors = 0
    
    for uni in universes_to_check:
        print(f"\n--- Validating Universe: {uni} ---")
        u_path = os.path.join(UNIVERSE_ROOT, uni)
        b_dir = os.path.join(u_path, "blueprints")
        
        if not os.path.exists(b_dir):
            print(f"No blueprints directory found at {b_dir}")
            continue
            
        for root, _, files in os.walk(b_dir):
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, UNIVERSE_ROOT)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        items = []
                        if isinstance(data, list): items = data
                        elif isinstance(data, dict):
                            if "id" in data: items = [data]
                            else:
                                for k, v in data.items():
                                    if isinstance(v, dict) and "id" not in v: v["id"] = k
                                    items.append(v)
                                    
                        for item in items:
                            total_blueprints += 1
                            errors = validate_blueprint(item, rel_path)
                            if errors:
                                total_errors += len(errors)
                                for err in errors:
                                    print(f"ERROR: {err}")
                            else:
                                # print(f"PASS: {item.get('id')}")
                                pass
                                
                    except Exception as e:
                        print(f"CRITICAL ERROR loading {path}: {e}")
                        total_errors += 1
                        
    print(f"\nValidation Summary:")
    print(f"  Blueprints Checked: {total_blueprints}")
    print(f"  Total Errors: {total_errors}")
    
    if total_errors > 0:
        sys.exit(1)
    else:
        print("All blueprints passed validation!")
        sys.exit(0)

if __name__ == "__main__":
    main()
