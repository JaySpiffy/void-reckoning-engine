
import json
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.dna_generator import blend_dna_profiles, UNIT_CLASSES, normalize_dna

# Templates for missing classes
GROUND_TEMPLATES = {
    # TIER 1
    "light_infantry": {
        "tier": 1,
        "cost_range": (50, 100),
        "base_stats": {"hp": 60, "armor": 15, "damage": 20, "speed": 8, "type": "infantry"},
        "suggested_abilities": ["Ability_Rapid_Fire"],
        "suggested_traits": ["Veteran Crew"]
    },
    "assault_infantry": {
        "tier": 1,
        "cost_range": (100, 150),
        "base_stats": {"hp": 100, "armor": 25, "damage": 40, "speed": 6, "type": "infantry"},
        "suggested_abilities": ["Ability_Plasma_Burst", "Ability_Fortify_Position"],
        "suggested_traits": ["Reckless Pilot"]
    },
    "skirmisher": {
        "tier": 1,
        "cost_range": (80, 120),
        "base_stats": {"hp": 60, "armor": 10, "damage": 25, "speed": 10, "type": "infantry"},
        "suggested_abilities": ["Ability_Evasive_Maneuvers", "Ability_Sensor_Sweep"],
        "suggested_traits": ["Stalker Pattern"]
    },
    # TIER 2
    "light_vehicle": {
        "tier": 2,
        "cost_range": (200, 350),
        "base_stats": {"hp": 200, "armor": 30, "damage": 50, "speed": 12, "type": "vehicle"},
        "suggested_abilities": ["Ability_Afterburner", "Ability_Hit_and_Run"],
        "suggested_traits": ["Veteran Crew", "Stalker Pattern"]
    },
    "apc": {
        "tier": 2,
        "cost_range": (300, 500),
        "base_stats": {"hp": 250, "armor": 50, "damage": 30, "speed": 10, "type": "vehicle", "transport_capacity": 2},
        "suggested_abilities": ["Ability_Shield_Regen", "Ability_Sensor_Sweep"],
        "suggested_traits": ["Cautious Commander", "Regeneration"]
    },
    "anti_tank": {
        "tier": 2,
        "cost_range": (400, 600),
        "base_stats": {"hp": 150, "armor": 25, "damage": 100, "speed": 8, "type": "vehicle"},
        "suggested_abilities": ["Ability_Tracking_Lock", "Ability_Ion_Cannon"],
        "suggested_traits": ["Master-Crafted", "Reckless Pilot"]
    },
    # TIER 3
    "battle_tank": {
        "tier": 3,
        "cost_range": (800, 1200),
        "base_stats": {"hp": 500, "armor": 80, "damage": 120, "speed": 7, "type": "vehicle"},
        "suggested_abilities": ["Ability_Plasma_Burst", "Ability_Fortify_Position"],
        "suggested_traits": ["Master-Crafted", "Veteran Crew"]
    },
    "heavy_vehicle": {
        "tier": 3,
        "cost_range": (1200, 2000),
        "base_stats": {"hp": 600, "armor": 100, "damage": 150, "speed": 6, "type": "vehicle"},
        "suggested_abilities": ["Ability_Torpedo_Salvo", "Ability_Shield_Regen"],
        "suggested_traits": ["Reckless Pilot", "Veteran Crew"]
    },
    "superheavy_tank": {
        "tier": 3,
        "cost_range": (2000, 3000),
        "base_stats": {"hp": 1000, "armor": 150, "damage": 250, "speed": 5, "type": "vehicle"},
        "suggested_abilities": ["Ability_Overcharge", "Ability_Fortify_Position", "Ability_EMP_Burst"],
        "suggested_traits": ["Cautious Commander", "Regeneration", "Master-Crafted"]
    }
}

FACTION_THEMES = {
    "Zealot_Legions": {
        "light_infantry": "Initiate", "assault_infantry": "Crusader", "skirmisher": "Scout", 
        "light_vehicle": "Sentinel", "apc": "Rhino", "anti_tank": "Lancer", 
        "battle_tank": "Predator", "heavy_vehicle": "Land Raider", "superheavy_tank": "Baneblade"
    },
    "Ascended_Order": {
        "light_infantry": "Adept", "assault_infantry": "Templar", "skirmisher": "Seeker",
        "light_vehicle": "Glider", "apc": "Conveyance", "anti_tank": "Prism",
        "battle_tank": "Arbiter", "heavy_vehicle": "Sanctuary", "superheavy_tank": "Cathedral"
    },
    # Add generics for others if needed or rely on auto-naming
}

