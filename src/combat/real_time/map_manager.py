import math
from typing import Dict, List, Any, Optional

class MapObject:
    def __init__(self, name: str, x: float, y: float, radius: float):
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius

    def is_inside(self, px: float, py: float) -> bool:
        dist = math.sqrt((px - self.x)**2 + (py - self.y)**2)
        return dist <= self.radius

class EnvironmentalArea(MapObject):
    """
    An area that applies stat modifiers (e.g. Woods, Nebulae).
    modifiers: e.g. {"speed_mult": 0.5, "accuracy_mult": 0.8}
    """
    def __init__(self, name: str, x: float, y: float, radius: float, modifiers: Dict[str, float]):
        super().__init__(name, x, y, radius)
        self.modifiers = modifiers

class StaticObstacle(MapObject):
    """
    Impassable terrain (Buildings, Asteroids).
    """
    pass

class TacticalObjective(MapObject):
    """
    A capture point that provides Victory Points (VP).
    """
    def __init__(self, name: str, x: float, y: float, radius: float, vp_per_sec: float = 1.0):
        super().__init__(name, x, y, radius)
        self.vp_per_sec = vp_per_sec
        self.owner: Optional[str] = None # Faction name
        self.capture_progress: Dict[str, float] = {} # Faction -> 0-100 progress
        self.capture_threshold = 100.0

    def update_capture(self, present_factions: List[str], dt: float):
        """
        Simplistic capture logic:
        - If only one faction is in range, they gain progress.
        - If multiple or zero, progress stalls (or decays).
        """
        if len(present_factions) == 1:
            f = present_factions[0]
            if self.owner == f:
                return # Already owned
            
            # Gain progress
            current = self.capture_progress.get(f, 0.0)
            self.capture_progress[f] = min(self.capture_threshold, current + 20 * dt) # 5s to capture
            
            # Check for ownership change
            if self.capture_progress[f] >= self.capture_threshold:
                self.owner = f
                # Reset others
                self.capture_progress = {f: self.capture_threshold}
        elif len(present_factions) == 0:
            # Slow decay if empty?
            for f in list(self.capture_progress.keys()):
                if self.owner != f:
                    self.capture_progress[f] = max(0.0, self.capture_progress[f] - 5 * dt)

class MapTemplates:
    @staticmethod
    def apply_space_asteroid_field(grid: Any):
        """Adds asteroids and a central nebula."""
        grid.add_map_object(EnvironmentalArea("Nebula", 50, 50, 20, {"accuracy_mult": 0.5}))
        grid.add_map_object(StaticObstacle("Bigma", 30, 30, 5))
        grid.add_map_object(StaticObstacle("Smalla", 70, 70, 3))
        grid.add_map_object(TacticalObjective("Station Alpha", 50, 50, 5, vp_per_sec=5.0))

    @staticmethod
    def apply_land_forest_ruins(grid: Any):
        """Adds woods and ruins with capture points."""
        grid.add_map_object(EnvironmentalArea("Woods", 20, 20, 15, {"speed_mult": 0.6, "defense_mult": 1.5}))
        grid.add_map_object(EnvironmentalArea("Ruins", 80, 80, 10, {"defense_mult": 2.0, "accuracy_mult": 0.8}))
        grid.add_map_object(StaticObstacle("Cathedral", 50, 50, 8))
        grid.add_map_object(TacticalObjective("North Hill", 50, 20, 5))
        grid.add_map_object(TacticalObjective("South Bunker", 50, 80, 5))
    @staticmethod
    def apply_land_desert(grid: Any):
        """Adds open desert with few rocky outcrops and sandstorms."""
        grid.add_map_object(EnvironmentalArea("Sandstorm", 50, 50, 30, {"accuracy_mult": 0.4, "speed_mult": 0.8}))
        grid.add_map_object(StaticObstacle("Rock Spire", 20, 40, 4))
        grid.add_map_object(StaticObstacle("Dune Ridge", 70, 60, 6))
        grid.add_map_object(TacticalObjective("Oasis", 50, 50, 7, vp_per_sec=3.0))

    @staticmethod
    def apply_land_ice(grid: Any):
        """Adds slippery ice fields and blizzards."""
        grid.add_map_object(EnvironmentalArea("Blizzard", 50, 50, 40, {"accuracy_mult": 0.3, "speed_mult": 0.5}))
        grid.add_map_object(EnvironmentalArea("Ice Field", 30, 70, 20, {"speed_mult": 1.5, "defense_mult": 0.5})) # Fast but exposed
        grid.add_map_object(TacticalObjective("Thermal Vent", 50, 50, 5))

    @staticmethod
    def apply_land_city(grid: Any):
        """Adds urban sprawl with buildings and streets."""
        # Central Plaza
        grid.add_map_object(TacticalObjective("City Center", 50, 50, 8, vp_per_sec=2.0))
        
        # Grid of Buildings (Static Obstacles)
        # 4 Quadrants
        grid.add_map_object(StaticObstacle("Admin Block", 25, 25, 10))
        grid.add_map_object(StaticObstacle("Hab Block A", 75, 25, 10))
        grid.add_map_object(StaticObstacle("Hab Block B", 25, 75, 10))
        grid.add_map_object(StaticObstacle("Industrial Zone", 75, 75, 12))
        
        # Cover (Debris/Barricades)
        grid.add_map_object(EnvironmentalArea("Barricades", 50, 20, 10, {"defense_mult": 1.5, "speed_mult": 0.8}))
        grid.add_map_object(EnvironmentalArea("Alleyway", 20, 50, 5, {"defense_mult": 1.2}))

    @staticmethod
    def apply_land_wasteland(grid: Any):
        """Adds craters and hazardous zones."""
        grid.add_map_object(EnvironmentalArea("Radiation Zone", 50, 50, 25, {"accuracy_mult": 0.7, "defense_mult": 0.9}))
        grid.add_map_object(EnvironmentalArea("Crater Field", 30, 30, 15, {"speed_mult": 0.5, "defense_mult": 1.5}))
        grid.add_map_object(StaticObstacle("Wrecked Titan", 70, 70, 15))
        grid.add_map_object(TacticalObjective("Relic Vault", 50, 50, 5, vp_per_sec=3.0))

    @staticmethod
    def apply_land_plains(grid: Any):
        """Standard open field with light cover."""
        grid.add_map_object(EnvironmentalArea("Tall Grass", 20, 80, 20, {"accuracy_mult": 0.9}))
        grid.add_map_object(EnvironmentalArea("Small Hill", 80, 20, 15, {"range_mult": 1.1}))
        grid.add_map_object(TacticalObjective("Comms Relay", 50, 50, 5))

