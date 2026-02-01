#!/usr/bin/env python3
"""
Helper script to generate unit blueprints from class templates.
Usage: python scripts/generate_unit_from_class.py --class fighter --faction Zealot_Legions --name "Cherubim"
"""

import json
import argparse
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.utils.dna_generator import UNIT_CLASSES, blend_dna_profiles, normalize_dna

def generate_unit_blueprint(unit_class, faction, name, tier, cost, domain):
    # Load faction DNA
    faction_dna_path = r"universes/eternal_crusade/factions/faction_dna.json"
    faction_dna = {}
    
    if os.path.exists(faction_dna_path):
        with open(faction_dna_path, 'r', encoding='utf-8') as f:
            faction_dna_db = json.load(f)
            faction_dna = faction_dna_db.get(faction, {})
    
    class_dna = UNIT_CLASSES.get(unit_class, {})
    
    # Blend DNA
    final_dna = blend_dna_profiles(class_dna, faction_dna, class_weight=0.5)
    
    # Create blueprint
    blueprint = {
        "name": name,
        "blueprint_id": f"{faction.lower().replace(' ', '_')}_{name.lower().replace(' ', '_')}",
        "type": "ship" if domain == "space" else "infantry" if "infantry" in unit_class else "vehicle",
        "unit_class": unit_class,
        "domain": domain,
        "faction": faction,
        "tier": tier,
        "cost": cost,
        "base_stats": {
            "role": unit_class,
            "tier": tier,
            "hp": 100 + (tier * 100),  # Placeholder
            "armor": 20 + (tier * 10),
            "damage": 10 + (tier * 5),
            "speed": 30 if domain == "space" else 6,
            "cost": cost,
            "keywords": f"{unit_class} {domain} tier{tier}"
        },
        "elemental_dna": final_dna,
        "source_universe": "eternal_crusade",
        "description": f"{faction} {unit_class}",
        "traits": []
    }
    
    return blueprint

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="unit_class", required=True, help="Unit class (e.g., fighter)")
    parser.add_argument("--faction", required=True, help="Faction name")
    parser.add_argument("--name", required=True, help="Unit name")
    parser.add_argument("--tier", type=int, required=True, help="Tier (0-6)")
    parser.add_argument("--cost", type=int, required=True, help="Resource cost")
    parser.add_argument("--domain", required=True, choices=["space", "ground"])
    
    args = parser.parse_args()
    
    blueprint = generate_unit_blueprint(
        args.unit_class, args.faction, args.name, args.tier, args.cost, args.domain
    )
    
    print(json.dumps(blueprint, indent=2))
