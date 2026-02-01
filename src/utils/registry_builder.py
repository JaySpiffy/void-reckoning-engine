import os
import re
import json
import sys
from typing import Dict

import src.core.config as config
from src.utils.registry_schemas import (
    RegistrySchema, BUILDING_SCHEMA, TECH_SCHEMA,
    _standardize_building_entry, _standardize_tech_entry
)

from src.generators.procedural_registry_generator import generate_ship_roster, generate_land_roster
# Alias for backward compatibility
generate_procedural_roster = generate_ship_roster

class RegistryBuilderError(Exception):
    """Base exception for registry building errors."""
    pass

def safe_registry_save(path: str, data: Dict, verbose: bool = True) -> None:
    """Safely saves registry data to JSON with error handling."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        if verbose: print(f"Saved {len(data)} entries to {path}")
    except Exception as e:
        raise RegistryBuilderError(f"Failed to save registry to {path}: {e}")

def run_integration(name: str, callback, verbose: bool = True) -> None:
    """Executes an integration callback with standardized error handling."""
    try:
        callback()
    except ImportError:
        pass # Optional dependency missing
    except Exception as e:
        if verbose: print(f"WARNING: Integration '{name}' failed: {e}")
        # We generally don't raise here to allow partial builds, but we log it.

# Keep other standardizers for now if they aren't in schemas yet, 
# or import them if I moved them. I only moved Building/Tech.
# Re-implement others or keep them? 
# The plan focused on Building/Tech. I'll keep the others here for now.

def _standardize_faction_entry(data: dict) -> dict:
    return {
        "id": data.get("id", "unknown"),
        "name": data.get("name", "Unknown"),
        "quirks": data.get("quirks", {}),
        "subfactions": data.get("subfactions", []),
        "government_type": data.get("government_type", "unknown"),
        "ethics": data.get("ethics", []),
        "civics": data.get("civics", []),
        "starting_resources": data.get("starting_resources", {}),
        "source_file": data.get("source_file", "config"),
        "source_format": data.get("source_format", "config"),
        "personality_id": data.get("personality_id"),
        "unit_files": data.get("unit_files", [])
    }

def _standardize_weapon_entry(data: dict) -> dict:
    return {
        "id": data.get("id", "unknown"),
        "name": data.get("name", "Unknown"),
        "category": data.get("category", "General"),
        "stats": data.get("stats", {}),
        "tags": data.get("tags", []),
        "source_file": data.get("source_file", "unknown"),
        "source_format": data.get("source_format", "unknown")
    }

def _standardize_ability_entry(data: dict) -> dict:
    return {
        "id": data.get("id", "unknown"),
        "name": data.get("name", "Unknown"),
        "description": data.get("description", ""),
        "effect": data.get("effect", ""),
        "stats": data.get("stats", {}),
        "source_file": data.get("source_file", "unknown"),
        "source_format": data.get("source_format", "unknown")
    }

def _parse_markdown_files(universe_path: str, schema: RegistrySchema) -> Dict[str, dict]:
    """Generic markdown parser using schema strategy."""
    registry = {}
    
    # Locate Directory
    search_dirs = [os.path.join(universe_path, d) for d in schema.source_dirs]
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir): continue
        
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if not file.endswith(".md"): continue
                if "cost_table" in file: continue # Specific exclude
                
                path = os.path.join(root, file)
                faction = get_faction_from_path(path, universe_path)
                # print(f"Processing {file} -> Faction: {faction}") # Enable this if needed
                
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Strategy: Regex Block (Building Style)
                if "simple_tier" in schema.regex_patterns:
                    # Pattern 1
                    for m in re.finditer(schema.regex_patterns["simple_tier"], content):
                        tier = int(m.group(1))
                        name = m.group(2).split('(')[0].strip()
                        if name not in registry:
                            registry[name] = {"id": name, "tier": tier, "faction": faction, "source_file": file}
                            
                    # Pattern 2 (Complex)
                    if "complex_block" in schema.regex_patterns:
                        for m in re.finditer(schema.regex_patterns["complex_block"], content, re.DOTALL):
                            tier = int(m.group(1))
                            name = m.group(2).strip()
                            body = m.group(3)
                            
                            entry = {
                                "id": f"{faction}_{name}" if faction and faction != "Global" else name,
                                "name": name,
                                "tier": tier,
                                "faction": faction,
                                "source_file": file
                            }
                            
                            # Extract extra fields
                            if "body_fields" in schema.regex_patterns:
                                for field, pattern in schema.regex_patterns["body_fields"].items():
                                    match = re.search(pattern, body, re.DOTALL)
                                    if match:
                                        val = match.group(1).strip()
                                        if field in ["cost", "maintenance"]:
                                            entry[field] = int(val)
                                        elif field == "unlocks":
                                            entry[field] = [u.strip() for u in val.split(',')]
                                        elif field == "prerequisites":
                                            # Remove brackets and split
                                            clean = val.replace('[', '').replace(']', '')
                                            if clean.lower() == "none" or not clean:
                                                entry[field] = []
                                            else:
                                                entry[field] = [p.strip() for p in clean.split(',')]
                                        elif field == "effects": # specific dict handling
                                            entry["effects"] = {"description": val}
                                        else:
                                            entry[field] = val
                                            
                            if entry["id"] not in registry:
                                registry[entry["id"]] = entry

                # Strategy: Stateful Line (Tech Style)
                elif "tier_header" in schema.regex_patterns:
                    lines = content.splitlines()
                    current_tier = 1
                    current_id = None
                    
                    for line in lines:
                        # Context Update
                        t_match = re.search(schema.regex_patterns["tier_header"], line)
                        if t_match:
                            current_tier = int(t_match.group(1))
                            continue
                            
                        # Item Start
                        i_match = re.search(schema.regex_patterns["item_header"], line)
                        if i_match:
                            name = i_match.group(1).strip()
                            reg_id = f"Tech_{faction}_{name}" if faction and faction != "Global" else f"Tech_{name}"
                            current_id = reg_id
                            # print(f"[DEBUG] Found Tech Item: {name} (ID: {reg_id}) in {file}") 
                            if reg_id not in registry:
                                registry[reg_id] = {
                                    "id": reg_id,
                                    "name": name,
                                    "tier": current_tier,
                                    "faction": faction,
                                    "source_file": file,
                                    "unlocks_buildings": [],
                                    "unlocks_ships": []
                                }
                            continue
                            
                        # Body Fields
                        if current_id and "body_fields" in schema.regex_patterns:
                            for field, pattern in schema.regex_patterns["body_fields"].items():
                                match = re.search(pattern, line)
                                if match:
                                    val = match.group(1).strip()
                                    if field == "cost":
                                        registry[current_id]["cost"] = int(val)
                                    elif field == "effects":
                                        registry[current_id]["effects"] = {"description": val}
                                    elif field == "unlocks_inference":
                                        # Specific Logic for Unlocks Inference
                                        target = val
                                        if any(k in target.lower() for k in ["ship", "fleet", "cruiser", "escort"]):
                                             registry[current_id]["unlocks_ships"].append(target)
                                        else:
                                             registry[current_id]["unlocks_buildings"].append(target)
                                    else:
                                        registry[current_id][field] = val
                                        
    return registry


def _build_generic_registry(universe_path: str, schema: RegistrySchema, verbose: bool = True):
    """Generic builder engine."""
    name = schema.name
    if verbose: print(f"Building {name} Registry...")
    
    # 1. Parse Core Files
    registry = _parse_markdown_files(universe_path, schema)
    
    # 2. Hooks / Integrations (Star Wars, Star Trek, Base)
    # Genericize the Star Wars/Trek logic?
    # For now, hardcoded blocks in original functions are complex.
    # We can keep specific functions wrapping this generic one, 
    # OR we can execute callbacks in schema.integrations.
    
    # For this refactor, I will implement specific logic *inside* the wrapper functions
    # (build_building_registry) to keep this clean, OR call them from here.
    # Let's keep it simple: This function does the Markdown part. 
    # The external attributes handle the rest.
    
    return registry

def validate_entry(entry: dict, schema_type: str) -> bool:
    """Validates entry against basic schema requirements."""
    required = ["id", "name"]
    if schema_type == "building": required += ["tier", "cost"]
    elif schema_type == "tech": required += ["tier", "cost"]
    elif schema_type == "faction": required += ["quirks"]
    elif schema_type == "weapon": required += ["category", "stats"]
    elif schema_type == "ability": required += [] # minimal
    
    missing = [f for f in required if f not in entry]
    if missing:
        # print(f"Validation Failed for {schema_type} {entry.get('id')}: missing {missing}")
        return False
    return True

def get_faction_from_path(path, universe_path):
    """Dynamically detects faction from path by checking directory structure or filename."""
    factions_dir = os.path.join(universe_path, "factions")
    
    # 1. Check directory structure (factions/NAME/...)
    try:
        rel_path = os.path.relpath(path, factions_dir)
        faction_name = rel_path.split(os.sep)[0]
        if faction_name != ".." and os.path.isdir(os.path.join(factions_dir, faction_name)):
            return faction_name
    except ValueError:
        pass

    # 2. Check filename prefix (Faction_Name_...)
    filename = os.path.basename(path)
    if os.path.exists(factions_dir):
        potential_factions = [d for d in os.listdir(factions_dir) if os.path.isdir(os.path.join(factions_dir, d))]
        for faction in potential_factions:
            if filename.lower().startswith(faction.lower()):
                return faction
                
    return "Neutral"

def build_building_registry(universe_path, verbose=True):
    """Parses infrastructure markdown files to build the building registry."""
    infra_dir = os.path.join(universe_path, "infrastructure")
    registry = _build_generic_registry(universe_path, BUILDING_SCHEMA, verbose)
    
    # Base Buildings
    base_buildings = ["None", "Recruitment Stations", "Spaceport"]
    for b in base_buildings:
        if b not in registry:
             registry[b] = {"id": b, "tier": 0, "faction": "Global", "source_file": "manual"}

    # Note: Third-party universe-specific building integrations have been removed.
    # To add custom universe building parsers, add integration blocks here.
            
    # Final Standardization Pass
    for bid, data in registry.items():
        registry[bid] = _standardize_building_entry(data)
        
    out_path = os.path.join(infra_dir, "building_registry.json")
    safe_registry_save(out_path, registry, verbose)

def build_tech_registry(universe_path, verbose=True):
    """Parses technology markdown files to build the technology registry."""
    tech_dir = os.path.join(universe_path, "technology")
    
    # 1. Generic Markdown Parsing
    registry = _build_generic_registry(universe_path, TECH_SCHEMA, verbose)
    
    # 2. Tech-Specific Synthesis: Buildings -> Techs
    # Pre-populate with buildings if available
    b_reg_path = os.path.join(universe_path, "infrastructure", "building_registry.json")
    if os.path.exists(b_reg_path):
        with open(b_reg_path, 'r') as f:
            buildings = json.load(f)
        for b_id, b_data in buildings.items():
            tier = b_data.get("tier", 1)
            tech_id = f"Tech_{b_id}"
            
            # Synthesize entry
            syn_entry = {
                "id": tech_id,
                "name": f"Construction: {b_data.get('name', b_id)}",
                "tier": tier,
                "cost": int(b_data.get("cost", 0) * 0.1),
                "prerequisites": b_data.get("prerequisites", []),
                "unlocks_buildings": [b_id],
                "faction": b_data.get("faction"),
                "source_format": "synthetic",
                "source_file": "building_synthesis"
            }
            registry[tech_id] = _standardize_tech_entry(syn_entry)


    # Note: Third-party universe-specific technology integrations have been removed.
    # To add custom universe technology parsers, add integration blocks here.
    # Final Standardization Pass
    for tid, data in registry.items():
        registry[tid] = _standardize_tech_entry(data)

    out_path = os.path.join(tech_dir, "technology_registry.json")
    safe_registry_save(out_path, registry, verbose)

def build_faction_registry(universe_path, verbose=True):
    """Builds faction registry from universe config.json."""
    if verbose: print("Building Faction Registry...")
    config_path = os.path.join(universe_path, "config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        factions = config.get("factions", [])
        metadata = config.get("faction_metadata", {})
    except (FileNotFoundError, json.JSONDecodeError):
        if verbose: print(f"WARNING: config.json not found or invalid at {config_path}. Discovering factions from filesystem...")
        # Discover factions from directory
        factions = []
        factions_dir = os.path.join(universe_path, "factions")
        if os.path.exists(factions_dir):
            for item in os.listdir(factions_dir):
                if os.path.isdir(os.path.join(factions_dir, item)) and not item.startswith('_'):
                    factions.append(item)
        metadata = {}
        
        # Save a default config
        if factions:
            default_config = {
                "name": os.path.basename(universe_path),
                "version": "1.0.0",
                "factions": factions,
                "faction_metadata": {}
            }
            try:
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                if verbose: print(f"Created default config.json with discovered factions: {factions}")
            except Exception as e:
                if verbose: print(f"WARNING: Failed to save default config.json: {e}")

    registry = {}
    for faction_name in factions:
        faction_dir = os.path.join(universe_path, "factions", faction_name)
        subfactions = []
        if os.path.isdir(faction_dir):
            for item in os.listdir(faction_dir):
                item_path = os.path.join(faction_dir, item)
                if os.path.isdir(item_path) and not item.startswith('_'):
                    subfactions.append(item)
        
        # Base entry
        entry = {"id": faction_name, "subfactions": subfactions}
        
        # Merge metadata if present
        if faction_name in metadata:
            entry.update(metadata[faction_name])
            
        # Discover Unit Files (Ref: restore_registry.py logic)
        units_dir = os.path.join(universe_path, "units")
        if "unit_files" not in entry:
            entry["unit_files"] = []
            
        if os.path.exists(units_dir):
            prefix = faction_name.lower()
            for f_name in os.listdir(units_dir):
                if f_name.lower().startswith(prefix) and f_name.endswith(".json"):
                    rel_path = f"units/{f_name}"
                    if rel_path not in entry["unit_files"]:
                        entry["unit_files"].append(rel_path)
            
        registry[faction_name] = entry
    
    # Note: Third-party universe-specific faction integrations have been removed.
    # To add custom universe faction parsers, add integration blocks here.
    # Merge AI Extraction Data
    ai_data_path = os.path.join(universe_path, "parsed_ai_data.json")
    if os.path.exists(ai_data_path):
        def _merge_ai_data():
            with open(ai_data_path, 'r', encoding='utf-8') as f:
                ai_data = json.load(f)
            for fid, fdata in ai_data.items():
                if fid in registry:
                    r_entry = registry[fid]
                    if "quirks" in fdata:
                        if "quirks" not in r_entry: r_entry["quirks"] = {}
                        r_entry["quirks"].update(fdata["quirks"])
                    pid_val = fdata.get("personality_id")
                    if pid_val:
                         r_entry["personality_id"] = pid_val
                    elif "personality_id" not in r_entry:
                         r_entry["personality_id"] = fid
        run_integration("AI Data Merge", _merge_ai_data, verbose)

    # Standardization Pass
    for fid, data in registry.items():
        registry[fid] = _standardize_faction_entry(data)
        if not validate_entry(registry[fid], "faction"):
             if verbose: print(f"Validation warning: Invalid faction entry {fid}")

    out_path = os.path.join(universe_path, "factions", "faction_registry.json")
    safe_registry_save(out_path, registry, verbose)
    if verbose: print(f"Saved {len(registry)} factions to {out_path}")

def build_diplomacy_registry(universe_path: str, verbose: bool = True):
    """Builds diplomacy registry from extracted rules."""
    if verbose: print("Building Diplomacy Registry...")
    
    # Load raw rules if available
    rules_path = os.path.join(universe_path, "diplomacy_rules.json") # Created by Orchestrator?
    # Or just bias table
    
    # Check for historical_bias.json
    bias_path = os.path.join(universe_path, "historical_bias.json")
    
    # If using Orchestrator generated output, we might have specific files.
    # For now, we ensure the directory structure exists and potentially aggregate.
    pass

def build_weapon_registry(universe_path, verbose=True):
    """Builds the master weapon registry using Procedural Generation."""
    if verbose: print("Building Weapon Registry (Procedural)...")
    registry = {}
    factions_dir = os.path.join(universe_path, "factions")
    
    # 1. Load Base Blueprints
    from src.core.config import UNIVERSE_ROOT
    base_bp_path = os.path.join(UNIVERSE_ROOT, "base", "weapons", "base_weapon_blueprints.json")
    if not os.path.exists(base_bp_path):
        if verbose: print(f"WARNING: Base weapon blueprints not found at {base_bp_path}")
        return

    with open(base_bp_path, 'r', encoding='utf-8') as f:
        blueprints = json.load(f)

    # 2. Initialize Factory
    from src.factories.weapon_factory import ProceduralWeaponFactory
    factory = ProceduralWeaponFactory(blueprints)
    
    # 4. Generate Arsenal for Each Faction
    f_reg_path = os.path.join(factions_dir, "faction_registry.json")
    factions = []
    if os.path.exists(f_reg_path):
        with open(f_reg_path, 'r', encoding='utf-8') as f:
            f_reg = json.load(f)
            factions = list(f_reg.keys())
    
    if not factions:
        factions = [d for d in os.listdir(factions_dir) if os.path.isdir(os.path.join(factions_dir, d))]
        
    for faction in factions:
        if faction == "Neutral": continue
        
        # Generate 10 weapons per faction
        # Factory now uses static parameters or defaults
        arsenal = factory.generate_arsenal(faction, {}, count=10)
        registry.update(arsenal)
        
    # 5. Standardize and Save
    out_path = os.path.join(factions_dir, "weapon_registry.json")
    
    # Standardization Pass
    for wid, data in registry.items():
        registry[wid] = _standardize_weapon_entry(data)
        
    with open(out_path, 'w', encoding='utf-8') as f: json.dump(registry, f, indent=2)
    if verbose: print(f"Generated {len(registry)} procedural weapons to {out_path}")


def build_ability_registry(universe_path, verbose=True):
    """Builds the ability registry from the universe's database."""
    if verbose: print("Building Ability Registry...")
    registry = {}
    registry = {}
    
    # 1. Scan Standard Factions Database
    factions_dir = os.path.join(universe_path, "factions")
    path = os.path.join(factions_dir, "abilities_database.md")
    
    # 2. Scan Abilities Directory (New Standard)
    abilities_dir = os.path.join(universe_path, "abilities")
    ability_files = []
    if os.path.exists(path): ability_files.append(path)
    
    if os.path.exists(abilities_dir):
        for f in os.listdir(abilities_dir):
            if f.endswith(".md"):
                ability_files.append(os.path.join(abilities_dir, f))
                
    lines = []
    for f_path in ability_files:
        with open(f_path, 'r', encoding='utf-8') as f:
             lines.extend(f.readlines())
        
    for line in lines:
        line = line.strip()
        if not line.startswith('|') or '---' in line: continue
        entry_match = re.search(r'^\|\s*\*\*(.*?)\*\*\s*\|', line)
        if entry_match:
            clean_name = entry_match.group(1).split('(')[0].strip()
            if clean_name in ["Ability Name", "Notes", "Pick-and-Mix Doctrines"]: continue
            cols = [c.strip() for c in line.split('|')]
            description = cols[2] if len(cols) > 2 else ""
            
            # Don't overwrite if it already exists from another high-priority source?
            # For abilities, we merge
            registry[clean_name] = {
                "id": clean_name, 
                "description": description, 
                "source_file": "abilities_database.md",
                "source_format": "markdown"
            }
            
    # Note: Third-party universe-specific ability integrations have been removed.
    # To add custom universe ability parsers, add integration blocks here.
    # Standardization Pass
    for aid, data in registry.items():
        registry[aid] = _standardize_ability_entry(data)
        if not validate_entry(registry[aid], "ability"):
             if verbose: print(f"Validation warning: Invalid ability entry {aid}")

    out_path = os.path.join(factions_dir, "ability_registry.json")
    with open(out_path, 'w', encoding='utf-8') as f: json.dump(registry, f, indent=2)
    if verbose: print(f"Saved {len(registry)} abilities to {out_path}")

    if verbose: print(f"Saved {len(registry)} total traits to {out_path}")

