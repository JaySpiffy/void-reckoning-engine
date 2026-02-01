import os
import json
from typing import Dict, Any, Optional, List
from src.core.config import get_universe_config

class UniverseDataManager:
    """
    Singleton manager for universe-specific game data.
    Provides a centralized API for accessing things like planet classes,
    terrain modifiers, and faction lists.
    """
    _instance: Optional['UniverseDataManager'] = None
    
    def __init__(self):
        self.active_universe: Optional[str] = None
        self.universe_config = None
        self.game_data: Dict[str, Any] = {}
        self.factions: List[str] = []
        self._registry_cache: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> 'UniverseDataManager':
        if cls._instance is None:
            cls._instance = UniverseDataManager()
        return cls._instance

    def load_universe_data(self, universe_name: str):
        """Loads all universe-specific data for the given universe."""
        if self.active_universe == universe_name:
            return

        self._registry_cache.clear()
        self.active_universe = universe_name
        
        self.active_universe = universe_name
        
        self.universe_config = get_universe_config(universe_name)
        print(f"[DEBUG] UniverseDataManager: Loaded universe config for {universe_name}")

        # Reload Legacy Static DBs with new universe context
        try:
            from src.data.weapon_data import reload_weapon_db
            from src.combat.combat_utils import reload_combat_dbs
            reload_weapon_db()
            reload_combat_dbs()
        except ImportError:
            pass # Maybe modules not present or circular dep failed but we try
        
        self.game_data = self.universe_config.load_game_data()
        self.diplomacy_data = self.universe_config.load_diplomacy_data()
        self.factions = self.universe_config.get_factions()
        print(f"[DEBUG] UniverseDataManager: Factions loaded: {self.factions}")

    def get_factions(self) -> List[str]:
        return self.factions

    def get_planet_classes(self) -> Dict[str, Any]:
        return self.game_data.get("planet_classes", {})

    def get_terrain_modifiers(self) -> Dict[str, Any]:
        return self.game_data.get("terrain_modifiers", {})

    def get_building_defense_bonus(self) -> Dict[str, Any]:
        return self.game_data.get("building_defense_bonus", {})

    def get_historical_bias(self) -> Dict[str, Any]:
        return self.diplomacy_data.get("historical_bias", {})

    def get_building_database(self) -> Dict[str, Any]:
        """Returns the building database loaded from infrastructure_db.json."""
        if "building" in self._registry_cache:
            return self._registry_cache["building"]
            
        if not self.universe_config:
            return {}
        path = self.universe_config.registry_paths.get("building")
        if path and path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._registry_cache["building"] = data
                # print(f"[DEBUG] UniverseDataManager: Loaded {len(data)} buildings from {path}")
                return data
        return {}

    def get_faction_registry(self) -> Dict[str, Any]:
        """Returns the faction registry loaded from faction_registry.json."""
        if "faction" in self._registry_cache:
            return self._registry_cache["faction"]

        if not self.universe_config:
            return {}
        path = self.universe_config.registry_paths.get("faction")
        if path and path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._registry_cache["faction"] = data
                return data
        return {}

    def get_weapon_database(self) -> Dict[str, Any]:
        """Returns the weapon registry."""
        if "weapon" in self._registry_cache:
            return self._registry_cache["weapon"]

        if not self.universe_config:
            return {}
        path = self.universe_config.registry_paths.get("weapon")
        if path and path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._registry_cache["weapon"] = data
                return data
        return {}

    def get_ability_database(self) -> Dict[str, Any]:
        """Returns the ability registry."""
        # 1. Try Cache
        if "ability" in self._registry_cache:
            return self._registry_cache["ability"]

        data = {}
        # 2. Load Base Atomic Registry (Core)
        base_path = "universes/base/abilities/atomic_ability_registry.json"
        if os.path.exists(base_path):
             with open(base_path, 'r', encoding='utf-8') as f:
                data.update(json.load(f))
        
        if self.universe_config:
            path = self.universe_config.registry_paths.get("ability")
            if path and path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    data.update(json.load(f))
                    
        # 4. Load Faction Specific Overrides (e.g. universes/void_reckoning/factions/ability_registry.json)
        # This covers cases where abilities are defined alongside factions but not in the main ability registry
        target_universe = self.active_universe or "void_reckoning"
        faction_reg_path = os.path.join("universes", target_universe, "factions", "ability_registry.json")
        if os.path.exists(faction_reg_path):
             try:
                 with open(faction_reg_path, 'r', encoding='utf-8') as f:
                     data.update(json.load(f))
             except Exception as e:
                 print(f"[WARNING] Failed to load faction ability registry: {e}")
                    
        self._registry_cache["ability"] = data
        return data
        
    def get_technology_database(self) -> Dict[str, Any]:
        """Returns the technology registry."""
        if "technology" in self._registry_cache:
            return self._registry_cache["technology"]

        if not self.universe_config:
            return {}
        path = self.universe_config.registry_paths.get("technology")
        if path and path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._registry_cache["technology"] = data
                print(f"[DEBUG] UniverseDataManager: Loaded {len(data)} technologies from {path}")
                return data
        return {}

    def get_trait_registry(self) -> Dict[str, Any]:
        """Returns the trait registry."""
        if "trait" in self._registry_cache:
            return self._registry_cache["trait"]

        if not self.universe_config:
            return {}
        path = self.universe_config.registry_paths.get("trait")
        if path and path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._registry_cache["trait"] = data
                return data
        return {}

    def get_blueprint_registry(self) -> Dict[str, Any]:
        """Returns the blueprint registry."""
        from src.utils.blueprint_registry import BlueprintRegistry
        return BlueprintRegistry.get_instance().blueprints


    def get_combat_rules_module(self) -> Any:
        """
        Dynamically loads the combat rules module defined in universe config.
        Returns None if not defined or load fails.
        """
        if not self.universe_config or not self.universe_config.modules:
            return None
            
        try:
            return self.universe_config.load_module("combat_rules")
        except (KeyError, ImportError) as e:
            print(f"[WARNING] Failed to load combat rules: {e}")
            return None
