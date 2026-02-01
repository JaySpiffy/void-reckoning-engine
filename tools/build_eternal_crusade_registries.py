import os
import json
import sys

sys.path.append(os.getcwd())

from src.utils import registry_builder

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
FACTIONS_DIR = os.path.join(UNIVERSE_PATH, "factions")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")

def build_registries():
    print(f"Building registries for {UNIVERSE_PATH}...")

    # 1. Build Faction Registry
    registry_builder.build_faction_registry(UNIVERSE_PATH)
    
    # 2. Build Tech Registry
    registry_builder.build_tech_registry(UNIVERSE_PATH)
    
    # 3. Build Building Registry (Infrastructure)
    registry_builder.build_building_registry(UNIVERSE_PATH)
    
    # 4. Build Blueprint Registry (Aggregate Units)
    print("Building Blueprint Registry...")
    blueprints = {}
    if os.path.exists(UNITS_DIR):
        for f in os.listdir(UNITS_DIR):
            if f.endswith(".json"):
                with open(os.path.join(UNITS_DIR, f), 'r') as file:
                    data = json.load(file)
                    # data is a list of units or a dict? generate_original_roster saves a LIST.
                    if isinstance(data, list):
                        for unit in data:
                            if "blueprint_id" in unit:
                                blueprints[unit["blueprint_id"]] = unit
    
    bp_path = os.path.join(FACTIONS_DIR, "blueprint_registry.json")
    with open(bp_path, 'w') as f:
        json.dump(blueprints, f, indent=2)
    print(f"Saved {len(blueprints)} blueprints to {bp_path}")

    # 5. Build Stub Registries for Validation
    stubs = {
        "weapon_registry.json": {},
        "ability_registry.json": {},
        "traits_registry.json": {}
    }
    
    for filename, content in stubs.items():
        path = os.path.join(FACTIONS_DIR, filename)
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump(content, f, indent=2)
            print(f"Created stub {filename}")

if __name__ == "__main__":
    build_registries()
