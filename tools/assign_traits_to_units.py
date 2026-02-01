import os
import json
import sys

sys.path.append(os.getcwd())

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")
TRAITS_REGISTRY_PATH = os.path.join(UNIVERSE_PATH, "factions", "traits_registry.json")

FACTIONS = [
    "zealot_legions", "ascended_order", "hive_swarm", "cyber_synod", "iron_vanguard",
    "ancient_guardians", "rift_daemons", "void_corsairs", "solar_hegemony", "scavenger_clans"
]

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    print(f"[ERR] Could not load {path}")
    return {}

def check_dna_requirements(unit_dna, requirements):
    """Returns True if unit_dna meets all requirements."""
    for atom, threshold in requirements.items():
        if unit_dna.get(atom, 0) < threshold:
            # Check for float precision issues, allow 0.01 tolerance
            if unit_dna.get(atom, 0) + 0.01 < threshold:
                return False
    return True

def get_trait_priority(trait_id, trait_data, unit_dna, unit_faction):
    reqs = trait_data.get("dna_requirements", {})
    
    # STRICT CHECK: Must meet DNA requirements
    if not check_dna_requirements(unit_dna, reqs):
        return -1 
        
    score = 0
    
    # Faction Match
    faction_title = unit_faction.replace("_", " ").title().replace(" ", "_")
    if faction_title in trait_data.get("faction_affinity", []):
        score += 50
        
    # DNA Over-match
    for atom, threshold in reqs.items():
        val = unit_dna.get(atom, 0)
        score += (val - threshold)
        
    return score

def assign_traits():
    print("Assigning Traits to Units (Strict Check)...")
    
    traits_registry = load_json(TRAITS_REGISTRY_PATH)
    if not traits_registry: return

    for faction in FACTIONS:
        # Include variants file in loop
        file_suffixes = ["_roster.json", "_heroes.json", "_specialists.json", "_specialists_variants.json", "_roster_variants.json"]
        
        for suffix in file_suffixes:
            filename = f"{faction}{suffix}"
            filepath = os.path.join(UNITS_DIR, filename)
            
            if not os.path.exists(filepath):
                continue
                
            # Read
            with open(filepath, 'r') as f:
                units = json.load(f)
            
            updated_count = 0
            for unit in units:
                if "elemental_dna" not in unit:
                    continue
                    
                unit_dna = unit["elemental_dna"]
                cost = unit.get("cost", unit.get("base_stats", {}).get("cost", 0))
                
                # Determine Max Traits
                max_traits = 1
                if cost > 200: max_traits = 2
                if cost > 1000: max_traits = 3
                if cost > 5000: max_traits = 4
                
                if "hero" in unit.get("base_stats", {}).get("keywords", ""):
                     max_traits = max(max_traits, 3)

                # Score all traits
                valid_traits = []
                for t_id, t_data in traits_registry.items():
                    score = get_trait_priority(t_id, t_data, unit_dna, faction)
                    if score >= 0:
                        valid_traits.append((score, t_id))
                
                valid_traits.sort(key=lambda x: x[0], reverse=True)
                assigned = [t_id for score, t_id in valid_traits[:max_traits]]
                
                # Fallback: If unit has 0 valid traits but is high tier, give it something basic?
                # Actually, better to leave empty than assign invalid trait.
                
                # Check for Hatred legacy
                # If unit had Trait_Hatred but doesn't meet reqs, it will be stripped.
                # If we want to FORCE Hatred on Zealots, we would need to boost DNA or lower reqs.
                # Current plan: Strict adherence to DNA.
                
                unit["traits"] = assigned
                updated_count += 1

            # Save
            with open(filepath, 'w') as f:
                json.dump(units, f, indent=2)
            print(f"Updated {filename}: {updated_count} units processed.")

    print("Strict Trait Assignment complete.")

if __name__ == "__main__":
    assign_traits()
