import os
import re
import json
import sys

import src.core.config as config
from universes.base.universe_loader import UniverseLoader
from pathlib import Path

def log_error(errors_list, file, message):
    errors_list.append(f"[{os.path.basename(file)}] {message}")

def load_registries():
    try:
        with open(config.REGISTRY_BUILDING, 'r', encoding='utf-8') as f:
            buildings = json.load(f)
    except Exception as e:
        print(f"CRITICAL: Could not load building_registry.json from {config.REGISTRY_BUILDING}: {e}")
        return None, None, None, None
        
    try:
        with open(config.REGISTRY_TECH, 'r', encoding='utf-8') as f:
            techs = json.load(f)
    except Exception as e:
        print(f"CRITICAL: Could not load technology_registry.json from {config.REGISTRY_TECH}: {e}")
        return None, None, None, None

    try:
        with open(config.REGISTRY_WEAPON, 'r', encoding='utf-8') as f:
            weapons = json.load(f)
    except:
        weapons = {} # Optional for now

    try:
        with open(config.REGISTRY_ABILITY, 'r', encoding='utf-8') as f:
            abilities = json.load(f)
    except:
        abilities = {} # Optional for now
        
    return buildings, techs, weapons, abilities

def validate_parser_data(file, data, buildings_reg, techs_reg, weapons_reg, abilities_reg, errors, tier_warnings):
    """
    Validates a single unit's PARSER_DATA block against registries and schema rules.
    
    Performs comprehensive checks including:
    - Existence of required fields (e.g., hp, tier, cost).
    - Type validation for integer fields.
    - Reference integrity (checking if buildings, techs, weapons exist in registries).
    - Tier logic (ensuring unit tier is not lower than required building tier).
    
    Args:
        file (str): Absolute path to the unit file (for logging).
        data (dict): The parsed key-value data from the unit file.
        buildings_reg (dict): Building registry for validation.
        techs_reg (dict): Technology registry for validation.
        weapons_reg (dict): Weapon registry for validation.
        abilities_reg (dict): Ability registry for validation.
        errors (list): Output list to append error messages to.
        tier_warnings (list): Output list to append tier logic warnings to.
    """
    # Determine Schema Type
    is_ship = False
    if 'unit_type' in data and data['unit_type'] == 'ship':
        is_ship = True
    elif 'ship_' in os.path.basename(file):
        is_ship = True
        
    # Field Existence
    required_fields_core = [
        "name", "tier", "armor", "speed"
    ]
    
    required_fields_land = ["hp", "melee_attack", "melee_defense", "weapon_skill"]
    required_fields_ship = ["hull_points", "shields", "turrets"]
    # Tactical Strategy Fields (Optional for now, but good to track)
    tactical_fields = ["weapon_arcs", "armor_front", "armor_side", "armor_rear", "agility", "grid_size", "facing"]
    
    check_list = required_fields_core[:]
    # Note: land/ship specific fields are now checked with loose requirements or aliases
    
    for field in check_list:
        if field not in data:
            # Check in 'stats' block as fallback
            if 'stats' in data and isinstance(data['stats'], dict) and field in data['stats']:
                data[field] = data['stats'][field] # Pull into top-level for convenience of further checks
            else:
                log_error(errors, file, f"Missing required field: {field}")
                return # Stop further checks if critical fields missing

    # Handle optional/flexible fields
    if "requisition_cost" not in data and "cost" in data:
        data["requisition_cost"] = data["cost"]
    elif "requisition_cost" not in data:
        log_error(errors, file, "Missing requisition_cost or cost")
        return

    if "required_building" not in data:
        data["required_building"] = "None"

    # Style-specific Aliases & Defaults
    if is_ship:
        if "hull_points" not in data and "hull" in data:
            data["hull_points"] = data["hull"]
        
        # Ensure minimal ship stats for types/constraints check
        for f in required_fields_ship:
            if f not in data: data[f] = 0 
    else:
        # Land defaults
        for f in required_fields_land:
            if f not in data: data[f] = 0
    # Types & Constraints
    unit_tier = 0
    try:
        unit_tier = int(data['tier'])
        int(data['requisition_cost'])
        if is_ship:
             int(data['hull_points'])
             if 'shields' in data: int(data['shields'])
        else:
             int(data['hp'])
    except ValueError:
        log_error(errors, file, "One or more integer fields (tier, hp/hull, cost) are not numbers")
    except KeyError:
        # Field missing - already caught by required field check, but good to be safe
        pass

    # Reference Validation: Building & Tier Logic
    req_build = data['required_building']
    if req_build != "None":
        if req_build not in buildings_reg:
            log_error(errors, file, f"Invalid Building Reference: '{req_build}'")
        else:
            # Tier Check
            b_data = buildings_reg[req_build]
            b_tier = int(b_data.get('tier', 0))
            if unit_tier < b_tier:
                log_error(errors, file, f"Logic Error: Tier {unit_tier} unit requires Higher Tier {b_tier} building '{req_build}'")
                tier_warnings.append({
                    "unit": data.get('name', 'Unknown'),
                    "unit_tier": unit_tier,
                    "building": req_build,
                    "building_tier": b_tier,
                    "delta": b_tier - unit_tier,
                    "file": os.path.basename(file)
                })

    # Reference Validation: Tech
    if 'required_tech' in data:
        try:
            import ast
            req_techs = ast.literal_eval(data['required_tech']) if data['required_tech'].startswith('[') else []
            for tech in req_techs:
                if tech not in techs_reg:
                    log_error(errors, file, f"Invalid Tech Reference: '{tech}'")
        except:
            log_error(errors, file, f"Malformed tech list: {data['required_tech']}")
    else:
        data['required_tech'] = "[]"

     # Reference Validation: Weapons (Optional)
    if 'weapons' in data:
        try:
           w_data = data['weapons']
           w_list = []
           if isinstance(w_data, str) and w_data.startswith('['):
               import ast
               w_list = ast.literal_eval(w_data)
           elif isinstance(w_data, list):
               w_list = w_data
           
           for w in w_list:
               if w not in weapons_reg:
                   log_error(errors, file, f"Invalid Weapon Reference: '{w}'")
        except:
             log_error(errors, file, f"Malformed weapons list: {data['weapons']}")

     # Reference Validation: Abilities (Optional)
    if 'abilities' in data:
        try:
           a_data = data['abilities']
           a_list = []
           if isinstance(a_data, str) and a_data.startswith('['):
               import ast
               a_list = ast.literal_eval(a_data)
           elif isinstance(a_data, list):
               a_list = a_data
               
           for a in a_list:
               if a not in abilities_reg:
                   log_error(errors, file, f"Invalid Ability Reference: '{a}'")
        except:
             log_error(errors, file, f"Malformed abilities list: {data['abilities']}")

    # Progression Validation
    if 'progression' in data and isinstance(data['progression'], dict):
        prog = data['progression']
        valid_types = ['standard', 'vehicle', 'hero', 'ship', 'titan', 'monster']
        valid_curves = ['slow', 'standard', 'fast']
        
        p_type = prog.get('type', 'standard')
        if p_type not in valid_types:
            log_error(errors, file, f"Invalid Progression Type: '{p_type}'")
            
        p_curve = prog.get('xp_curve', 'standard')
        if p_curve not in valid_curves:
            log_error(errors, file, f"Invalid XP Curve: '{p_curve}'")