def build_trait_registry(universe_path, verbose=True):
    """Builds the trait registry by merging base and universe-specific traits."""
    if verbose: print("Building Trait Registry...")
    registry = {}
    
    # 1. Load Base Traits
    from src.core.config import UNIVERSE_ROOT
    base_trait_path = os.path.join(UNIVERSE_ROOT, "base", "traits.json")
    if os.path.exists(base_trait_path):
        with open(base_trait_path, 'r', encoding='utf-8') as f:
            registry.update(json.load(f))
            if verbose: print(f"  Loaded {len(registry)} base traits.")
            
    # 2. Load Universe-Specific Traits
    universe_trait_path = os.path.join(universe_path, "traits.json")
    if os.path.exists(universe_trait_path):
        with open(universe_trait_path, 'r', encoding='utf-8') as f:
            u_traits = json.load(f)
            registry.update(u_traits)
            if verbose: print(f"  Loaded {len(u_traits)} universe-specific traits.")
            
    # 3. Save to factions directory (companion to weapon/ability registries)
    factions_dir = os.path.join(universe_path, "factions")
    out_path = os.path.join(factions_dir, "traits_registry.json")
    
    # Ensure directory exists before writing
    if registry or not os.path.exists(factions_dir):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
    if verbose: print(f"Saved {len(registry)} total traits to {out_path}")

