import json
import os
from typing import Dict, Any, List, Optional

class PostureRegistry:
    """
    Handles loading, validation, and retrieval of posture definitions.
    Supports Archetype-based inheritance to simplify configuration.
    """
    def __init__(self, universe_name: str = "void_reckoning"):
        self.universe_name = universe_name
        self.postures: Dict[str, Any] = {}
        self.archetypes: Dict[str, Any] = {}
        self._load_registry()

    def _load_registry(self):
        """Loads posture definitions from the universe directory."""
        # Standard path for posture registry
        path = f"universes/{self.universe_name}/ai/posture_registry.json"
        
        if not os.path.exists(path):
            # Fallback for local dev if CWD is different
            path = os.path.join(os.getcwd(), path)
            
        if not os.path.exists(path):
            # Default fallback if file is totally missing
            self._create_default_registry()
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.archetypes = data.get("archetypes", {})
                self.postures = data.get("postures", {})
                
                # Apply Inheritance
                self._apply_archetype_inheritance()
        except Exception as e:
            print(f"[REGRISTRY] Failed to load postures: {e}")
            self._create_default_registry()

    def _apply_archetype_inheritance(self):
        """Merges archetype defaults into specific postures."""
        for p_id, p_data in self.postures.items():
            archetype_id = p_data.get("archetype")
            if archetype_id and archetype_id in self.archetypes:
                archetype = self.archetypes[archetype_id]
                
                # Deep merge logic for weights and effects
                merged_data = self._deep_merge(archetype, p_data)
                self.postures[p_id] = merged_data

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Helper to merge nested dictionaries."""
        result = base.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    def get_posture(self, posture_id: str) -> Optional[Dict]:
        return self.postures.get(posture_id)

    def get_available_postures(self, faction_name: str = None) -> List[str]:
        """Returns IDs of postures valid for this faction."""
        available = []
        for p_id, p_data in self.postures.items():
            # Check Faction Affinity
            affinity = p_data.get("faction_affinity")
            if affinity and faction_name not in affinity:
                continue
            
            # Check 'general' flag
            if not p_data.get("general", True) and not affinity:
                 continue
                 
            available.append(p_id)
        return available

    def _create_default_registry(self):
        """Provides minimal hardcoded postures if JSON loading fails."""
        self.archetypes = {
            "BALANCED": {
                "name": "Balanced",
                "weights": {"income": 1.0, "distance": 1.0, "threat": 1.0, "expansion_bias": 1.0},
                "personality_mods": {}
            }
        }
        self.postures = {
            "BALANCED": {"archetype": "BALANCED", "general": True}
        }
