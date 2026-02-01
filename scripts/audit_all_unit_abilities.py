
import os
import re
import json
import sys

# Setup Path
sys.path.append(os.getcwd())

from src.core.universe_data import UniverseDataManager
from src.factories.unit_factory import UnitFactory

TARGET_DIRS = [
    r"universes/warhammer40k_atomic",
    r"universes/star_wars_atomic",
    r"universes/star_trek_atomic"
]

def audit_abilities():
    print("Starting Global Atomic Ability Audit...")
    
    # 1. Load Registry
    udm = UniverseDataManager.get_instance()
    # We need to manually initialize if not in a campaign context
    # But get_ability_database loads the base registry automatically
    ability_db = udm.get_ability_database()
    print(f"Registry loaded with {len(ability_db)} atomic definitions.")
    
    stats = {
        "total_units": 0,
        "total_ability_slots": 0,
        "mapped_slots": 0,
        "missing_abilities": set(),
        "unmapped_units": []
    }
    
    factory = UnitFactory()
    
    for dir_path in TARGET_DIRS:
        if not os.path.exists(dir_path):
            print(f"Warning: Directory not found: {dir_path}")
            continue
            
        print(f"Auditing Universe: {dir_path}...")
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith(".md"): continue
                
                path = os.path.join(root, file)
                # Use factory to parse properly (handles JSON and Markdown)
                try:
                    unit = factory.create_from_file(path, faction="Audit")
                    if not unit: continue
                    
                    stats["total_units"] += 1
                    unit_has_unmapped = False
                    
                    for ab_key in unit.abilities:
                        # Skip tags
                        if ab_key in ["Tags", "Infantry", "Vehicle", "Monster", "Core"]: continue
                        
                        stats["total_ability_slots"] += 1
                        
                        # Normalize key
                        clean_key = ab_key.lower().replace(" ", "_").replace("-", "_")
                        
                        if clean_key in ability_db:
                            stats["mapped_slots"] += 1
                        else:
                            stats["missing_abilities"].add(ab_key)
                            unit_has_unmapped = True
                            
                    if unit_has_unmapped:
                        stats["unmapped_units"].append(unit.name)
                        
                except Exception as e:
                    # print(f"Error parsing {file}: {e}")
                    pass

    print("\n--- AUDIT RESULTS ---")
    print(f"Total Units Scanned: {stats['total_units']}")
    print(f"Total Ability Slots Found: {stats['total_ability_slots']}")
    print(f"Mapped to Atomic DNA: {stats['mapped_slots']} ({ (stats['mapped_slots']/(stats['total_ability_slots'] or 1))*100:.1f}%)")
    print(f"Missing from Registry: {len(stats['missing_abilities'])}")
    
    if stats["missing_abilities"]:
        print("\nTop Missing Abilities (Sample):")
        for ab in list(stats["missing_abilities"])[:20]:
            print(f"  - {ab}")
            
    print("\nAudit Complete.")

if __name__ == "__main__":
    audit_abilities()