def build_blueprint_registry(universe_path, verbose=True):
    """Builds the blueprint registry by merging base and universe-specific blueprints."""
    if verbose: print("Building Blueprint Registry...")
    from src.utils.blueprint_registry import BlueprintRegistry
    
    # 1. Use the BlueprintRegistry singleton to load and merge
    registry_obj = BlueprintRegistry.get_instance()
    registry_obj.load_blueprints(universe_path, verbose=verbose)
    
    # 2. Save the merged result to factions directory
    factions_dir = os.path.join(universe_path, "factions")
    out_path = os.path.join(factions_dir, "blueprint_registry.json")
    
    # Ensure factions dir exists
    if not os.path.exists(factions_dir):
        os.makedirs(factions_dir)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(registry_obj.blueprints, f, indent=2)
        
    if verbose: print(f"Saved {len(registry_obj.blueprints)} blueprints to {out_path}")
    return len(registry_obj.blueprints)

def build_event_registry(universe_path, verbose=True):
    """Builds event registry for custom universes."""
    if verbose: print("Building Event Registry...")
    # Note: Third-party universe-specific event integrations have been removed.
    # To add custom universe event parsers, add integration logic here.
    pass

def build_map_registry(universe_path, verbose=True):
    """Builds map registry for custom universes."""
    if verbose: print("Building Map Registry...")
    # Note: Third-party universe-specific map integrations have been removed.
    # To add custom universe map parsers, add integration logic here.
    pass

