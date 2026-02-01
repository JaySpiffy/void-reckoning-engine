import os
import re
import json
import logging
import copy
import ast
from typing import List, Dict, Optional, Any, Tuple

from src.utils.parser_registry import ParserRegistry
from src.utils.format_detector import FormatDetector

import src.core.config as config
from src.data.weapon_data import get_weapon_stats
from src.models.unit import Unit, Ship, Regiment, Component

# Defaults
_registry = ParserRegistry.get_instance()

def _safe_int(val: Any, default: int = 0) -> int:
    """Safely converts a value to integer, handling float strings."""
    if val is None: return default
    try:
        if isinstance(val, (int, float)):
            return int(val)
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default

def detect_file_format(filepath: str) -> Dict[str, str]:
    """
    Determines if file is XML, Markdown, or Stellaris script.
    Returns: {'format': '...', 'engine': '...'}
    """
    if filepath.endswith('.xml'):
        return {'format': 'xml', 'engine': 'petroglyph'}
    elif filepath.endswith('.md'):
        return {'format': 'markdown', 'engine': 'native'}
    else:
        return {'format': 'unknown', 'engine': None}

def _extract_raw_stats_from_md(content: str) -> Dict[str, str]:
    """Extracts raw key-value stats from markdown content."""
    stats = {}
    data_block = ""
    
    # 1. Block Detection
    if "<!-- PARSER_DATA" in content:
        start_idx = content.find("<!-- PARSER_DATA")
        end_idx = content.find("-->", start_idx)
        if end_idx != -1:
            data_block = content[start_idx:end_idx] 
    elif "## Parser Data" in content:
        start_marker = "## Parser Data"
        start_idx = content.find(start_marker) + len(start_marker)
        json_start = content.find("{", start_idx)
        if json_start != -1:
            json_end = content.rfind("}")
            if json_end > json_start:
                try:
                    raw_json = json.loads(content[json_start:json_end+1])
                    for k, v in raw_json.items():
                        if k == "stats" and isinstance(v, dict):
                            for sk, sv in v.items(): stats[sk] = str(sv)
                        elif k == "weapons":
                            stats["weapons"] = str(v)
                        elif k == "tags":
                             stats["keywords"] = str(v)
                        else:
                            stats[k] = str(v)
                    return stats
                except: pass

    if not data_block:
         match = re.search(r"PARSER_DATA:({.*?})", content, re.DOTALL)
         if match: data_block = match.group(1)
            
    if not data_block: return stats

    # 2. Text Block Parsing
    if data_block:
        current_list_key = None
        for line in data_block.split('\n'):
            line_clean = line.strip()
            if not line_clean: continue
            
            if ":" in line and not line_clean.startswith("-"):
                key, val = line.split(":", 1)
                key = key.strip()
                stats[key] = val.strip()
                current_list_key = key if not stats[key] else None
            elif line_clean.startswith("-") and current_list_key:
                existing = stats.get(current_list_key, "")
                item = line_clean.strip("- ")
                if ":" in item:
                    parts = item.split(":", 1)
                    if parts[0].strip().lower() == "name": item = parts[1].strip()
                    else: item = parts[0].strip()
                
                if existing: stats[current_list_key] = f"{existing}, {item}"
                else: stats[current_list_key] = item
                
    return stats

def _extract_weapons_from_md(content: str) -> List[str]:
    """Helper to parse weapons section."""
    weapons_list = []
    w_header_match = re.search(r"##\s*(\d\.)?\s*(Weapons|Wargear|Armament)", content, re.IGNORECASE)
    
    if w_header_match:
        weapon_section_start = w_header_match.start()
        next_header = re.search(r"##\s*(\d\.)?\s*(Abilities|Role|Visuals)", content[weapon_section_start+10:], re.IGNORECASE)
        weapon_section_end = len(content)
        if next_header:
            weapon_section_end = weapon_section_start + 10 + next_header.start()
        
        weapon_text = content[weapon_section_start:weapon_section_end]
        found_weapons = re.findall(r"\*\s+\*\*.*?\*\*:\s*(.*)", weapon_text)
        if not found_weapons:
             found_weapons = re.findall(r"\*\s+\*\*(.*?)\*\*", weapon_text)
        
        for w in found_weapons:
            w_clean = w.split("\n")[0].strip()
            if w_clean: weapons_list.append(w_clean)
    return weapons_list

