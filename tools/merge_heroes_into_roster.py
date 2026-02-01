import os
import json

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")

FACTIONS = [
    "zealot_legions",
    "ascended_order",
    "hive_swarm",
    "cyber_synod",
    "iron_vanguard",
    "ancient_guardians",
    "rift_daemons",
    "void_corsairs",
    "solar_hegemony",
    "scavenger_clans"
]

def merge_heroes():
    print("Starting Hero Merge Process...")
    
    for faction in FACTIONS:
        roster_file = os.path.join(UNITS_DIR, f"{faction}_roster.json")
        heroes_file = os.path.join(UNITS_DIR, f"{faction}_heroes.json")
        
        if not os.path.exists(roster_file):
            print(f"[WARN] Roster not found for {faction}: {roster_file}")
            continue
            
        if not os.path.exists(heroes_file):
            print(f"[INFO] No heroes file for {faction}")
            continue
            
        try:
            with open(roster_file, 'r') as f:
                roster_data = json.load(f)
            
            with open(heroes_file, 'r') as f:
                heroes_data = json.load(f)
                
            if not isinstance(roster_data, list):
                print(f"[ERR] Roster data for {faction} is not a list!")
                continue
                
            if not isinstance(heroes_data, list):
                print(f"[ERR] Heroes data for {faction} is not a list!")
                continue

            # Create set of existing IDs for fast lookup
            existing_ids = set()
            for unit in roster_data:
                if "blueprint_id" in unit:
                    existing_ids.add(unit["blueprint_id"])
            
            added_count = 0
            for hero in heroes_data:
                b_id = hero.get("blueprint_id")
                if not b_id:
                    print(f"[WARN] Hero missing blueprint_id in {faction}")
                    continue
                
                # Update keywords as requested
                base_stats = hero.get("base_stats", {})
                keywords = base_stats.get("keywords", "")
                if "hero" not in keywords:
                    keywords += " hero"
                if f"tier{hero.get('tier', 4)}" not in keywords:
                    keywords += f" tier{hero.get('tier', 4)}"
                base_stats["keywords"] = keywords.strip()
                hero["base_stats"] = base_stats

                if b_id not in existing_ids:
                    roster_data.append(hero)
                    existing_ids.add(b_id)
                    added_count += 1
                else:
                    print(f"[INFO] Skipping duplicate hero {b_id} in {faction}")

            if added_count > 0:
                with open(roster_file, 'w') as f:
                    json.dump(roster_data, f, indent=2)
                print(f"[SUCCESS] Merged {added_count} heroes into {faction}_roster.json")
            else:
                print(f"[INFO] No new heroes to merge for {faction}")

        except Exception as e:
            print(f"[ERR] Failed processing {faction}: {e}")

if __name__ == "__main__":
    merge_heroes()
