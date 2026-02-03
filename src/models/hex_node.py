from typing import Tuple, Dict, Any, Optional
from src.core.simulation_topology import GraphNode
from src.core.hex_lib import Hex

class HexNode(GraphNode):
    """
    A GraphNode representing a single Hex tile on a Planet surface.
    Coordinates (q, r) map to the visualization layer.
    """
    def __init__(self, node_id: str, q: int, r: int, planet_id: str):
        # ID is usually f"{planet_id}_{q}_{r}" or similiar
        super().__init__(node_id, "HexNode")
        self.q = q
        self.r = r
        self.hex_coords = Hex(q, r)
        self.parent_planet_id = planet_id
        
        # Terrain
        self.terrain_type = "Plains" # Default
        self.feature: Optional[str] = None # e.g. "Fortress", "Mine"
        self.biomass = 0 # Organic content (Forests etc)
        
        # Gameplay State
        self.resource_yield = {}
        
    @property
    def position(self) -> Tuple[float, float]:
        """Override standard position with hex pixel calculation."""
        # Assume generic size for now, visualization engine scales it
        return self.hex_coords.to_pixel(1.0)
    
    @position.setter
    def position(self, value):
        # Ignore manual overrides if dependent on q,r
        pass

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "q": self.q,
            "r": self.r,
            "terrain_type": self.terrain_type,
            "feature": self.feature,
            "parent_planet_id": self.parent_planet_id
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'HexNode':
        # Reconstruct logic needed? Usually nodes are rebuilt by generation
        # But for save loading:
        node = cls(data["id"], data["q"], data["r"], data["parent_planet_id"])
        node.terrain_type = data.get("terrain_type", "Plains")
        node.feature = data.get("feature")
        
        # Base restore
        node.metadata = data.get("metadata", {})
    def get_bombardment_defense(self) -> float:
        """
        Calculates the local bombardment defense provided by buildings in this hex.
        Returns a float percentage (e.g., 0.15 for 15%).
        """
        from src.core.constants import get_building_database
        
        building_db = get_building_database()
        defense = 0.0
        
        for b_id in self.buildings:
            b_data = building_db.get(b_id)
            if not b_data:
                continue
                
            effects = b_data.get("effects", {}).get("description", "")
            # Naive parsing for now, or check for specific effect keys if structured
            # "Reducues bombardment damage by 15%"
            if "bombardment damage" in effects.lower():
                # Extract number
                import re
                match = re.search(r"(\d+)%", effects)
                if match:
                    defense += float(match.group(1)) / 100.0
                    
        return min(defense, 0.90) # Cap at 90%