def _create_unit_object(stats: Dict, faction: str, weapons_list: List[str]) -> Unit:
    """Instantiates the Unit object from processed stats."""
    name = stats.get("name", "Unknown")
    
    # Abilities & Tags processing
    abilities = {}
    if "keywords" in stats:
        kw_str = stats["keywords"]
        clean_kws = [k.strip().replace("'", "").replace('"', "") for k in kw_str.strip("[]").split(',')]
        for k in clean_kws: 
            if k: abilities[k] = True

    if "abilities" in stats:
        ab_str = stats["abilities"]
        clean_abs = [k.strip().replace("'", "").replace('"', "") for k in ab_str.strip("[]").split(',')]
        for k in clean_abs:
            if k: abilities[k] = True
            
    if "Tags" not in abilities:
        tags = ["Infantry"]
        if _safe_int(stats.get("armor", 0)) > 80: tags.append("Vehicle") 
        if _safe_int(stats.get("hp", 0)) > 300: tags.append("Monster")
        for k in abilities:
             if k not in tags: tags.append(k)
        abilities["Tags"] = tags

    # Stats Extraction
    ma = _safe_int(stats.get("ma") or stats.get("melee_attack", 30))
    md = _safe_int(stats.get("md") or stats.get("melee_defense", 30))
    hp = _safe_int(stats.get("hp") or stats.get("hull_points", 100))
    armor = _safe_int(stats.get("armor", 0))
    damage = _safe_int(stats.get("damage") or stats.get("weapon_skill", 20))
    shield_val = _safe_int(stats.get("shield") or stats.get("shields") or 0)
    turrets_val = _safe_int(stats.get("turrets", 0))
    cost_val = _safe_int(stats.get("requisition_cost") or stats.get("points") or 150)
    
    if turrets_val > 0: abilities["Turrets"] = turrets_val

    # Class Determination
    role = stats.get("Role", "Infantry")
    is_ship_unit = False
    ship_keywords = ["Ship", "Cruiser", "Battleship", "Escort", "Frigate", "Destroyer", "Grand Cruiser", "Battlecruiser"]
    
    if any(sk in role for sk in ship_keywords): is_ship_unit = True
    elif any(sk in abilities for sk in ship_keywords): is_ship_unit = True
    elif stats.get("unit_type", "").lower() in ["space", "ship", "strike_craft"]: is_ship_unit = True
    elif stats.get("type", "").lower() in ["space", "ship", "strike_craft"]: is_ship_unit = True

    blueprint_id = stats.get("blueprint_id")
    unit_class = stats.get("unit_class")
    domain = stats.get("domain")

    # Instantiate
    trans_cap = int(stats.get("transport_capacity", 0))
    
    # Common Kwargs
    unit_kwargs = {
        "ma": ma,
        "md": md,
        "hp": hp,
        "armor": armor,
        "damage": damage,
        "shield": shield_val,
        "cost": cost_val,
        "rank": 0,
        "blueprint_id": blueprint_id,
        "unit_class": unit_class,
        "domain": domain
    }
    
    if is_ship_unit:
         u = Ship(name, faction, transport_capacity=trans_cap, **unit_kwargs)
    else:
         u = Regiment(name, faction, **unit_kwargs)

    # Inject abilities specifically (since they go to TraitComponent)
    # Unit.__init__ doesn't grab 'abilities' from kwargs automatically for TraitComponent?
    # Let's check Unit.py. It creates components if kwargs are passed.
    # But TraitComponent needs explicit setting.
    # Actually, we add components manually below anyway, but let's be safe.
    if abilities:
        from src.combat.components.trait_component import TraitComponent
        u.add_component(TraitComponent(traits=[], abilities=abilities))

    # Component & Weapon Analysis
    # Ensure stats component is created if not done by kwargs
    if not u.stats_comp:
         from src.combat.components.stats_component import StatsComponent
         u.add_component(StatsComponent(ma=ma, md=md, damage=damage, armor=armor, hp=hp))
    
    # Add Movement Component
    if not u.movement_comp:
         from src.combat.components.movement_component import MovementComponent
         speed = _safe_int(stats.get("speed") or stats.get("movement_points") or stats.get("mobility_speed_tactical", 30))
         u.add_component(MovementComponent(speed))
            
    # Weapon Analysis
    from src.analysis.weapon_analyzer import WeaponAnalyzer
    roles = set()
    total_power = 0
    for w_name in weapons_list:
         w_stats = get_weapon_stats(w_name)
         roles.add(WeaponAnalyzer.classify_weapon(w_stats))
         try: total_power += WeaponAnalyzer.calculate_efficiency_score(w_stats, "MEQ")
         except: pass
    u.tactical_roles = list(roles)
    u.power_rating = _safe_int(total_power) if total_power > 0 else _safe_int(cost_val * 0.1)

    # Misc Stats
    if "faction" in stats: u.faction = stats["faction"]
    u.resonator_mastery = _safe_int(stats.get("resonator_mastery", 0))
    if "Resonator" in u.abilities or "Resonator" in u.abilities.get("Tags", []):
         if u.resonator_mastery == 0: u.resonator_mastery = 1 
         
    mappings = [
        ("upkeep", "upkeep_cost"), ("build_time", "build_time"), ("transport_capacity", "transport_capacity"),
        ("bs", "bs"), ("charge_bonus", "charge_bonus"), ("weapon_range_default", "weapon_range"),
        ("fear_rating", "fear_rating"), ("morale_aura", "morale_aura"), ("regen_hp_per_turn", "regen_hp_per_turn"),
        ("stealth_rating", "stealth_rating"), ("suppression_resistance", "suppression_resistance"),
        ("suppression_power", "suppression_power"), ("detection_range", "detection_range"),
        ("xp_gain_rate", "xp_gain_rate"), ("tier", "tier"), ("agility", "agility"),
        ("facing", "facing"), ("armor_front", "armor_front"), ("armor_side", "armor_side"), ("armor_rear", "armor_rear")
    ]
    for attr, key in mappings:
        val = stats.get(key) or stats.get(attr)
        if val: setattr(u, attr, _safe_int(val))

    # Lists
    for list_attr in ["grid_size", "weapon_arcs", "required_tech", "traits"]:
        if list_attr in stats:
            try:
                val = stats[list_attr]
                if val.startswith("[") and val.endswith("]"): setattr(u, list_attr, ast.literal_eval(val))
                elif list_attr == "required_tech" or list_attr == "traits": setattr(u, list_attr, [val.strip()])
            except: pass
            
    return u

