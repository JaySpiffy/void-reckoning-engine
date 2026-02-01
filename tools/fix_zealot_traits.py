import os
import json
import sys

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")
roster_path = os.path.join(UNITS_DIR, "zealot_legions_roster.json")

def fix_zealot_traits():
    if not os.path.exists(roster_path):
        print(f"Error: {roster_path} not found.")
        return

    with open(roster_path, 'r') as f:
        units = json.load(f)

    count = 0
    for unit in units:
        name_lower = unit.get("name", "").lower()
        role_lower = str(unit.get("role", "")).lower() # Sometimes role isn't in base dict, but let's check
        type_lower = unit.get("type", "").lower()
        desc_lower = unit.get("description", "").lower()
        
        # Reset traits to empty list to ensure we "replace" as requested
        new_traits = []

        # Logic Mapping
        # Anti-Air / Sniper -> Sniper
        if "anti-air" in name_lower or "anti_air" in role_lower or "exorcist" in name_lower:
            new_traits.append("Trait_Sniper")
        
        # Tanks / Heavy Vehicles -> Shielded OR Entrenched
        elif "tank" in name_lower or "heavy" in name_lower or "purifier" in name_lower or "cathedral" in name_lower or "basilica" in name_lower:
             new_traits.append("Trait_Shielded")
             new_traits.append("Trait_Entrenched") # Give them both for tankiness? Or just one. User said "or". Let's do Shielded.
        
        # Fast Vehicles / Chariots -> Fleet_Footed? Or just Fearless?
        elif "chariot" in name_lower or "scout" in name_lower or "speed" in name_lower:
             new_traits.append("Trait_Fleet_Footed")

        # Infantry / Walkers -> Fearless (The classic Zealot trait)
        elif "infantry" in type_lower or "walker" in type_lower or "initiate" in name_lower or "templar" in name_lower or "penitent" in name_lower:
             new_traits.append("Trait_Fearless")
             
        # Ships (if not caught by heavy) -> Shielded
        elif "ship" in type_lower:
             new_traits.append("Trait_Shielded")
        
        # Fallback
        else:
             new_traits.append("Trait_Fearless")

        # Always add Hatred because they are Zealots? 
        # User said "replace the uniform Trait_Fearless/Trait_Hatred pairing".
        # So maybe we DON'T add Hatred to everyone.
        # Let's add Hatred only to Elite units maybe? Or just leave it out to differentiate.
        # I'll add Hatred to "Templar" and "Heroes" if I see them.
        if "templar" in name_lower or "hero" in name_lower:
            new_traits.append("Trait_Hatred")

        unit["traits"] = new_traits
        count += 1
        print(f"Updated {unit['name']} -> {new_traits}")

    with open(roster_path, 'w') as f:
        json.dump(units, f, indent=2)
    print(f"Fixed traits for {count} units.")

if __name__ == "__main__":
    fix_zealot_traits()
