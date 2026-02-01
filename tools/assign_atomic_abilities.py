import os
import json
import random

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")
ABILITY_REGISTRY_PATH = os.path.join(UNIVERSE_PATH, "factions", "ability_registry.json")

FACTIONS = [
    "zealot_legions", "ascended_order", "hive_swarm", "cyber_synod", "iron_vanguard",
    "ancient_guardians", "rift_daemons", "void_corsairs", "solar_hegemony", "scavenger_clans"
]

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def assign_abilities():
    print("Assigning Atomic Abilities to Rosters...")
    
    # Load Ability Registry
    abilities = load_json(ABILITY_REGISTRY_PATH)
    if not abilities:
        print("Error: Ability Registry not found or empty.")
        return

    # Categorize abilities by faction affinity
    faction_buckets = {f: [] for f in FACTIONS}
    # Pre-process faction keys to match registry (Title Case usually)
    # The registry uses "Zealot_Legions", the file uses "zealot_legions".
    # We will map "Zealot_Legions" -> "zealot_legions"
    
    for aid, data in abilities.items():
        affinities = data.get("faction_affinity", [])
        for aff in affinities:
            key = aff.lower()
            if key in faction_buckets:
                faction_buckets[key].append(aid)
            elif key == "all": # Fallback if we had 'all'
                for k in faction_buckets: faction_buckets[k].append(aid)

    # Process each faction roster
    for faction in FACTIONS:
        roster_path = os.path.join(UNITS_DIR, f"{faction}_roster.json")
        roster = load_json(roster_path)
        
        if not roster:
            continue
            
        units_updated = 0
        available_abilities = faction_buckets.get(faction, [])
        
        if not available_abilities:
            print(f"[WARN] No specific abilities found for {faction}")
            continue

        for unit in roster:
            # Determine logic based on Tier/Role
            tier = int(unit.get("tier", 1) or unit.get("base_stats", {}).get("tier", 1))
            role = str(unit.get("type", "")).lower()
            if "hero" in unit.get("base_stats", {}).get("keywords", ""):
                tier = max(tier, 4) # Ensure heroes are treated as high tier
                
            num_abilities = 0
            if tier == 1: num_abilities = 0
            elif tier == 2: num_abilities = 0 # Mostly specialists trigger later or passives
            elif tier == 3: num_abilities = 1
            elif tier == 4: num_abilities = 2
            elif tier >= 5: num_abilities = 3
            
            # Special case: Casters/Psykers get +1
            name = unit.get("name", "").lower()
            desc = unit.get("description", "").lower()
            if "psyker" in name or "sage" in name or "farseer" in name or "witch" in name:
                num_abilities += 1
                
            if num_abilities > 0:
                # Pick unique abilities
                # Sort of random but deterministic seed could be nice. For now random is fine as it's a one-off gen.
                # Actually, let's try to pick 'relevant' ones if we encoded roles in abilities.
                # Since we didn't strictly encode roles in the bucket, random choice from the faction bucket is the MVP.
                chosen = random.sample(available_abilities, min(num_abilities, len(available_abilities)))
                
                # Check if unit already has abilities, append if so
                current_abilities = unit.get("abilities", [])
                
                # Filter out old generic ones if we want? Or just append. 
                # Let's clean up old "Generic_" ones if they exist, or just ensure uniqueness.
                final_abilities = list(set(current_abilities + chosen))
                
                unit["abilities"] = final_abilities
                units_updated += 1
                
        # Save Roster
        with open(roster_path, 'w') as f:
            json.dump(roster, f, indent=2)
        print(f"Updated {units_updated} units in {faction} with atomic abilities.")

if __name__ == "__main__":
    assign_abilities()