def build_campaign_registry(universe_path: str, verbose: bool = True):
    """Builds the campaign registry from extracted campaign configs."""
    camp_dir = os.path.join(universe_path, "campaigns")
    if not os.path.exists(camp_dir):
        return
        
    if verbose: print("Building Campaign Registry...")
    registry = {}
    
    # 1. Scan for campaign_config.json files
    # Allow multiple campaigns in subdirectories or root
    for root, _, files in os.walk(camp_dir):
        for f in files:
            if f.endswith("campaign_config.json") or f == "campaign_config.json":
                path = os.path.join(root, f)
                try:
                    with open(path, 'r') as cf:
                        data = json.load(cf)
                        
                    # Validate
                    from src.utils.campaign_validator import CampaignValidator
                    validator = CampaignValidator()
                    valid, errs = validator.validate_campaign_config(data)
                    
                    if valid:
                         cid = data.get("campaign_id", "unknown")
                         registry[cid] = {
                             "path": path,
                             "name": data.get("name", cid),
                             "description": data.get("description", "")
                         }
                    else:
                        if verbose: print(f"Skipping invalid campaign {path}: {errs}")
                        
                except Exception as e:
                    if verbose: print(f"Error loading campaign {path}: {e}")
                    
    # Save Registry Index
    out_path = os.path.join(camp_dir, "campaign_registry.json")
    with open(out_path, 'w') as f:
        json.dump(registry, f, indent=2)
        
    if verbose: print(f"Saved {len(registry)} campaigns to {out_path}")