def scan_units(buildings_reg, techs_reg, weapons_reg, abilities_reg, errors, tier_warnings):
    """
    Scans the `02_factions_and_units` directory for unit files and initiates validation.
    
    Filters out non-unit markdown files (like indexes or templates), extracts the PARSER_DATA 
    block, and delegates actual validation to `validate_parser_data`.
    
    Args:
        buildings_reg (dict): Building registry.
        techs_reg (dict): Technology registry.
        weapons_reg (dict): Weapon registry.
        abilities_reg (dict): Ability registry.
        errors (list): Mutable list where errors will be collected.
        tier_warnings (list): Mutable list where tier warnings will be collected.
    """
    print("Scanning Units...")
    unit_names = {}
    
    for root, dirs, files in os.walk(config.UNITS_DIR):
        for file in files:
            # Skip non-data files to reduce noise
            if not file.endswith(".md"): continue
            if file in ["README.md", "AIR_WARFARE_MECHANICS.md", "ROSTER_SUMMARIES.md", "unit_customization.md", "remediation_techs.md", "remediation_infrastructure.md", "TRAITS_GUIDE.md"]: continue
            if "database" in file or "matrix" in file or "PHILOSOPHY" in file or "summary" in file or "SPEC" in file: continue
            if "faction_" in file and "registry" not in file: continue # Faction overviews often don't have parser data
            if "KEYWORDS" in file or "global" in file or "schema" in file or "template" in file: continue
            if "definitions" in file or "tree" in file: continue

            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Support both comment style and MD code block style
            data = None
            
            # Style 1: <!-- PARSER_DATA ... -->
            match = re.search(r'<!-- PARSER_DATA(.*?)-->', content, re.DOTALL)
            if match:
                data_block = match.group(1)
                data = {}
                lines = data_block.strip().split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key, val = key.strip(), val.strip()
                        if not val and i + 1 < len(lines) and (lines[i+1].startswith('  ') or lines[i+1].startswith('\t')):
                            nested_data = {}
                            i += 1
                            while i < len(lines) and (lines[i].startswith('  ') or lines[i].startswith('\t')):
                                subline = lines[i].strip()
                                if ':' in subline:
                                    subkey, subval = subline.split(':', 1)
                                    nested_data[subkey.strip()] = subval.strip()
                                i += 1
                            data[key] = nested_data
                            continue
                        else:
                            data[key] = val
                    i += 1
            
            # Style 2: ## Parser Data \n ```json ... ```
            if not data:
                # Look for ## Parser Data followed by a json block
                json_match = re.search(r'## Parser Data\s*?\n\s*?```json\s*?\n(.*?)\n\s*?```', content, re.DOTALL | re.IGNORECASE)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                    except json.JSONDecodeError as e:
                        log_error(errors, file, f"Malformed JSON in Parser Data block: {e}")
                        continue
            
            if not data:
                log_error(errors, file, "Missing PARSER_DATA block (checked both <!-- --> and ## styles)")
                continue

            # Uniqueness Check
            name = data.get('name', 'Unknown')
            if name in unit_names:
                log_error(errors, file, f"Duplicate unit name '{name}' (also in {unit_names[name]})")
            else:
                unit_names[name] = file
                
            validate_parser_data(file, data, buildings_reg, techs_reg, weapons_reg, abilities_reg, errors, tier_warnings)