def apply_ground_dna_adjustments(dna):
    """
    Applies ground-specific adjustments:
    - Mass -20% (Ground units smaller than ships)
    - Frequency +10% (Maneuverability)
    - Stability +5% (Terrain stability)
    """
    new_dna = dna.copy()
    
    # Apply modifiers
    if "atom_mass" in new_dna: new_dna["atom_mass"] *= 0.8
    if "atom_frequency" in new_dna: new_dna["atom_frequency"] *= 1.1
    if "atom_stability" in new_dna: new_dna["atom_stability"] *= 1.05
    
    return normalize_dna(new_dna)

def generate_missing():
    base_path = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units"
    factions_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\factions"
    
    # Load faction DNA
    with open(os.path.join(factions_dir, "faction_dna.json"), "r") as f:
        faction_dna_data = json.load(f)
        
    registry_path = os.path.join(factions_dir, "faction_registry.json")
    with open(registry_path, "r", encoding='utf-8') as f:
        registry = json.load(f)
        
    for faction in registry.keys():
        print(f"Checking {faction}...")
        
        # 1. Identify Missing
        # Only check the REINFORCEMENTS file to see if we already generated it.
        # We purposely ignore the main roster files to ensure we have a standard set of "modern" units.
        
        current_reinforcements = []
        reinforcement_file = os.path.join(base_path, f"{faction.lower()}_ground_reinforcements.json")
        if os.path.exists(reinforcement_file):
            try:
                with open(reinforcement_file, "r", encoding='utf-8') as f:
                    current_reinforcements = json.load(f)
            except: pass
            
        existing_generated_classes = set(u.get("unit_class") for u in current_reinforcements if u.get("unit_class"))
            
        # We want ALL 9 classes to be present in the reinforcements/modern lineup
        target_classes = list(GROUND_TEMPLATES.keys())
        missing_classes = [c for c in target_classes if c not in existing_generated_classes]
        
        print(f"  Already Generated: {sorted(list(existing_generated_classes))}")
        print(f"  Generating: {missing_classes}")
        
        # 2. Generate Units
        new_units = []
        f_dna = faction_dna_data.get(faction, {})
        theme = FACTION_THEMES.get(faction, {})
        
        for cls_name in missing_classes:
            if cls_name not in GROUND_TEMPLATES:
                print(f"  Skipping {cls_name}, no template.")
                continue

            template = GROUND_TEMPLATES[cls_name]
            
            # Blend DNA
            c_dna = UNIT_CLASSES.get(cls_name)
            if not c_dna: 
                print(f"  Warning: No DNA preset for {cls_name}")
                continue
            
            blended = blend_dna_profiles(c_dna, f_dna, class_weight=0.5)
            final_dna = apply_ground_dna_adjustments(blended)
            
            # Name
            flavor = theme.get(cls_name, cls_name.replace('_', ' ').title())
            display_name = f"{faction} {flavor}"
            
            # Cost
            cost = int(sum(template["cost_range"]) / 2)
            upkeep = cost // 10
            
            unit = {
                "name": display_name,
                "blueprint_id": f"{faction.lower()}_{cls_name}",
                "type": template["base_stats"]["type"],
                "faction": faction,
                "cost": cost,
                "upkeep": upkeep,
                "base_stats": dict(template["base_stats"]),
                "elemental_dna": final_dna,
                "source_universe": "eternal_crusade",
                "description": f"{faction} {cls_name}-class ground unit. Auto-generated via Taxonomy.",
                "abilities": list(template["suggested_abilities"]),
                "traits": list(template["suggested_traits"]),
                "unit_class": cls_name,
                "domain": "ground"
            }
            unit["base_stats"]["cost"] = cost
            if "transport_capacity" in template["base_stats"]:
                unit["base_stats"]["transport_capacity"] = template["base_stats"]["transport_capacity"]
                
            new_units.append(unit)
            
        # 3. Write to new file (Overwrites previous reinforcement file)
        # We need to appended to existing reinforcement file if it exists to not lose skirmishers etc
        outfile = os.path.join(base_path, f"{faction.lower()}_ground_reinforcements.json")
        final_list = []
        
        if os.path.exists(outfile):
            try:
                with open(outfile, "r", encoding='utf-8') as f:
                    final_list = json.load(f)
            except: pass
            
        # Add new units effectively merging
        existing_ids = set(u["blueprint_id"] for u in final_list)
        for nu in new_units:
            if nu["blueprint_id"] not in existing_ids:
                final_list.append(nu)
                
        if final_list:
            with open(outfile, "w", encoding='utf-8') as f:
                json.dump(final_list, f, indent=2)
            print(f"  Updated {outfile} with total {len(final_list)} units.")


if __name__ == "__main__":
    generate_missing()
