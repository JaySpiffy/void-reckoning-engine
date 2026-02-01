import sys
import os
import json
import re
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.eaw_structure_parser import EaWStructureParser
from src.core.config import ROOT_DIR, UNIVERSE_ROOT

def link_units():
    mod_root = os.path.join(ROOT_DIR, "examples_only", "star wars")
    parser = EaWStructureParser(mod_root)
    structures = parser.get_all_structures()
    
    # Map Unit -> Building
    unit_to_building = {}
    
    print("Building Unit->Structure map...")
    for s_name, data in structures.items():
        if "unlocks" in data:
            for u in data["unlocks"]:
                # If unit already mapped, maybe keep lower tier or first found?
                # EaW can have multiple buildings unlock same unit (e.g. diff factions)
                # For now just take the first one found or overwrite
                unit_to_building[u] = {
                    "building": s_name,
                    "tier": data["tier"]
                }
                
    # Save Registry
    universe_sw = Path(UNIVERSE_ROOT) / "star_wars"
    reg_path = universe_sw / "factions" / "unit_building_requirements.json"
    
    with open(reg_path, 'w', encoding='utf-8') as f:
        json.dump(unit_to_building, f, indent=4)
        
    print(f"Saved requirements for {len(unit_to_building)} units to {reg_path}")
    
    # Update Markdown Files
    factions_dir = universe_sw / "factions"
    updated_count = 0
    
    for root, _, files in os.walk(factions_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                
                # Check parser data to get unit ID
                # We need to parse valid JSON block
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if not json_match: continue
                
                try:
                    data = json.loads(json_match.group(1))
                    u_id = data.get("id")
                    if not u_id or u_id not in unit_to_building: continue
                    
                    req_info = unit_to_building[u_id]
                    
                    # Update data
                    if data.get("required_building") == req_info["building"]:
                        continue # Already updated
                        
                    data["required_building"] = req_info["building"]
                    data["tech_tier"] = req_info["tier"]
                    
                    # Write back
                    new_json = json.dumps(data, indent=4)
                    new_content = content.replace(json_match.group(1), new_json)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    updated_count += 1
                except:
                    pass
                    
    print(f"Updated {updated_count} markdown files with building requirements.")

if __name__ == "__main__":
    link_units()
