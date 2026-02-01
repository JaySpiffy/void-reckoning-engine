
import argparse
import sys
import os
import json
import random
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.unit_parser import load_all_units
from src.core.physics_calibrator import PhysicsCalibrator
from src.core.config import UNIVERSE_ROOT

def main():
    parser = argparse.ArgumentParser(description="Auto-calibrate Physics Profile for a Universe")
    parser.add_argument("--universe", required=True, help="Name of the universe (folder in universes/)")
    parser.add_argument("--output", help="Custom output path (defaults to universes/{name}/physics_profile.json)")
    parser.add_argument("--validate", action="store_true", help="Run validation after calibration")
    parser.add_argument("--dry-run", action="store_true", help="Do not save changes, just print report")
    parser.add_argument("--min-units", type=int, default=20, help="Minimum units required (default 20)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    
    print(f"Loading units for universe: {args.universe}...")
    
    # 1. Load Units
    # load_all_units returns Dict[faction, List[Unit]]
    all_units_map = load_all_units(args.universe)
    
    # Flatten list
    units = []
    for faction_units in all_units_map.values():
        units.extend(faction_units)
        
    print(f"Found {len(units)} units total.")
    
    # Filter for DNA
    valid_units = [u for u in units if u.elemental_dna]
    print(f"Units with Elemental DNA: {len(valid_units)}")
    
    if len(valid_units) < args.min_units:
        print(f"ERROR: Insufficient units for calibration. Need {args.min_units}, found {len(valid_units)}.")
        sys.exit(1)
        
    # 2. Calibrate
    print("Running calibration analysis...")
    profile, metadata = PhysicsCalibrator.calibrate(valid_units, args.universe)
    
    # 3. Validate
    sample_units = []
    if args.validate:
        # Pick random sample
        sample_size = min(10, len(valid_units))
        sample_units = random.sample(valid_units, sample_size)
    
    validation_report = PhysicsCalibrator.validate_calibration(profile, sample_units)
    
    # 4. Report
    report = PhysicsCalibrator.generate_report(profile, metadata, validation_report)
    print("\n" + report + "\n")
    
    if args.dry_run:
        print("Dry run completed. No files saved.")
        return

    # 5. Save
    if args.output:
        out_path = args.output
    else:
        # Default: universes/{name}/physics_profile.json
        uni_dir = os.path.join(UNIVERSE_ROOT, args.universe)
        if not os.path.exists(uni_dir):
            print(f"Warning: Universe directory {uni_dir} does not exist. Saving to current directory.")
            out_path = "physics_profile.json"
        else:
            out_path = os.path.join(uni_dir, "physics_profile.json")
            
    print(f"Saving profile to {out_path}...")
    
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    
    # Logic to decide if we wrap in universe key or write flat
    # Heuristic: If filename is 'physics_profiles.json' (plural) or located in base/, assumes shared.
    # User comment: "When targeting the shared universes/base/physics_profiles.json ... wrap under universe key. Otherwise flat."
    # Also "per-universe files remain flat".
    
    is_shared_file = False
    if "base" in out_path.replace("\\", "/").split("/") or "physics_profiles.json" in os.path.basename(out_path):
         is_shared_file = True
    
    # Prepare Profile Data
    profile_data = profile.to_dict()
    # Merge metadata (excluding transient large objects)
    profile_data.update({k: v for k, v in metadata.items() if k not in ["distributions", "archetype"]})
    profile_data["archetype"] = metadata.get("archetype")
    
    if is_shared_file:
        data_to_write = {}
        if os.path.exists(out_path):
            try:
                with open(out_path, 'r', encoding='utf-8') as f:
                    data_to_write = json.load(f)
            except:
                data_to_write = {}
        
        data_to_write[args.universe] = profile_data
        
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_write, f, indent=2)
            
    else:
        # Per-universe file: Write flat dictionary directly
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2)
        
    print("Success.")

if __name__ == "__main__":
    main()
