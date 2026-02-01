
import os
import json
from pathlib import Path

def audit_universe(uni_path):
    print(f"\n--- Auditing Universe: {uni_path.name} ---")
    config_path = uni_path / "config.json"
    blueprint_path = uni_path / "factions" / "blueprint_registry.json"
    
    if not config_path.exists():
        print(f"[ERROR] config.json missing at {config_path}")
        return
    
    if not blueprint_path.exists():
        print(f"[ERROR] blueprint_registry.json missing at {blueprint_path}")
        return
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
        config_factions = set(config_data.get("factions", []))
        
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprints = json.load(f)
        
    blueprint_factions = set()
    for bp_id in blueprints.keys():
        if ":" in bp_id:
            blueprint_factions.add(bp_id.split(":")[0])
            
    print(f"Factions in config.json: {len(config_factions)}")
    print(f"Factions with units in registry: {len(blueprint_factions)}")
    
    missing_in_config = blueprint_factions - config_factions
    redundant_in_config = config_factions - blueprint_factions
    
    if missing_in_config:
        print(f"[UNITS IN REGISTRY BUT NOT IN CONFIG] {sorted(list(missing_in_config))}")
    if redundant_in_config:
        significant_missing = [f for f in redundant_in_config if f != "Neutral"]
        if significant_missing:
            print(f"[FACTION IN CONFIG BUT NO UNITS IN REGISTRY] {sorted(list(significant_missing))}")
        else:
            print("[INFO] Only 'Neutral' faction has no units (expected).")
    
    return list(blueprint_factions)

def main():
    universes_root = Path("universes")
    
    # Scan all directories in universes/
    all_universes = [d.name for d in universes_root.iterdir() if d.is_dir() and (d / "config.json").exists()]
    
    for uni_name in sorted(all_universes):
        uni_path = universes_root / uni_name
        audit_universe(uni_path)

if __name__ == "__main__":
    main()