def generate_tech_tree_visualizations(universe_path: str, verbose: bool = True):
    """Generates visual tech trees for all factions."""
    if verbose: print("Generating Tech Tree Visualizations...")
    
    # Load Main Registry
    tech_path = os.path.join(universe_path, "technology", "technology_registry.json")
    if not os.path.exists(tech_path): return
    
    with open(tech_path, 'r') as f:
        master_tree = json.load(f)
        
    # Group by Faction
    faction_trees = {}
    for tid, tdata in master_tree.items():
        # Handle shared techs (no faction) vs specific
        f = tdata.get("faction") or "Global"
        
        # If star trek, techs might be shared or implied.
        if tdata.get("source_format") == "stellaris":
             # Use potential if available, else assume shared/available
             pass
             
        if f not in faction_trees: faction_trees[f] = {}
        faction_trees[f][tid] = tdata
        
    from src.utils.tech_graph_generator import TechGraphGenerator
    generator = TechGraphGenerator(faction_trees)
    
    graph_dir = os.path.join(universe_path, "technology", "graphs")
    if not os.path.exists(graph_dir): os.makedirs(graph_dir)
    
    for faction in faction_trees:
        # Generate Mermaid
        mmd = generator.generate_dependency_graph(faction, "mermaid")
        if mmd:
            with open(os.path.join(graph_dir, f"{faction}_tech_tree.mmd"), "w") as f:
                f.write(mmd)
                
        # Generate JSON for Web Visualization
        generator.export_to_json_graph(faction, os.path.join(graph_dir, f"{faction}_tech_tree.json"))
        
    if verbose: print(f"Generated tech graphs for {len(faction_trees)} factions.")

