import os
import json
import sys

# Ensure we can import from src
sys.path.append(os.getcwd())

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")
FACTION_DNA_PATH = os.path.join(UNIVERSE_PATH, "factions", "faction_dna.json")

FACTIONS = [
    "zealot_legions", "ascended_order", "hive_swarm", "cyber_synod", "iron_vanguard",
    "ancient_guardians", "rift_daemons", "void_corsairs", "solar_hegemony", "scavenger_clans"
]

NEW_SPECIALISTS = {
    "zealot_legions": {
        "support": "Chaplain-Medic", "fast_attack": "Assault Crusader", "heavy_infantry": "Bulwark Sentinel"
    },
    "ascended_order": {
        "support": "Aether Conduit", "fast_attack": "Warp Striker", "heavy_infantry": "Psi-Warden"
    },
    "hive_swarm": {
        "support": "Synapse Node", "fast_attack": "Ravener Strain", "heavy_infantry": "Carnifex Brood"
    },
    "cyber_synod": {
        "support": "Repair Construct", "fast_attack": "Wraith-Flayer", "heavy_infantry": "Monolith Guard"
    },
    "void_corsairs": {
        "support": "Raider Medic", "fast_attack": "Voidrunner", "heavy_infantry": "Boarding Marine"
    },
    "rift_daemons": {
        "support": "Warp Healer", "fast_attack": "Fury Daemon", "heavy_infantry": "Bloodletter Horde"
    },
    "scavenger_clans": {
        "support": "Scrap-Medic", "fast_attack": "Buggy Raider", "heavy_infantry": "Salvage Brute"
    },
    "iron_vanguard": {
        "support": "Field Engineer", "fast_attack": "Sentinel Scout", "heavy_infantry": "Siege Trooper"
    },
    "solar_hegemony": {
        "support": "Tech-Priest", "fast_attack": "Plasma Lancer", "heavy_infantry": "Phalanx Guard"
    },
    "ancient_guardians": {
        "support": "Farseer", "fast_attack": "Warp Spider", "heavy_infantry": "Wraithguard"
    }
}

DNA_TEMPLATES = {
    "anti_air": {"atom_frequency": 30.0, "atom_focus": 22.0, "atom_energy": 15.0},
    "anti_tank": {"atom_mass": 25.0, "atom_energy": 20.0, "atom_volatility": 15.0},
    "stealth": {"atom_frequency": 28.0, "atom_focus": 20.0, "atom_information": 15.0, "atom_mass": 5.0},
    "anti_capital": {"atom_mass": 30.0, "atom_energy": 25.0, "atom_volatility": 15.0, "atom_cohesion": 10.0},
    "support": {"atom_cohesion": 30.0, "atom_will": 25.0, "atom_stability": 20.0},
    "fast_attack": {"atom_frequency": 35.0, "atom_energy": 20.0, "atom_volatility": 15.0},
    "heavy_infantry": {"atom_mass": 25.0, "atom_cohesion": 25.0, "atom_stability": 20.0}
}

ABILITY_MATRIX = {
    "support": {
        "default": ["Ability_Shield_Harmonics", "Ability_Nanite_Repair", "Ability_Emergency_Repairs"],
        "zealot_legions": ["Ability_Morale_Boost", "Ability_Inspiration_Aura", "Ability_Psychic_Barrier"],
        "hive_swarm": ["Ability_Nanite_Repair", "Ability_Afterburner"], 
        "cyber_synod": ["Ability_Tactical_Doctrine", "Ability_Logic_Override"],
        "iron_vanguard": ["Ability_Emergency_Repairs", "Ability_Fortify_Position"]
    },
    "fast_attack": {
        "default": ["Ability_Afterburner", "Ability_Hit_and_Run"],
        "void_corsairs": ["Ability_Hit_and_Run", "Ability_Afterburner", "Ability_Phase_Jump"],
        "rift_daemons": ["Ability_Warp_Jump", "Ability_Phase_Jump"],
        "hive_swarm": ["Ability_Afterburner", "Ability_Hit_and_Run"],
        "ancient_guardians": ["Ability_Webway_Strike", "Ability_Phase_Jump"]
    },
    "heavy_infantry": {
        "default": ["Ability_Fortify_Position", "Ability_Kinetic_Strike"],
        "zealot_legions": ["Ability_Fortify_Position", "Ability_Morale_Boost"],
        "iron_vanguard": ["Ability_Fortify_Position", "Ability_Emergency_Repairs", "Ability_Kinetic_Strike"],
        "cyber_synod": ["Ability_Fortify_Position", "Ability_Tactical_Doctrine"]
    },
    "anti_air": {"default": ["Ability_EMP_Burst", "Ability_Ion_Cannon", "Ability_Frag_Barrage"]},
    "anti_tank": {"default": ["Ability_Melta_Beam", "Ability_Kinetic_Strike", "Ability_Antimatter_Torpedo"]},
    "stealth": {"default": ["Ability_Phase_Jump", "Ability_Neural_Disruptor", "Ability_Evasive_Maneuvers"]},
    "anti_capital": {"default": ["Ability_Antimatter_Torpedo", "Ability_Orbital_Bombardment", "Ability_Ion_Cannon"]}
}

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def normalize_dna(dna):
    total = sum(dna.values())
    if total <= 0: return dna
    factor = 100.0 / total
    return {k: round(v * factor, 2) for k, v in dna.items()}

