import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

class MultiRegistryLoader:
    """
    Loads and merges faction registries from multiple sources.
    Supports loading from void_reckoning (original) and procedural_sandbox (generated).
    """
    
    def __init__(self, base_universe_path: str = "universes/void_reckoning", 
                 procedural_universe_path: str = "universes/procedural_sandbox"):
        self.base_universe_path = base_universe_path
        self.procedural_universe_path = procedural_universe_path
        self.loaded_factions: Dict[str, Dict[str, Any]] = {}
        self.faction_index: Dict[str, str] = {}  # Maps uid/id to faction data key
    
    def load_all_registries(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads all faction registries from both base and procedural universes.
        
        Returns:
            Dictionary of all factions keyed by their uid (or id if uid missing)
        """
        # Load base universe factions
        self._load_base_registry()
        
        # Load procedural universe factions
        self._load_procedural_registry()
        
        return self.loaded_factions
    
    def _load_base_registry(self):
        """Loads factions from the base void_reckoning universe."""
        faction_registry_path = os.path.join(self.base_universe_path, "factions", "faction_registry.json")
        
        if os.path.exists(faction_registry_path):
            with open(faction_registry_path, 'r') as f:
                registry = json.load(f)
                
            for faction_id, faction_data in registry.items():
                # Use uid if available, otherwise use id
                faction_key = faction_data.get("uid", faction_data.get("id", faction_id))
                self.loaded_factions[faction_key] = faction_data
                self.faction_index[faction_key] = faction_key
                
                # Also index by legacy id for compatibility
                if "id" in faction_data:
                    self.faction_index[faction_data["id"]] = faction_key
    
    def _load_procedural_registry(self):
        """Loads all procedurally generated factions from procedural_sandbox."""
        procedural_factions_path = os.path.join(self.procedural_universe_path, "factions")
        
        if os.path.exists(procedural_factions_path):
            for filename in os.listdir(procedural_factions_path):
                if filename.endswith(".json"):
                    filepath = os.path.join(procedural_factions_path, filename)
                    with open(filepath, 'r') as f:
                        faction_data = json.load(f)
                    
                    # Use uid if available, otherwise use id
                    faction_key = faction_data.get("uid", faction_data.get("id", filename))
                    self.loaded_factions[faction_key] = faction_data
                    self.faction_index[faction_key] = faction_key
                    
                    # Also index by legacy id for compatibility
                    if "id" in faction_data:
                        self.faction_index[faction_data["id"]] = faction_key
    
    def get_faction(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a faction by uid or id.
        
        Args:
            identifier: The faction's uid or id
        
        Returns:
            Faction data dictionary or None if not found
        """
        # Try direct lookup first
        if identifier in self.loaded_factions:
            return self.loaded_factions[identifier]
        
        # Try indexed lookup
        if identifier in self.faction_index:
            return self.loaded_factions[self.faction_index[identifier]]
        
        return None
    
    def get_all_factions(self) -> List[Dict[str, Any]]:
        """Returns list of all loaded factions."""
        return list(self.loaded_factions.values())
    
    def get_procedural_factions(self) -> List[Dict[str, Any]]:
        """Returns list of only procedurally generated factions."""
        return [f for f in self.loaded_factions.values() if f.get("archetype") not in [None, "Unknown"]]
    
    def get_base_factions(self) -> List[Dict[str, Any]]:
        """Returns list of only base void_reckoning factions."""
        return [f for f in self.loaded_factions.values() if f.get("archetype") in [None, "Unknown"]]
