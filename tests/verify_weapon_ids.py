import json
import os
import sys

# Define paths
UNIVERSE_PATH = "C:\\Users\\whitt\\OneDrive\\Desktop\\New folder (4)\\universes\\eternal_crusade"
UNITS_PATH = os.path.join(UNIVERSE_PATH, "units")
REGISTRY_PATH = os.path.join(UNIVERSE_PATH, "factions", "weapon_registry.json")

def verify_solar_hegemony_weapons():
    # Load registry
    try:
        with open(REGISTRY_PATH, 'r') as f:
            registry = json.load(f)
    except FileNotFoundError:
        print(f"Error: Registry not found at {REGISTRY_PATH}")
        return

    # Files to check
    files_to_check = [
        "solar_hegemony_space_units.json",
        "solar_hegemony_capital_ships.json",
        "solar_hegemony_roster.json",
        "solar_hegemony_specialists.json"
    ]

    invalid_count = 0
    checked_count = 0

    for filename in files_to_check:
        filepath = os.path.join(UNITS_PATH, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File {filename} not found.")
            continue
            
        print(f"Checking {filename}...")
        try:
            with open(filepath, 'r') as f:
                units = json.load(f)
                
            for unit in units:
                components = unit.get("components", [])
                for comp in components:
                     weapon_id = comp.get("component")
                     # Ignore non-weapon components if any (usually slots are weapon_*)
                     # But here we assume all listed components are weapons given the context
                     
                     if weapon_id not in registry:
                         print(f"  [INVALID] Unit '{unit.get('name')}' uses unknown weapon ID: '{weapon_id}'")
                         invalid_count += 1
                     else:
                         checked_count += 1
                         
        except json.JSONDecodeError:
            print(f"  [ERROR] Failed to parse JSON in {filename}")

    print(f"\nVerification Complete.")
    print(f"  Checked Components: {checked_count}")
    print(f"  Invalid Components: {invalid_count}")

    if invalid_count == 0:
        print("SUCCESS: All Solar Hegemony units reference valid weapons.")
        sys.exit(0)
    else:
        print("FAILURE: Invalid weapon IDs found.")
        sys.exit(1)

if __name__ == "__main__":
    verify_solar_hegemony_weapons()