def parse_unit_file(filepath: str, faction: str) -> Optional[Unit]:
    """Parses a unit definition file (.md) into a Unit object."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        stats = _extract_raw_stats_from_md(content)
        if not stats: return None
        
        # Override faction from stats if present
        if "faction" in stats: faction = stats["faction"]
        
        weapons_list = _extract_weapons_from_md(content)
            
        return _create_unit_object(stats, faction, weapons_list)
        
    except Exception as e:
        print(f"PARSER ERROR in {filepath}: {e}")
        return None

def parse_building_markdown(filepath: str) -> Optional[Dict[str, Any]]:
    """Parses a building markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = {"stats": {}}
        if "<!-- PARSER_DATA" in content:
            start = content.find("<!-- PARSER_DATA")
            end = content.find("-->", start)
            if end != -1:
                block = content[start:end]
                for line in block.split('\n'):
                    if ":" in line:
                         k, v = line.split(":", 1)
                         data["stats"][k.strip()] = v.strip()
                         
        return data
    except:
        return None

def parse_technology_markdown(filepath: str) -> Optional[Dict[str, Any]]:
    """Parses a technology markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        data = {"stats": {}}
        # Metadata extraction if present
        return data
    except:
        return None

def parse_json_roster(filepath: str, default_faction: str) -> List[Unit]:
    """Parses a JSON roster file into a list of Unit objects."""
    units = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, dict):
            # Check if it's a map of ID->Unit (like procedural_roster.json) or a single Unit
            # Heuristic: If values are dicts and keys look like IDs, treat as map.
            # Or simpler: if "name" is NOT in top level, assume map.
            if "name" not in data and "base_stats" not in data:
                 data = list(data.values())
            else:
                 data = [data]
        elif not isinstance(data, list):
            data = [] # Invalid format
            
        for entry in data:
            if not isinstance(entry, dict): continue
            
            stats = entry.get("base_stats", {})
            name = entry.get("name", "Unknown")
            faction = entry.get("faction", default_faction)
            
            for k in ["cost", "type", "tier", "upkeep"]:
                if k in entry and k not in stats: stats[k] = entry[k]

            is_ship_unit = False
            u_type = stats.get("type", "").lower()
            if u_type in ["ship", "fighter", "frigate", "cruiser", "battleship", "titan"]: 
                is_ship_unit = True
            elif entry.get("domain") == "space":
                is_ship_unit = True

            abilities_list = entry.get("abilities", [])
            abilities = {a: True for a in abilities_list}
            
            components_data = entry.get("components", [])
            authentic_weapons = []
            for c_entry in components_data:
                if isinstance(c_entry, dict):
                    comp_id = c_entry.get("component")
                    slot = c_entry.get("slot", "").lower()
                    if comp_id and ("weapon" in slot or "turret" in slot or "arm" in slot or "mount" in slot):
                        authentic_weapons.append(comp_id)

            ma = stats.get("ma") or stats.get("melee_attack", 30)
            md = stats.get("md") or stats.get("melee_defense", 30)
            hp = stats.get("hp", 100)
            armor = stats.get("armor", 0)
            damage = stats.get("damage", 10)
            cost = stats.get("cost", 100)
            shield = stats.get("shield", 0)
            
            # Prepare Kwargs
            unit_kwargs = {
                "ma": ma,
                "md": md,
                "hp": hp,
                "armor": armor,
                "damage": damage,
                "cost": cost,
                "shield": shield,
                "blueprint_id": entry.get("blueprint_id"),
                "unit_class": entry.get("unit_class")
            }

            if is_ship_unit:
                u = Ship(name, faction, domain="space", **unit_kwargs)
            else:
                u = Regiment(name, faction, domain="ground", **unit_kwargs)

            # Add Traits/Abilities
            if abilities:
                 from src.combat.components.trait_component import TraitComponent
                 u.add_component(TraitComponent(traits=[], abilities=abilities))

            # Add Weapons implicitly from authentic_weapons if not added via components
            # (Logic for components construction)
            if authentic_weapons:
                 from src.combat.components.weapon_component import WeaponComponent
                 for w_id in authentic_weapons:
                      w_stats = get_weapon_stats(w_id)
                      u.add_component(WeaponComponent(w_id, w_stats))
            
            # Add Movement Component
            if not u.movement_comp:
                 from src.combat.components.movement_component import MovementComponent
                 speed = stats.get("speed") or stats.get("movement_points") or 30
                 u.add_component(MovementComponent(speed))

            units.append(u)

    except Exception as e:
        print(f"Warning: Failed to parse JSON roster {filepath}: {e}")
        
    return units

def load_all_units(target_universe: Optional[str] = None) -> Dict[str, List[Unit]]:
    """Loads all unit definitions."""
    all_units = {}
    from src.core.config import list_available_universes, get_universe_config
    
    universes_to_scan = [target_universe] if target_universe else list_available_universes()

    for uni_name in universes_to_scan:
        try:
            uni_config = get_universe_config(uni_name)
            units_dir = str(uni_config.factions_dir)
            universe_root = os.path.dirname(units_dir)
            
            scan_dirs = [units_dir]
            json_units_dir = os.path.join(universe_root, "units")
            if os.path.exists(json_units_dir): scan_dirs.append(json_units_dir)

            for scan_dir in scan_dirs:
                if not os.path.exists(scan_dir): continue
                    
                for root, dirs, files in os.walk(scan_dir):
                    rel_path = os.path.relpath(root, scan_dir)
                    path_parts = rel_path.split(os.path.sep) if rel_path != "." else []
                    faction = path_parts[0] if path_parts else "Unknown"
                
                    for file in files:
                        path_full = os.path.join(root, file)
                        try:
                            detect_info = detect_file_format(path_full)
                            fmt = detect_info['format']
                            
                            if fmt == "markdown" and "template" not in file and "SPEC" not in file:
                                unit = parse_unit_file(path_full, faction)
                                if unit:
                                    from src.factories.unit_factory import UnitFactory
                                    unit.source_universe = uni_name
                                    UnitFactory._finalize_unit(unit)
                                    factions_to_register = [f.strip() for f in unit.faction.split(',')]
                                    for f_dest in factions_to_register:
                                        if f_dest not in all_units: all_units[f_dest] = []
                                        all_units[f_dest].append(unit)
                            elif file.endswith(".json") and ("roster" in file or "units" in file):
                                f_guess = file.replace("_roster.json", "").replace("_", " ").title().replace(" ", "_")
                                units = parse_json_roster(path_full, f_guess)
                                if units:
                                     from src.factories.unit_factory import UnitFactory
                                     for u in units:
                                         u.source_universe = uni_name
                                         UnitFactory._finalize_unit(u)
                                         if u.faction not in all_units: all_units[u.faction] = []
                                         all_units[u.faction].append(u)
                        except: continue
        except: pass
    return all_units
