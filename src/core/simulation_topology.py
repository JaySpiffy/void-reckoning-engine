
import heapq
import functools

from typing import Dict, Any, Optional, List, Tuple

class GraphNode:
    """
    Generic node for Galaxy, System, and Planet graphs.
    """
    def __init__(self, node_id, node_type, name=None, 
                 portal_dest_universe: Optional[str] = None, 
                 portal_dest_coords: Optional[Tuple[float, float]] = None, 
                 portal_id: Optional[str] = None):
        self.id = node_id
        self.type = node_type # "FluxPoint", "Planet", "LandingZone", "Province", "Capital", "System"
        self.name = name if name else f"{node_type}_{node_id}"
        self.edges = [] # List of GraphEdge
        self.metadata = {} # Generic storage (e.g., resource value, owner)
        self.position = None # (x, y) tuple for visualization topology
        
        # Phase 19: Construction Data
        self.buildings = [] # List of building IDs constructed here
        self.max_tier = 1 # Max building tier allow (1=Province, 3=Minor, 5=Major)
        self.building_slots = 0 # Available slots
        self.construction_queue = [] # Compatibility for Planet-like logic
        self.unit_queue = [] # Compatibility for Planet-like logic
        self.max_queue_size = 5 # Compatibility for Planet-like logic
        self.naval_slots = 0 # Compatibility for Planet-like logic
        
        # Phase 33: Ground Warfare
        self.armies = [] # List of Army objects stationed on this node
        self.is_sieged = False

        # Phase 22: Portal Infrastructure
        if portal_dest_universe:
            self.metadata["portal_dest_universe"] = portal_dest_universe
            self.metadata["portal_dest_coords"] = portal_dest_coords
            self.metadata["portal_id"] = portal_id
            
        # Optimization R3: Pre-Index Building Stats
        self._building_cache = {"income": 0, "maintenance": 0, "research": 0}

    @property
    def owner(self) -> str:
        """Compatibility property for Planet-like ownership checks."""
        # Check metadata first
        if "owner" in self.metadata:
            return self.metadata["owner"]
        
        # Fallback to parent object (e.g. Planet) if available
        obj = self.metadata.get("object")
        if obj and hasattr(obj, 'owner') and obj != self:
            return obj.owner
            
        return "Neutral"

    @owner.setter
    def owner(self, value: str):
        """Sets the owner in metadata."""
        self.metadata["owner"] = value

    def generate_resources(self) -> Dict[str, Any]:
        """Compatibility method for Planet-like resource generation checks."""
        # Nodes don't typically generate resources in isolation, 
        # though buildings on them contribute to the Parent Planet income.
        return {"req": 0, "breakdown": {"base": 0, "buildings": 0, "provinces": 0}}

    @property
    def base_income_req(self) -> int:
        """Compatibility property for base income requirements."""
        # Check metadata first
        if "base_income_req" in self.metadata:
            return self.metadata["base_income_req"]
        
        # Fallback to parent object (e.g. Planet) if available
        obj = self.metadata.get("object")
        if obj and hasattr(obj, 'base_income_req') and obj != self:
            return obj.base_income_req
            
        return 0

    @property
    def system(self) -> Any:
        """Compatibility property for parent StarSystem resolution."""
        # Check metadata first
        if "system" in self.metadata:
            return self.metadata["system"]
        
        # Check parent object (e.g. Planet) for its system
        obj = self.metadata.get("object")
        if obj and hasattr(obj, 'system') and obj != self:
            return obj.system
            
        return None

    @property
    def node_reference(self) -> 'GraphNode':
        """Compatibility property: a node is its own reference."""
        return self

    @property
    def provinces(self) -> List['GraphNode']:
        """Compatibility property for Planet-like province list."""
        # A province node is its only province.
        return [self]

    def refresh_building_cache(self):
        """Aggregates bonuses from buildings on this node into the cache. (Optimized R3)"""
        from src.core.universe_data import UniverseDataManager
        building_db = UniverseDataManager.get_instance().get_building_database()
        
        income = 0
        maintenance = 0
        research = 0
        garrison = 0
        naval = 0
        queue = 0
        army = 0
        
        for b_id in self.buildings:
            if b_id in building_db:
                data = building_db[b_id]
                income += data.get("income_req", 0)
                maintenance += data.get("maintenance", 0)
                
                # Tech
                if "research_output" in data:
                    research += data["research_output"]
                elif "Research" in data.get("category", "") or "Lab" in b_id:
                     research += 10
                     
                # Military / Logistics
                garrison += data.get("garrison_bonus", 0)
                b_naval = data.get("naval_slots", 0)
                if b_naval > 0:
                    naval += b_naval
                    queue += 5
                
                if any(k in b_id for k in ["Barracks", "Academy", "Training"]):
                    army += 2
                    queue += 3
                elif any(k in b_id for k in ["Shipyard", "Dock", "Foundry"]):
                    if b_naval == 0:
                        naval += 2
                        queue += 5
                elif any(k in b_id for k in ["Communications", "Logistics", "Hub"]):
                    queue += 2
        
        self._building_cache = {
            "income": income,
            "maintenance": maintenance,
            "research": research,
            "garrison": garrison,
            "naval": naval,
            "queue": queue,
            "army": army
        }

    def process_queue(self, engine: Any) -> None:
        """Compatibility method for Planet-like queue processing."""
        # Nodes usually have their construction advanced by the Parent Planet,
        # but if they are treated as independent colonies, we need a stub.
        pass

    def is_portal(self) -> bool:
        """Returns True if this node acts as an inter-universe portal."""
        return "portal_dest_universe" in self.metadata

    def add_edge(self, target_node, distance=1, stability=1.0):
        edge = GraphEdge(self, target_node, distance, stability)
        self.edges.append(edge)
        return edge

    def add_bidirectional_edge(self, target_node, distance=1, stability=1.0):
        """Adds edges in both directions between this node and target_node."""
        e1 = self.add_edge(target_node, distance, stability)
        e2 = target_node.add_edge(self, distance, stability)
        return e1, e2

    def __lt__(self, other):
        # Tie-breaker for Priority Queue
        return self.id < other.id

    def __repr__(self):
        base = f"[{self.type}] {self.name}"
        if self.is_portal():
            base += f" -> PORTAL to {self.metadata.get('portal_dest_universe')}"
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Serializes node state for config persistence."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "position": self.position,
            "metadata": self.metadata,
            "buildings": self.buildings,
            "max_tier": self.max_tier,
            "building_slots": self.building_slots
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GraphNode':
        """Deserializes node from dictionary."""
        node = cls(data["id"], data["type"], data.get("name"))
        node.position = data.get("position")
        node.metadata = data.get("metadata", {})
        node.buildings = data.get("buildings", [])
        node.max_tier = data.get("max_tier", 1)
        node.building_slots = data.get("building_slots", 0)
        return node

class PortalNode(GraphNode):
    """
    Specialized node for inter-universe portals.
    """
    def __init__(self, node_id, name=None, 
                 portal_dest_universe: str = None, 
                 portal_dest_coords: Tuple[float, float] = None, 
                 portal_id: str = None):
        super().__init__(node_id, "PortalNode", name, 
                         portal_dest_universe, portal_dest_coords, portal_id)

class GraphEdge:
    """
    Directional connection between two nodes.
    """
    def __init__(self, source, target, distance=1, stability=1.0):
        self.source = source
        self.target = target
        self.distance = distance # Cost to traverse (turns)
        self.stability = stability # 0.0 to 1.0 (Storm risk)
        self.blocked = False

    def is_traversable(self):
        return not self.blocked

    def to_dict(self) -> Dict[str, Any]:
        """Serializes edge state."""
        return {
            "source_id": self.source.id,
            "target_id": self.target.id,
            "distance": self.distance,
            "stability": self.stability,
            "blocked": self.blocked
        }


