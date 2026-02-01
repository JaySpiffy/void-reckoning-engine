
import json
import os
from collections import defaultdict

def count_units():
    base_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units"
    
    # Store counts: faction -> domain -> count
    counts = defaultdict(lambda: {"space": 0, "ground": 0})
    
    for filename in os.listdir(base_dir):
        if not filename.endswith(".json"): continue
        
        # Infer faction from filename (e.g., zealot_legions_space_units.json)
        # Using a reliable way: read the "faction" field from the first unit
        filepath = os.path.join(base_dir, filename)
        
        try:
            with open(filepath, "r", encoding='utf-8') as f:
                units = json.load(f)
                
            if not isinstance(units, list): continue
            
            for u in units:
                faction = u.get("faction", "Unknown")
                domain = u.get("domain", "ground").lower() # Default to ground if missing, but we fixed this
                
                # Check file name as fallback/sanity if domain missing
                if "space" in filename and domain != "space":
                     domain = "space"
                
                counts[faction][domain] += 1
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    print(f"{'Faction':<20} | {'Space Ships':<12} | {'Ground Units':<12} | {'Total':<10}")
    print("-" * 60)
    
    total_space = 0
    total_ground = 0
    
    for faction in sorted(counts.keys()):
        space = counts[faction]["space"]
        ground = counts[faction]["ground"]
        total = space + ground
        print(f"{faction:<20} | {space:<12} | {ground:<12} | {total:<10}")
        
        total_space += space
        total_ground += ground

    print("-" * 60)
    print(f"{'TOTAL':<20} | {total_space:<12} | {total_ground:<12} | {total_space+total_ground:<10}")

if __name__ == "__main__":
    count_units()
