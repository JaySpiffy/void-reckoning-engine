import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import ROOT_DIR
from src.utils.stellaris_country_parser import StellarisCountryParser

def main():
    mod_root = os.path.join(ROOT_DIR, "examples_only", "star_trak", "common")
    if not os.path.exists(mod_root):
        mod_root = "examples_only/star_trak/common"
    
    parser = StellarisCountryParser(mod_root)
    print(f"Parsing countries from {mod_root}...")
    
    data = parser.parse_all_country_types()
    
    print(f"Found {len(data)} country types.")
    
    # Dump to file for inspection
    out_path = os.path.join(ROOT_DIR, "universes", "star_trek", "parsed_country_types.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Saved parsed data to {out_path}")

if __name__ == "__main__":
    main()