def build_all_registries(universe_name="void_reckoning", verbose=True):
    """Builds all registries for specified universe."""
    from src.core.config import UNIVERSE_ROOT
    universe_path = os.path.join(UNIVERSE_ROOT, universe_name)
    
    if not os.path.exists(universe_path):
        raise ValueError(f"Universe '{universe_name}' not found at {universe_path}")
    
    build_building_registry(universe_path, verbose)
    build_tech_registry(universe_path, verbose)
    build_faction_registry(universe_path, verbose)
    build_weapon_registry(universe_path, verbose)
    build_ability_registry(universe_path, verbose)
    build_trait_registry(universe_path, verbose)
    build_blueprint_registry(universe_path, verbose)
    
    # New Advanced Parsers (Phase 57)
    build_event_registry(universe_path, verbose)
    build_map_registry(universe_path, verbose)
    build_diplomacy_registry(universe_path, verbose)
    
    # Campaign System (Phase 60)
    build_campaign_registry(universe_path, verbose)
    generate_tech_tree_visualizations(universe_path, verbose)
    
def build_all_registries(universe_name="void_reckoning", verbose=True):
    """Builds all registries for specified universe."""
    from src.core.config import UNIVERSE_ROOT
    universe_path = os.path.join(UNIVERSE_ROOT, universe_name)
    
    if not os.path.exists(universe_path):
        raise ValueError(f"Universe '{universe_name}' not found at {universe_path}")
    
    build_building_registry(universe_path, verbose)
    build_tech_registry(universe_path, verbose)
    build_faction_registry(universe_path, verbose)
    build_weapon_registry(universe_path, verbose)
    build_ability_registry(universe_path, verbose)
    build_trait_registry(universe_path, verbose)
    build_blueprint_registry(universe_path, verbose)
    
    # New Advanced Parsers (Phase 57)
    build_event_registry(universe_path, verbose)
    build_map_registry(universe_path, verbose)
    build_diplomacy_registry(universe_path, verbose)
    
    # Campaign System (Phase 60)
    build_campaign_registry(universe_path, verbose)
    generate_tech_tree_visualizations(universe_path, verbose)
    
    # Procedural Units (Added Phase 73)
    generate_procedural_roster(universe_path, verbose)
    generate_land_roster(universe_path, verbose)

# Procedural Generation logic moved to src/generators/procedural_registry_generator.py

if __name__ == "__main__":
    build_all_registries()
    # Manual trigger if running directly
    # generate_land_roster(os.path.join(UNIVERSE_ROOT, "void_reckoning"), True)
