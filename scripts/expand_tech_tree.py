
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
TECH_DIR = BASE_DIR / "universes" / "eternal_crusade" / "technology"

def expand_tech_tree():
    nodes = [
        # Tier 1
        {"id": "Tech_Basic_Doctrine", "label": "Basic Doctrine", "tier": 1, "cost": 1000, "category": "military"},
        {"id": "Tech_Logistics", "label": "Logistics", "tier": 1, "cost": 1000, "category": "psychic"},
        {"id": "Tech_Industrial_Forging", "label": "Industrial Forging", "tier": 1, "cost": 800, "category": "industry"},
        {"id": "Tech_Resource_Extraction", "label": "Resource Extraction", "tier": 1, "cost": 800, "category": "economy"},
        
        # Tier 2
        {"id": "Tech_Heavy_Armor", "label": "Heavy Armor", "tier": 2, "cost": 2500, "category": "military"},
        {"id": "Tech_Advanced_Ballistics", "label": "Advanced Ballistics", "tier": 2, "cost": 2500, "category": "military"},
        {"id": "Tech_Warp_Navigation", "label": "Warp Navigation", "tier": 2, "cost": 3000, "category": "psychic"},
        {"id": "Tech_Mega_Construction", "label": "Mega Construction", "tier": 2, "cost": 2500, "category": "industry"},
        {"id": "Tech_Trade_Networks", "label": "Trade Networks", "tier": 2, "cost": 2000, "category": "economy"},
        
        # Tier 3
        {"id": "Tech_Capital_Ships", "label": "Capital Ships", "tier": 3, "cost": 5000, "category": "military"},
        {"id": "Tech_Titan_Integration", "label": "Titan Integration", "tier": 3, "cost": 6000, "category": "psychic"},
        {"id": "Tech_Planetary_Shielding", "label": "Planetary Shielding", "tier": 3, "cost": 4500, "category": "industry"},
        {"id": "Tech_Ascension_Protocol", "label": "Ascension Protocol", "tier": 3, "cost": 8000, "category": "economy"}
    ]

    edges = [
        # T1 -> T2
        {"from": "Tech_Basic_Doctrine", "to": "Tech_Heavy_Armor"},
        {"from": "Tech_Basic_Doctrine", "to": "Tech_Advanced_Ballistics"},
        {"from": "Tech_Logistics", "to": "Tech_Warp_Navigation"},
        {"from": "Tech_Industrial_Forging", "to": "Tech_Mega_Construction"},
        {"from": "Tech_Resource_Extraction", "to": "Tech_Trade_Networks"},
        
        # T2 -> T3 (Cross-linking)
        {"from": "Tech_Heavy_Armor", "to": "Tech_Capital_Ships"},
        {"from": "Tech_Warp_Navigation", "to": "Tech_Capital_Ships"},
        
        {"from": "Tech_Advanced_Ballistics", "to": "Tech_Titan_Integration"},
        {"from": "Tech_Mega_Construction", "to": "Tech_Titan_Integration"},
        
        {"from": "Tech_Mega_Construction", "to": "Tech_Planetary_Shielding"},
        {"from": "Tech_Heavy_Armor", "to": "Tech_Planetary_Shielding"},
        
        {"from": "Tech_Trade_Networks", "to": "Tech_Ascension_Protocol"},
        {"from": "Tech_Logistics", "to": "Tech_Ascension_Protocol"} # Link T1 to T3? No, T2 usually.
    ]
    
    # Correction: Link T2 to T3 Ascension
    # Let's link Warp Nav to Ascension as well
    edges[-1] = {"from": "Tech_Warp_Navigation", "to": "Tech_Ascension_Protocol"}

    tree = {
        "nodes": nodes,
        "edges": edges
    }

    with open(TECH_DIR / "tech_tree.json", 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=4)
        print(f"Expanded tech_tree.json with {len(nodes)} nodes and {len(edges)} edges.")

if __name__ == "__main__":
    expand_tech_tree()