def get_abilities(role, faction):
    if role in ABILITY_MATRIX:
        if faction in ABILITY_MATRIX[role]:
            return ABILITY_MATRIX[role][faction]
        return ABILITY_MATRIX[role]["default"]
    return []

def get_faction_dna_overlay(faction_key, all_dna):
    if faction_key in all_dna: return all_dna[faction_key]
    title_key = faction_key.replace("_", " ").title().replace(" ", "_")
    return all_dna.get(title_key, {})

def calculate_blended_dna(role, faction_key, all_dna):
    base_dna = {
        "atom_mass": 0.0, "atom_energy": 0.0, "atom_cohesion": 0.0, "atom_volatility": 0.0,
        "atom_stability": 0.0, "atom_focus": 0.0, "atom_frequency": 0.0, "atom_aether": 0.0,
        "atom_will": 0.0, "atom_information": 0.0
    }
    
    # Scale Role Template (0.7 weight)
    template = DNA_TEMPLATES.get(role, {})
    for k, v in template.items():
        base_dna[k] += v * 0.7
    
    # Scale Faction Overlay (0.3 weight)
    faction_dna = get_faction_dna_overlay(faction_key, all_dna)
    
    for k, v in faction_dna.items():
        if not k.startswith("atom_"): 
            continue # Skip non-atom fields like description
            
        if k in base_dna:
            base_dna[k] += v * 0.3
        else:
             base_dna[k] = v * 0.3

    # Normalize to 100
    return normalize_dna(base_dna)

def create_unit(faction, role, name, tier, cost, all_dna):
    blueprint_id = f"{faction}_{name.lower().replace(' ', '_').replace('-', '_')}"
    
    final_dna = calculate_blended_dna(role, faction, all_dna)
    
    description = f"Specialist unit for {faction} fulfilling the {role} role."
    if "Zealot" in faction:
        description = f"Fanatical {role.replace('_', ' ')} bolstering the Crusade with unwavering zeal."
    elif "Ascended" in faction:
        description = f"Enlightened {role.replace('_', ' ')} channeling the power of the Aether."
    elif "Hive" in faction:
        description = f"Bio-adapted {role.replace('_', ' ')} strain evolved for the swarm."
    elif "Cyber" in faction:
        description = f"Automated {role.replace('_', ' ')} construct optimized for efficiency."
    elif "Iron" in faction:
        description = f"Heavily armored {role.replace('_', ' ')} leveraging industrial might."
    
    unit = {
        "name": name,
        "blueprint_id": blueprint_id,
        "type": "infantry" if role in ["support", "heavy_infantry"] else "vehicle",
        "faction": faction.replace("_", " ").title().replace(" ", "_"),
        "tier": tier,
        "cost": cost,
        "base_stats": {
            "role": role,
            "tier": tier,
            "hp": cost // 5,
            "armor": cost // 20,
            "damage": cost // 10,
            "cost": cost,
            "keywords": f"specialist {role}"
        },
        "elemental_dna": final_dna,
        "source_universe": "eternal_crusade",
        "description": description,
        "specialist": True,
        "abilities": get_abilities(role, faction),
        "traits": ["Trait_Fearless"] if faction == "zealot_legions" else []
    }
    return unit

def expand_specialists():
    print("Expanding Specialist Rosters (Fixed)...")
    
    all_faction_dna = load_json(FACTION_DNA_PATH)
    if not all_faction_dna: 
        print("Error: Could not load faction DNA.")
        return

    for faction in FACTIONS:
        filepath = os.path.join(UNITS_DIR, f"{faction}_specialists.json")
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r') as f:
            units = json.load(f)
            
        # 1. Clean Slate for New Units
        kept_units = []
        for u in units:
            role = u.get("base_stats", {}).get("role", "")
            if role in ["support", "fast_attack", "heavy_infantry"]:
                continue
            kept_units.append(u)
        units = kept_units

        # 2. Update Existing Units
        for unit in units:
            role = unit.get("base_stats", {}).get("role", "specialist")
            if role == "anti_capital_ship": 
                role = "anti_capital"
                unit["base_stats"]["role"] = "anti_capital"
                
            # COST FIX for Anti-Capital
            if role == "anti_capital":
                unit["cost"] = 1150
                unit["base_stats"]["cost"] = 1150
                unit["tier"] = 3
                unit["base_stats"]["tier"] = 3
                unit["base_stats"]["hp"] = 800
                unit["base_stats"]["damage"] = 300
            
            # DNA Blending
            if role in DNA_TEMPLATES:
                unit["elemental_dna"] = calculate_blended_dna(role, faction, all_faction_dna)
                
            # Abilities
            if "abilities" not in unit or not unit["abilities"]:
                unit["abilities"] = get_abilities(role, faction)
                
            # Metadata Parity
            unit["source_universe"] = "eternal_crusade"
            if "description" not in unit: 
                 unit["description"] = f"{faction.replace('_',' ').title()} {role.replace('_', ' ')} unit."
            unit["specialist"] = True

        # 3. Add New Units (Support, Fast Attack, Heavy Infantry)
        new_roles = NEW_SPECIALISTS.get(faction, {})
        for role_key, name in new_roles.items():
            cost = 700 if role_key == "support" else (800 if role_key == "fast_attack" else 950)
            tier = 2 if role_key != "heavy_infantry" else 3
            units.append(create_unit(faction, role_key, name, tier, cost, all_faction_dna))
             
        # Save
        with open(filepath, 'w') as f:
            json.dump(units, f, indent=2)
        print(f"Updated {faction} specialists: {len(units)} total units.")

if __name__ == "__main__":
    expand_specialists()
