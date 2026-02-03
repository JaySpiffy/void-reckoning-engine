import os
import json

def consolidate():
    units_dir = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\void_reckoning\units"
    out_path = os.path.join(units_dir, "hand_crafted_roster.json")
    
    unique_roster = {}
    
    # We want to keep Heroes and Specialists which aren't in the procedural rosters
    targets = ["heroes", "specialists", "specialists_variants", "capital_ships", "strategic_ground", "ground_reinforcements"]
    factions = [
        "algorithmic_hierarchy", "aurelian_hegemony", "biotide_collective", 
        "nebula_drifters", "primeval_sentinels", "scraplord_marauders", 
        "steelbound_syndicate", "templars_of_the_flux", "transcendent_order", 
        "voidspawn_entities"
    ]
    
    processed_files = 0
    for faction in factions:
        for cat in targets:
            filename = f"{faction}_{cat}.json"
            filepath = os.path.join(units_dir, filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, list):
                            for unit in data:
                                b_id = unit.get("blueprint_id")
                                if b_id:
                                    unique_roster[b_id] = unit
                        elif isinstance(data, dict):
                            for b_id, unit in data.items():
                                unique_roster[b_id] = unit
                        processed_files += 1
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(unique_roster, f, indent=2)
    
    print(f"Consolidated {len(unique_roster)} units from {processed_files} files into {out_path}")

if __name__ == "__main__":
    consolidate()
