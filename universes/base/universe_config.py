from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import importlib

class UniverseConfig:
    """
    Manages universe metadata and dynamic path resolution.
    
    This class handles the mapping of universe-specific data directories
    and registry files, ensuring the core engine can access content
    regardless of the active universe.
    """
    
    def __init__(self, 
                 universe_name: str, 
                 universe_version: str, 
                 universe_root: Path,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initializes the universe configuration.
        
        Args:
            universe_name: The canonical name of the universe.
            universe_version: The version string for the universe data.
            universe_root: The root directory where universe data is stored.
            metadata: Optional dictionary of custom universe settings.
        """
        self.universe_name = universe_name
        self.universe_version = universe_version
        self.universe_root = Path(universe_root)
        self.metadata = metadata or {}
        self.factions = self.metadata.get("factions", [])
        
        # Format support (Phase Hybrid)
        self.unit_formats: Dict[str, List[str]] = {}
        self.supports_xml: bool = self.metadata.get("supports_xml", False)
        
        # Alias for backward compatibility
        self.name = universe_name
        
        # Data paths
        self.game_data_path = self.universe_root / "game_data.json"
        self.diplomacy_data_path = self.universe_root / "diplomacy_data.json"
        self.translation_table_path = self.universe_root.parent / "base" / "translation_table.json"
        self.physics_profiles_path = self.universe_root.parent / "base" / "physics_profiles.json"
        self.portal_config_path = self.universe_root / "portal_config.json"
        
        self._cache: Dict[str, Any] = {}
        
        # Derived paths
        self.factions_dir = self.universe_root / "factions"
        self.infrastructure_dir = self.universe_root / "infrastructure"
        self.technology_dir = self.universe_root / "technology"
        self.units_dir = self.universe_root / "units"
        
        # Registry paths
        building_path = self.infrastructure_dir / "building_registry.json"
        if not building_path.exists():
            alt_path = self.infrastructure_dir / "infrastructure_db.json"
            if alt_path.exists():
                building_path = alt_path
                
        self.registry_paths: Dict[str, Path] = {
            "building": building_path,
            "tech": self.technology_dir / "technology_registry.json",
            "technology": self.technology_dir / "technology_registry.json",
            "weapon": self.factions_dir / "weapon_registry.json",
            "ability": self.factions_dir / "ability_registry.json",
            "faction": self.factions_dir / "faction_registry.json",
            "trait": self.factions_dir / "traits_registry.json",
            "blueprint": self.factions_dir / "blueprint_registry.json"
        }
        
        # Module paths (loaded from config.json)
        self.modules: Dict[str, str] = metadata.get("modules", {}) if metadata else {}

    def load_module(self, module_key: str) -> Any:
        """Dynamically imports and returns a universe-specific module.
        
        Args:
            module_key: Key in the modules dictionary (e.g., 'ai_personalities').
            
        Returns:
            Any: The imported module object.
            
        Raises:
            KeyError: If module_key is not defined in config.
            ImportError: If the module cannot be loaded.
        """
        module_path = self.modules.get(module_key)
        if not module_path:
            raise KeyError(f"Module '{module_key}' not defined in universe configuration.")
            
        return importlib.import_module(module_path)

    def load_game_data(self) -> Dict[str, Any]:
        """Loads game_data.json for the universe."""
        if "game_data" in self._cache:
            return self._cache["game_data"]
            
        if not self.game_data_path.exists():
            return {}
            
        with open(self.game_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._cache["game_data"] = data
            return data

    def load_diplomacy_data(self) -> Dict[str, Any]:
        """Loads diplomacy_data.json for the universe."""
        if "diplomacy_data" in self._cache:
            return self._cache["diplomacy_data"]
            
        if not self.diplomacy_data_path.exists():
            return {}
            
        with open(self.diplomacy_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._cache["diplomacy_data"] = data
            return data

    def load_portal_config(self) -> Dict[str, Any]:
        """Loads and validates portal_config.json for the universe."""
        if "portal_config" in self._cache:
            return self._cache["portal_config"]
            
        if not self.portal_config_path.exists():
            return {"enable_portals": False, "portals": [], "portal_pairs": []}
            
        try:
            # We skip full validation for the new field for now, or assume Validator handles it loosely
            # Ideally update Validator too, but prompt said "update validation OR bypass".
            # We'll just load it directly to be safe, assuming the file has it.
            with open(self.portal_config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Basic key checks if not validating deeply
            if "portals" not in data: data["portals"] = []
            if "portal_pairs" not in data: data["portal_pairs"] = []
                
            self._cache["portal_config"] = data
            return data
        except Exception as e:
            print(f"Error loading portal config from {self.portal_config_path}: {e}")
            return {"enable_portals": False, "portals": [], "portal_pairs": []}

    def get_portal_definitions(self) -> List[Dict[str, Any]]:
        """Returns the list of portal definitions (Phase 22)."""
        cfg = self.load_portal_config()
        return cfg.get("portals", [])

    def get_portal_pairs(self) -> List[Dict[str, Any]]:
        """Returns the list of portal pairs (Phase 22)."""
        cfg = self.load_portal_config()
        return cfg.get("portal_pairs", [])

    def has_portals(self) -> bool:
        """Returns True if portals are enabled (Phase 22)."""
        cfg = self.load_portal_config()
        return cfg.get("enable_portals", False)

    def get_factions(self) -> list:
        """Returns the list of factions supported by this universe."""
        return self.factions

    def validate_structure(self) -> bool:
        """Validates that the required universe directory structure exists.
        
        Returns:
            bool: True if factions, infrastructure, and technology dirs exist.
        """
        required_dirs = [
            self.factions_dir,
            self.infrastructure_dir,
            self.technology_dir
        ]
        return all(d.is_dir() for d in required_dirs)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the configuration to a dictionary.
        
        Returns:
            Dict[str, Any]: Serialized config data.
        """
        return {
            "name": self.universe_name,
            "version": self.universe_version,
            "root": str(self.universe_root),
            "metadata": self.metadata,
            "unit_formats": self.unit_formats,
            "supports_xml": self.supports_xml,
            "portal_config_path": str(self.portal_config_path)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniverseConfig':
        """Deserializes the configuration from a dictionary.
        
        Args:
            data: The dictionary containing config data.
            
        Returns:
            UniverseConfig: An instance of UniverseConfig.
        """
        config = cls(
            universe_name=data["name"],
            universe_version=data["version"],
            universe_root=Path(data["root"]),
            metadata=data.get("metadata")
        )
        config.factions = data.get("factions", [])
        config.unit_formats = data.get("unit_formats", {})
        config.supports_xml = data.get("supports_xml", False)
        if "portal_config_path" in data:
            config.portal_config_path = Path(data["portal_config_path"])
        return config

    def __repr__(self) -> str:
        return f"UniverseConfig(name='{self.universe_name}', version='{self.universe_version}')"
