
import os
import json
from pathlib import Path
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.utils.portal_validator import PortalValidator

def main():
    print("=== Multi-Universe Portal Network Validator ===")
    universes_root = Path("universes")
    
    # 1. Discover universes with portal configs
    universes = [d.name for d in universes_root.iterdir() if d.is_dir() and (d / "portal_config.json").exists()]
    print(f"Discovered {len(universes)} universes with portal configurations: {', '.join(universes)}")
    
    # 2. Structural Validation
    all_valid = True
    portal_data = {}
    for uni in universes:
        config_path = universes_root / uni / "portal_config.json"
        res = PortalValidator.validate_portal_config(config_path)
        if not res["valid"]:
            print(f"[ERROR] {uni}: {res['error']}")
            all_valid = False
        else:
            portal_data[uni] = res["data"]["portals"]
            
    if not all_valid:
        print("\n[FAIL] Structural validation failed. Fix JSON errors before proceeding.")
        return

    # 3. Bidirectional Consistency Check
    print("\nChecking Bidirectional Consistency...")
    consistency_errors = []
    links_checked = set()
    
    for uni_a, portals_a in portal_data.items():
        for p_a in portals_a:
            uni_b = p_a["dest_universe"]
            p_id = p_a["portal_id"]
            
            # Skip if we already checked this specific link pair
            link_key = tuple(sorted([f"{uni_a}:{p_id}", f"{uni_b}:{p_id}"]))
            if link_key in links_checked:
                continue
            
            # Check if destination exists in our set
            if uni_b not in portal_data:
                # We might be linking to a universe that isn't enabled or is missing config
                # But for this network, all should be present
                consistency_errors.append(f"Portal '{p_id}' in {uni_a} targets {uni_b}, but {uni_b} has no portal_config.json")
                continue
                
            # Find matching portal in B
            matching_p = next((p for p in portal_data[uni_b] if p["portal_id"] == p_id and p["dest_universe"] == uni_a), None)
            
            if not matching_p:
                consistency_errors.append(f"Portal '{p_id}' in {uni_a} targets {uni_b}, but no matching portal found in {uni_b}")
            else:
                # Coordinate Check
                if p_a["source_coords"] != matching_p["dest_coords"]:
                    consistency_errors.append(f"Coord Mismatch [{p_id}]: {uni_a}.source {p_a['source_coords']} != {uni_b}.dest {matching_p['dest_coords']}")
                if p_a["dest_coords"] != matching_p["source_coords"]:
                    consistency_errors.append(f"Coord Mismatch [{p_id}]: {uni_a}.dest {p_a['dest_coords']} != {uni_b}.source {matching_p['source_coords']}")
            
            links_checked.add(link_key)

    if consistency_errors:
        print("\n[FAIL] Consistency checks failed:")
        for err in consistency_errors:
            print(f"  - {err}")
    else:
        print("\n[SUCCESS] Portal network is structurally sound and consistent!")
        
    print("\n" + PortalValidator.generate_portal_report(universes_root))

if __name__ == "__main__":
    main()
