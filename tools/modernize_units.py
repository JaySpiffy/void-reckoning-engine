import json
import os

def modernize():
    roster_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\void_reckoning\units\hand_crafted_roster.json"
    if not os.path.exists(roster_path):
        print(f"File not found: {roster_path}")
        return
        
    with open(roster_path, 'r', encoding='utf-8') as f:
        roster = json.load(f)
        
    modern_roster = {}
    
    for b_id, unit in roster.items():
        # Baseline Modernization
        unit["logic_role"] = unit.get("logic_role")
        unit["collision_shape"] = unit.get("collision_shape")
        unit["category"] = unit.get("category")
        
        domain = unit.get("domain", "ground")
        u_type = unit.get("type", "infantry").lower()
        u_class = unit.get("unit_class", "").lower()
        
        # 1. Infer Ground Metadata
        if domain == "ground":
            if not unit["category"]:
                unit["category"] = "Infantry" if "infantry" in u_type or "hero" in u_type else "Vehicle"
            
            if not unit["logic_role"]:
                if "hero" in u_type:
                    unit["logic_role"] = "character"
                elif "titan" in u_class:
                    unit["logic_role"] = "power_armor" # Titans are basically big power armor in this logic
                elif "vehicle" in u_type:
                    unit["logic_role"] = "light_vehicle"
                else:
                    unit["logic_role"] = "character"
                    
            if not unit["collision_shape"]:
                if "infantry" in u_type or "hero" in u_type:
                    unit["collision_shape"] = "human_capsule"
                elif "titan" in u_class:
                    unit["collision_shape"] = "large_tank"
                elif "tank" in u_class:
                    unit["collision_shape"] = "large_tank"
                else:
                    unit["collision_shape"] = "tiny_sphere"

            # 2. Squad Members (NEW SYSTEM)
            if "squad_members" not in unit:
                unit["squad_members"] = [
                    {
                        "role": "Single Entity" if unit.get("unique") else "Rifleman",
                        "components": unit.get("components", [])
                    }
                ]

            # 3. Standardize Component Slots for Ground
            new_components = []
            for comp in unit.get("components", []):
                slot = comp.get("slot", "")
                if slot == "weapon_small": comp["slot"] = "hand_main"
                elif slot == "weapon_medium": comp["slot"] = "integrated_fixed"
                elif slot == "weapon_heavy": comp["slot"] = "integrated_fixed"
                new_components.append(comp)
            unit["components"] = new_components

        # 4. Infer Ship Metadata
        elif domain == "space":
             if not unit["category"]:
                 unit["category"] = "Ship"
             
             # Standardize ship slots if any old names remain
             new_components = []
             for comp in unit.get("components", []):
                slot = comp.get("slot", "")
                if slot == "weapon_small": comp["slot"] = "weapon_light"
                elif slot == "weapon_medium": comp["slot"] = "weapon_medium"
                elif slot == "weapon_heavy": comp["slot"] = "weapon_heavy"
                new_components.append(comp)
             unit["components"] = new_components

        modern_roster[b_id] = unit
        
    with open(roster_path, 'w', encoding='utf-8') as f:
        json.dump(modern_roster, f, indent=2)
        
    print(f"Modernized {len(modern_roster)} units in {roster_path}")

if __name__ == "__main__":
    modernize()