class ShieldDome(MapObject):
    """
    Visual representation of a planetary shield.
    """
    def __init__(self, name: str, x: float, y: float, radius: float, strength: float = 1.0):
        super().__init__(name, x, y, radius)
        self.strength = strength # 0.0 to 1.0 opacity/integrity

class MapGenerator:
    """
    Selects and applies map templates based on location context.
    """
    @staticmethod
    def generate_map(grid: Any, location: Any):
        """
        Populates a grid based on location type and biome.
        """
        # Determine Domain
        is_space = hasattr(location, 'is_star_system') or (hasattr(location, 'type') and location.type in ["Planet", "Star", "FluxGate"])
        
        if is_space:
            MapTemplates.apply_space_asteroid_field(grid)
            return

        # [Hex Map Support]
        # Check for Shield Generator (Local or Neighbor)
        has_shield = False
        shield_strength = 0.0
        
        # 1. Check Local
        if hasattr(location, 'buildings'):
            # Naive check for "Shield" in ID
            # Better: Use constants or DB, but ID match is fast for visual only
            if any("Shield" in b_id for b_id in location.buildings):
                has_shield = True
                shield_strength = 1.0
        
        # 2. Check Neighbors (AoE Visual)
        if not has_shield and hasattr(location, 'edges'):
             for edge in location.edges:
                  neighbor = edge.target
                  if hasattr(neighbor, 'buildings'):
                       if any("Shield" in b_id for b_id in neighbor.buildings):
                            has_shield = True
                            shield_strength = 0.5 # Fainter visual for projected shield
                            break
        
        if has_shield:
             # Add Shield Dome to Center
             # Radius 60 covers most of the map (100x100)
             grid.add_map_object(ShieldDome("Planetary Shield", 50, 50, 60, strength=shield_strength))

        # If location has explicit terrain_type (HexNode)
        terrain = getattr(location, 'terrain_type', None)
        if terrain:
            # Map Hex Biomes
            if terrain == "City":
                MapTemplates.apply_land_city(grid)
                return
            elif terrain in ["Wasteland", "Ruins"]:
                MapTemplates.apply_land_wasteland(grid)
                return
            elif terrain == "Forest":
                MapTemplates.apply_land_forest_ruins(grid)
                return
            elif terrain == "Plains":
                MapTemplates.apply_land_plains(grid)
                return

        # Legacy / Fallback Ground Biomes
        planet_class = getattr(location, 'planet_class', "Terran")
        if hasattr(location, 'parent_planet'): # GraphNode fallback
            # Try to resolve parent object
            if hasattr(location, 'metadata') and location.metadata.get("object"):
                 # Determine parent
                 pass 
        
        if planet_class in ["Desert", "Arid"]:
            MapTemplates.apply_land_desert(grid)
        elif planet_class in ["Ice", "Tundra"]:
            MapTemplates.apply_land_ice(grid)
        elif planet_class in ["Jungle", "Forest", "Gaia"]:
            MapTemplates.apply_land_forest_ruins(grid)
        else:
            # Fallback
            MapTemplates.apply_land_plains(grid)
