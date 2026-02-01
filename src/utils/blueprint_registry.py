import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

class BlueprintRegistry:
    """
    Singleton registry for unit and component blueprints (templates).
    Caches templates in memory for efficient instantiation.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BlueprintRegistry, cls).__new__(cls)
            cls._instance.blueprints: Dict[str, Dict[str, Any]] = {}
            cls._instance.initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def load_blueprints(self, universe_path: Optional[str] = None, verbose: bool = True):
        """
        Loads blueprints from base and optional universe-specific directories.
        """
        self.blueprints = {}
        from src.core.config import UNIVERSE_ROOT
        
        # 1. Load Base Blueprints
        base_dir = os.path.join(UNIVERSE_ROOT, "base", "blueprints")
        if os.path.exists(base_dir):
            self._load_from_dir(base_dir, "base", verbose=verbose)
            
        # 2. Load Universe-Specific Blueprints (Overrides)
        if universe_path:
            universe_dir = os.path.join(universe_path, "blueprints")
            universe_name = os.path.basename(universe_path)
            if os.path.exists(universe_dir):
                self._load_from_dir(universe_dir, universe_name, verbose=verbose)
                
            # 3. Load Faction-Specific Markdown Units (Auto-Discovery)
            factions_dir = os.path.join(universe_path, "factions")
            if os.path.exists(factions_dir):
                self._load_markdown_blueprints(factions_dir, universe_name, verbose=verbose)

            # 4. Load Units Directory (JSON/Markdown)
            units_dir = os.path.join(universe_path, "units")
            if os.path.exists(units_dir):
                self._load_from_dir(units_dir, universe_name, verbose=verbose)
        
        self.initialized = True
        if verbose:
            logging.info(f"BlueprintRegistry: Loaded {len(self.blueprints)} blueprints.")

    def _load_from_dir(self, directory: str, source_universe: str, verbose: bool = True):
        """Helper to load all JSON files in a directory."""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for item in data:
                                    self._register_item(item, source_universe)
                            elif isinstance(data, dict):
                                if "id" in data:
                                    self._register_item(data, source_universe)
                                else:
                                    # Might be a dict of blueprints
                                    for key, item in data.items():
                                        if isinstance(item, dict) and "id" not in item:
                                             item["id"] = key
                                        self._register_item(item, source_universe)
                    except Exception as e:
                        logging.error(f"Error loading blueprint file {path}: {e}")

    def _load_markdown_blueprints(self, directory: str, source_universe: str, verbose: bool = True):
        """Helper to load all Markdown unit files in a directory."""
        from src.utils.unit_parser import parse_unit_file
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    # Extract faction from path if possible
                    # Expected Path: .../factions/[FactionName]/Space_Units/[unit].md
                    parts = Path(path).parts
                    faction = "Unknown"
                    if "factions" in parts:
                        idx = parts.index("factions")
                        if len(parts) > idx + 1:
                            faction = parts[idx+1]
                    
                    try:
                        unit = parse_unit_file(path, faction)
                        if unit:
                            # Convert Unit object to Blueprint Dict
                            blueprint = {
                                "id": unit.name.lower().replace(" ", "_"),
                                "name": unit.name,
                                "type": "ship" if unit.is_ship() else "infantry",
                                "base_stats": {
                                    "hp": unit.base_hp,
                                    "armor": unit.armor,
                                    "ma": unit.base_ma,
                                    "md": unit.base_md,
                                    "damage": unit.base_damage,
                                    "shield": getattr(unit, 'shield_max', 0),
                                    "cost": unit.cost
                                },
                                "default_traits": unit.traits,
                                "authentic_weapons": unit.authentic_weapons
                            }
                            # Use register_blueprint to handle faction namespacing
                            factions_to_register = [f.strip() for f in unit.faction.split(',')]
                            for f_owner in factions_to_register:
                                # Create a copy of the blueprint for each registration to ensure ID safety
                                bp_copy = blueprint.copy()
                                self.register_blueprint(bp_copy, source_universe, faction_owner=f_owner)
                    except Exception as e:
                        if verbose:
                            logging.error(f"Error loading markdown blueprint {path}: {e}")

    def _register_item(self, item: Dict[str, Any], source_universe: str):
        """Registers or merges a blueprint item."""
        item["source_universe"] = source_universe
        b_id = item.get("id") or item.get("blueprint_id")
        if not b_id:
            return
            
        item["id"] = b_id # Normalize
        
        if b_id in self.blueprints:
            # Deep merge logic (Universe overrides Base)
            base = self.blueprints[b_id]
            
            # Merge base_stats
            if "base_stats" in item:
                if "base_stats" not in base: base["base_stats"] = {}
                base["base_stats"].update(item["base_stats"])
                
            # Merge universal_stats
            if "universal_stats" in item:
                if "universal_stats" not in base: base["universal_stats"] = {}
                base["universal_stats"].update(item["universal_stats"])
                
            # Concatenate default_traits
            if "default_traits" in item:
                if "default_traits" not in base: base["default_traits"] = []
                base["default_traits"].extend(item["default_traits"])
                base["default_traits"] = list(set(base["default_traits"])) # Unique
                
            # Overwrite other top-level fields
            for k, v in item.items():
                if k not in ["base_stats", "universal_stats", "default_traits"]:
                    base[k] = v
        else:
            self.blueprints[b_id] = item

    def get_blueprint(self, blueprint_id: str, faction: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a blueprint by ID, checking faction namespace first if provided."""
        if faction:
             namespaced_id = f"{faction}:{blueprint_id}"
             if namespaced_id in self.blueprints:
                  return self.blueprints[namespaced_id]
        return self.blueprints.get(blueprint_id)

    def register_blueprint(self, blueprint: Dict[str, Any], source_universe: str = "base", faction_owner: Optional[str] = None):
        """Manually registers a blueprint, optionally namespaced by faction."""
        b_id = blueprint.get("id") or blueprint.get("blueprint_id")
        if faction_owner and b_id:
             if not b_id.startswith(f"{faction_owner}:"):
                  blueprint["id"] = f"{faction_owner}:{b_id}"
                  blueprint["blueprint_id"] = blueprint["id"]
        self._register_item(blueprint, source_universe)

    def list_blueprints(self) -> List[str]:
        """Returns a list of all registered blueprint IDs."""
        return list(self.blueprints.keys())

    def validate_blueprint(self, b_id: str) -> bool:
        """Simple validation check."""
        b = self.get_blueprint(b_id)
        if not b: return False
        required = ["id", "name", "type", "base_stats"]
        if not all(field in b for field in required):
            return False
            
        return True

    def get_faction_blueprints(self, faction_name: str) -> List[Dict[str, Any]]:
        """Returns all blueprints registered to a specific faction."""
        results = []
        prefix = f"{faction_name}:"
        for b_id, data in self.blueprints.items():
            if b_id.startswith(prefix):
                results.append(data)
        return results

    def validate_acquisition(self, blueprint_id: str, faction: str, acquisition_type: str) -> Dict[str, Any]:
        """Validates if a blueprint acquisition is logical and valid."""
        res = {"valid": True, "error": None}
        
        # 1. Existence Check
        namespaced_id = f"{faction}:{blueprint_id}"
        if namespaced_id in self.blueprints:
             res["valid"] = False
             res["error"] = f"Faction {faction} already possesses blueprint {blueprint_id}"
             return res
             
        # 2. Acquisition Type
        valid_types = ["salvage", "theft", "share"]
        if acquisition_type not in valid_types:
             res["valid"] = False
             res["error"] = f"Invalid acquisition type: {acquisition_type}"
             return res
             
        # 3. Source Existence
        if blueprint_id not in self.blueprints:
             res["valid"] = False
             res["error"] = f"Source blueprint {blueprint_id} not found in registry"
             return res
             
        return res