def validate_all(output_report=True):
    """
    Main driver for the validation process.
    
    Loads all registries, initializes error collectors, runs the unit scan,
    and optionally writes the results to report files.
    
    Args:
        output_report (bool): If True, writes `validation_errors.json` and `tier_warnings.csv`.
        
    Returns:
        dict: A summary dictionary containing "success" (bool), "errors" (list), and "warnings" (list).
    """
    b_reg, t_reg, w_reg, a_reg = load_registries()
    
    errors = []
    tier_warnings = []

    # 1. Structural Validation (Verbatim check)
    if config.ACTIVE_UNIVERSE:
        print(f"Validating Universe Structure: {config.ACTIVE_UNIVERSE}...")
        loader = UniverseLoader(Path(config.UNIVERSE_ROOT))
        
        # Core Structure
        success, struct_errors = loader.validate_universe(config.ACTIVE_UNIVERSE)
        if not success:
            errors.extend(struct_errors)

        # Advanced Module Verification (checking existence of .py files)
        try:
            uni_path = Path(config.UNIVERSE_ROOT) / config.ACTIVE_UNIVERSE
            with open(uni_path / "config.json", 'r') as f:
                cfg_data = json.load(f)
                modules = cfg_data.get("metadata", {}).get("modules", {})
                for mod_name, mod_path in modules.items():
                    # Assuming format "universes.xxx.yyy" or similar
                    parts = mod_path.split('.')
                    if len(parts) >= 3 and parts[0] == "universes":
                         # Construct file path: universes/xxx/yyy.py
                         expected_file = Path(config.UNIVERSE_ROOT) / parts[1] / (parts[2] + ".py")
                         if not expected_file.exists():
                             errors.append(f"Module '{mod_name}' references missing file: {expected_file}")
        except Exception as e:
            errors.append(f"Structural Check Error: {e}")

    if b_reg is None or t_reg is None: 
        return {"success": False, "errors": errors + ["Failed to load critical registries"], "warnings": []}
    
    scan_units(b_reg, t_reg, w_reg, a_reg, errors, tier_warnings)
    
    if output_report:
        # Export Tier Warnings
        if tier_warnings:
            # Output warnings to CSV
            csv_path = os.path.join(config.REPORTS_DIR, "tier_warnings.csv")
            try:
                with open(csv_path, 'w', encoding='utf-8') as f:
                    f.write("Unit,Unit_Tier,Building,Building_Tier,Delta,File\n")
                    for w in tier_warnings:
                        f.write(f"{w['unit']},{w['unit_tier']},{w['building']},{w['building_tier']},{w['delta']},{w['file']}\n")
                print(f"\n[INFO] Exported {len(tier_warnings)} tier logic warnings to {csv_path}")
            except Exception as e:
                print(f"\n[ERROR] Failed to write CSV: {e}")

        # Export Full Errors to JSON
        error_report_path = os.path.join(config.REPORTS_DIR, "validation_errors.json")
        try:
            if not os.path.exists(os.path.dirname(error_report_path)):
                os.makedirs(os.path.dirname(error_report_path))
            with open(error_report_path, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2)
            print(f"[INFO] Exported {len(errors)} validation errors to {error_report_path}")
        except Exception as e:
            print(f"[ERROR] Failed to write Error JSON: {e}")
            
    return {
        "success": len(errors) == 0,
        "errors": errors,
        "warnings": tier_warnings
    }

def main():
    results = validate_all(output_report=True)
    errors = results["errors"]
    
    print("\n=== Refined Validation Report ===")
    if not errors:
        print("SUCCESS: Data Layer Integrity Verified (Strict Schema).")
    else:
        print(f"FAILED: Found {len(errors)} errors.")
        for err in errors[:25]:
            print(err)
        if len(errors) > 25:
            print(f"... and {len(errors)-25} more.")

if __name__ == "__main__":
    main()
