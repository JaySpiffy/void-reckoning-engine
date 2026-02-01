import os
import src.core.config as config
from typing import List, Dict, Optional, Any

class DataLoader:
    """Handles loading of combat-related data."""
    
    @staticmethod
    def load_traits() -> List[Dict[str, Any]]:
        """Parses trait_database.md into a list of dicts."""
        traits = []
        from src.core.universe_data import UniverseDataManager
        uni_config = UniverseDataManager.get_instance().universe_config
        
        db_path = None
        if uni_config:
            db_path = uni_config.factions_dir / "trait_database.md"
            
        if not db_path or not os.path.exists(db_path):
            db_path = os.path.join(config.DATA_DIR, "trait_database.md")
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.startswith("| TRAIT"): continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) < 5: continue
                    effect = parts[4]
                    traits.append({"name": parts[2], "type": parts[3], "effect": effect})
        except Exception as e:
            pass
        return traits

    @staticmethod
    def load_points_db() -> Dict[str, int]:
        """Loads unit points from markdown."""
        points_map = {}
        from src.core.universe_data import UniverseDataManager
        uni_config = UniverseDataManager.get_instance().universe_config
        
        db_path = None
        if uni_config:
            db_path = uni_config.factions_dir / "unit_points_database.md"
             
        if not db_path or not os.path.exists(db_path):
            db_path = os.path.join(config.DATA_DIR, "unit_points_database.md")
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.startswith("|") or "Unit Name" in line or "---" in line: continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) < 5: continue
                    name = parts[2]
                    try:
                        cost = int(parts[4])
                        points_map[name] = cost
                    except: continue
        except Exception as e:
            pass
        return points_map

    @staticmethod
    def find_unit_by_name(all_units: Dict[str, List[Any]], query: str, universe_name: Optional[str] = None) -> Optional[Any]:
        """Search for a unit by name."""
        query = query.lower()
        
        # Exact match first
        for faction_units in all_units.values():
            for u in faction_units:
                if u.name.lower() == query:
                    if universe_name:
                        u_uni = getattr(u, 'source_universe', None) or getattr(u, 'universe', None)
                        if u_uni != universe_name: continue
                    return u
                
        # Substring match
        for faction_units in all_units.values():
            for u in faction_units:
                if query in u.name.lower():
                    if universe_name:
                        u_uni = getattr(u, 'source_universe', None) or getattr(u, 'universe', None)
                        if u_uni != universe_name: continue
                    return u
                
        return None

    @staticmethod
    def load_all_units() -> Dict[str, List[Any]]:
        """Loads all units from the units directory."""
        from src.utils.unit_parser import parse_unit_file # Avoid circular import
        all_units = {}
        for root, dirs, files in os.walk(config.UNITS_DIR):
            for file in files:
                if file.endswith(".md") and "template" not in file and "SPEC" not in file:
                    path_parts = root.replace(config.UNITS_DIR, "").strip(os.path.sep).split(os.path.sep)
                    faction = "Unknown"
                    if len(path_parts) > 0: faction = path_parts[0]
                    path = os.path.join(root, file)
                    unit = parse_unit_file(path, faction)
                    if unit:
                        if faction not in all_units: all_units[faction] = []
                        all_units[faction].append(unit)
        return all_units
