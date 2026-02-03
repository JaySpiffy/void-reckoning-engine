import math
import random
from typing import List, Optional, Any, Dict

from src.core.universe_physics import PhysicsProfile
from src.combat.spatial_partition import QuadTree

class TacticalGrid:
    """
    Manages a 2D sparse grid for space combat simulation.
    target_scale: 100x100 tiles.
    """
    def __init__(self, width=100, height=100, map_type="Ground"):
        self.width = width
        self.height = height
        self.map_type = map_type
        # Sparse storage: (x, y) -> Unit/Ship object
        self.occupied_tiles = {} 
        self.terrain_map = {} # (x, y) -> "Heavy", "Light", or None

        
        # New: Spatial partition for efficient proximity queries
        self.spatial_index = QuadTree(width, height)
        
        # [GPU Acceleration] Optional tracker reference
        self.gpu_tracker = None
        
        # [PHASE 17.10] Map Environment Objects
        self.areas: List[Any] = [] # EnvironmentalArea
        self.obstacles: List[Any] = [] # StaticObstacle
        self.objectives: List[Any] = [] # TacticalObjective
        
        self.generate_terrain()

    def add_map_object(self, obj: Any):
        from src.combat.real_time.map_manager import EnvironmentalArea, StaticObstacle, TacticalObjective
        if isinstance(obj, EnvironmentalArea):
            self.areas.append(obj)
        elif isinstance(obj, StaticObstacle):
            self.obstacles.append(obj)
        elif isinstance(obj, TacticalObjective):
            self.objectives.append(obj)

    def get_modifiers_at(self, x: float, y: float) -> Dict[str, float]:
        """Aggregates modifiers from all areas at (x, y)."""
        combined = {}
        for area in self.areas:
            if area.is_inside(x, y):
                for mod, val in area.modifiers.items():
                    if mod not in combined:
                        combined[mod] = 1.0
                    combined[mod] *= val
        return combined

    def generate_terrain(self, density=0.15):
        """Randomly populates the grid based on map type."""
        # print(f"DEBUG_TERRAIN_GEN: Generating {self.map_type} Map")
        if self.map_type == "Space":
             # [Space Map] Empire at War Style
             # Asteroids (Block movement/fire, Indestructible) & Nebulae
             # Lower density for space optimization
             space_density = density * 0.4 
             for _ in range(int(self.width * self.height * space_density)):
                 x = random.randint(0, self.width - 1)
                 y = random.randint(0, self.height - 1)
                 # Asteroids
                 self.terrain_map[(x, y)] = {
                     "type": "Asteroid", 
                     "hp": 9999, 
                     "max_hp": 9999,
                     "blocks_movement": True
                 }
        else:
             # [Ground Map] Total War Style
             # Destructible Cover
             for _ in range(int(self.width * self.height * density)):
                 x = random.randint(0, self.width - 1)
                 y = random.randint(0, self.height - 1)
                 ctype = "Heavy" if random.random() < 0.3 else "Light"
                 max_hp = 100 if ctype == "Heavy" else 50
                 # [Dynamic Cover] Store detailed state
                 self.terrain_map[(x, y)] = {"type": ctype, "hp": max_hp, "max_hp": max_hp}

    def get_cover_at(self, x, y):
        # Backward compatibility: Return string type
        data = self.terrain_map.get((x, y))
        if isinstance(data, dict):
            return data["type"]
        return data or "None"

    def damage_cover(self, x, y, amount):
        """Reduces HP of cover at (x, y). Returns True if destroyed."""
        data = self.terrain_map.get((x, y))
        if not isinstance(data, dict): return False
        
        data["hp"] -= amount
        if data["hp"] <= 0:
            # Downgrade or Destroy
            if data["type"] == "Heavy":
                 data["type"] = "Light"
                 data["hp"] = 50
                 data["max_hp"] = 50
                 return "DOWNGRADE"
            else:
                 del self.terrain_map[(x, y)]
                 return "DESTROYED"
        return False

    def is_valid_tile(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_occupied(self, x, y):
        return (x, y) in self.occupied_tiles

    def place_unit(self, unit, x, y):
        """Initial placement of a unit with multi-tile support."""
        grid_w, grid_h = getattr(unit, 'grid_size', [1, 1])
        
        # 1. Validate all tiles
        for dx in range(grid_w):
            for dy in range(grid_h):
                if not self.is_valid_tile(x + dx, y + dy):
                    return False
                if self.is_occupied(x + dx, y + dy):
                    return False
                    
        # 2. Occupy all tiles
        for dx in range(grid_w):
            for dy in range(grid_h):
                self.occupied_tiles[(x + dx, y + dy)] = unit
                
        unit.grid_x = x
        unit.grid_y = y
        unit.is_deployed = True
        
        # New: Update spatial index
        self.spatial_index.insert(unit)
        return True

    def place_unit_randomly(self, unit, max_attempts=50):
        """Attempts to place a unit at a random valid location."""
        for _ in range(max_attempts):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.place_unit(unit, x, y):
                return True
        return False

    def place_unit_near_edge(self, unit, edge, margin=10, max_attempts=50):
        """Attempts to place a unit near a specific edge."""
        for _ in range(max_attempts):
            x, y = 0, 0
            if edge == "top":
                x = random.randint(0, self.width - 1)
                y = random.randint(0, margin)
                unit.facing = 180 # Face Down
            elif edge == "bottom":
                x = random.randint(0, self.width - 1)
                y = random.randint(self.height - margin - 1, self.height - 1)
                unit.facing = 0 # Face Up
            elif edge == "left":
                x = random.randint(0, margin)
                y = random.randint(0, self.height - 1)
                unit.facing = 90 # Face Right
            elif edge == "right":
                x = random.randint(self.width - margin - 1, self.width - 1)
                y = random.randint(0, self.height - 1)
                unit.facing = 270 # Face Left
                
            if self.place_unit(unit, x, y):
                return True
                
        return False

    def move_unit(self, unit, new_x, new_y):
        """Teleports a unit to a new tile (one step or jump) handling multi-tile footprint."""
        grid_w, grid_h = getattr(unit, 'grid_size', [1, 1])
        
        # 1. Calculate New Footprint
        new_tiles = []
        for dx in range(grid_w):
            for dy in range(grid_h):
                nx, ny = new_x + dx, new_y + dy
                if not self.is_valid_tile(nx, ny):
                    return False
                new_tiles.append((nx, ny))
        
        # 2. Identify Current Footprint (to ignore self-collision)
        current_tiles = []
        for dx in range(grid_w):
            for dy in range(grid_h):
                 cx, cy = unit.grid_x + dx, unit.grid_y + dy
                 current_tiles.append((cx, cy))

        # 3. Check Collision (ignoring own current tiles)
        for tile in new_tiles:
            if tile in self.occupied_tiles:
                occupant = self.occupied_tiles[tile]
                if occupant != unit: 
                    return False # Collision with another unit
        
        # 4. Execute Move
        # Clear old
        for tile in current_tiles:
            if tile in self.occupied_tiles and self.occupied_tiles[tile] == unit:
                del self.occupied_tiles[tile]
                
        # Set new
        for tile in new_tiles:
            self.occupied_tiles[tile] = unit
            
        # Update Unit
        unit.grid_x = new_x
        unit.grid_y = new_y
        
        # New: Update spatial index
        self.spatial_index.remove(unit)
        self.spatial_index.insert(unit)
    def update_unit_position(self, unit, new_x, new_y):
        """High-frequency position update for real-time simulation (Spatial Index only)."""
        unit.grid_x = new_x
        unit.grid_y = new_y
        if self.spatial_index:
            self.spatial_index.remove(unit)
            self.spatial_index.insert(unit)
        return True

    def remove_unit(self, unit):
        """Clears a unit from the grid."""
        grid_w, grid_h = getattr(unit, 'grid_size', [1, 1])
        for dx in range(grid_w):
            for dy in range(grid_h):
                tile = (unit.grid_x + dx, unit.grid_y + dy)
                if tile in self.occupied_tiles and self.occupied_tiles[tile] == unit:
                    del self.occupied_tiles[tile]
        unit.is_deployed = False
        
        # New: Update spatial index
        self.spatial_index.remove(unit)
        return True

    def get_distance_coords(self, x1, y1, x2, y2):
        """Calculates Euclidean distance between two coordinates."""
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    def get_distance(self, unit_a, unit_b):
        """Calculates distance between two units."""
        if not hasattr(unit_a, 'grid_x') or not hasattr(unit_b, 'grid_x'):
            return 9999.0
        # Euclidean for accurate range measurement
        return self.get_distance_coords(unit_a.grid_x, unit_a.grid_y, unit_b.grid_x, unit_b.grid_y)
    
    def get_unit_at(self, x, y):
        return self.occupied_tiles.get((x, y))

    def get_valid_moves(self, unit):
        """Returns adjacent free tiles (Chebyshev/King movement)."""
        moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = unit.grid_x + dx, unit.grid_y + dy
                if self.is_valid_tile(nx, ny) and not self.is_occupied(nx, ny):
                    moves.append((nx, ny))
        return moves

    def rotate_unit(self, unit, target_facing):
        """Rotate unit respecting agility limits. Returns actual degrees turned."""
        current = getattr(unit, 'facing', 0)
        
        # Calculate shortest rotation
        diff = (target_facing - current) % 360
        if diff > 180:
            diff -= 360
            
        # Apply agility limit
        max_turn = getattr(unit, 'agility', 180)
        actual_turn = max(-max_turn, min(max_turn, diff))
        
        unit.facing = (current + actual_turn) % 360
        return actual_turn

    def get_relative_bearing(self, attacker, defender):
        """Calculate angle from attacker to defender relative to attacker's facing."""
        dx = defender.grid_x - attacker.grid_x
        dy = defender.grid_y - attacker.grid_y
        
        # Standard atan2: 0=East, 90=North (if Y up), -90=South
        # Our Grid: 0,0 Top Left. Y grows Down.
        # Vector to North (Up): (0, -1). 
        angle_rad = math.atan2(dy, dx) 
        angle_deg = math.degrees(angle_rad)
        
        # We want North=0. 
        # Screen Angle: East=0, South=90, West=180, North=270 / -90
        # Mapped: North=0, East=90, South=180, West=270
        # Formula: (Any Angle + 90) % 360
        bearing_geo = (angle_deg + 90) % 360
        
        # Relative to facing
        attacker_facing = getattr(attacker, 'facing', 0)
        relative = (bearing_geo - attacker_facing) % 360
        return relative

    def check_weapon_arc(self, attacker, defender, weapon_arc):
        """Check if target is in weapon's firing arc. (Prow, Broadside, Dorsal, Aft)"""
        bearing = self.get_relative_bearing(attacker, defender)
        
        if weapon_arc == "Prow":
            return bearing >= 315 or bearing <= 45
        elif weapon_arc == "Broadside":
             # 90 degrees left (270) -> 225-315
             # 90 degrees right (90) -> 45-135
             return (45 <= bearing <= 135) or (225 <= bearing <= 315)
        elif weapon_arc == "Aft":
            return 135 <= bearing <= 225
        # Dorsal or Unknown = All around
        return True

    def get_armor_facing(self, attacker, defender):
        """Determine which armor facing of the DEFENDER is hit."""
        # Relative bearing of ATTACKER from DEFENDER's perspective
        bearing = self.get_relative_bearing(defender, attacker)
        
        if bearing >= 315 or bearing <= 45:
            return getattr(defender, 'armor_front', defender.armor)
        elif 135 <= bearing <= 225:
            return getattr(defender, 'armor_rear', int(defender.armor * 0.5))
        else:
            return getattr(defender, 'armor_side', int(defender.armor * 0.75))



    # --- New Spatial Query Methods ---
    def query_units_in_range(self, center_x: float, center_y: float, radius: float, faction_filter: Optional[str] = None) -> List:
        """Query units within a circular range using the spatial index (or GPU)."""
        # GPU Acceleration Hook
        if self.gpu_tracker and self.gpu_tracker.positions is not None:
             # For now, GPU tracker is optimized for unit-to-unit. 
             # Arbitrary coord query requires a temporary "virtual unit" or custom kernel.
             # Given Phase 1 scope, we stick to CPU QuadTree for arbitrary coords 
             # UNLESS we add performant arbitrary query to GPUTracker.
             # fallback to spatial index for arbitrary points for now to be safe.
             pass

        candidates = self.spatial_index.query_circle(center_x, center_y, radius)
        if faction_filter:
            return [u for u in candidates if u.faction == faction_filter]
        return candidates

    def find_nearest_enemy(self, unit: Any, max_distance: Optional[float] = None) -> Optional[Any]:
        """Finds the nearest enemy unit using the spatial index or GPU."""
        
        # [GPU Acceleration Path]
        if self.gpu_tracker and self.gpu_tracker.positions is not None:
             # We assume gpu_tracker is up to date (managed by engine)
             neighbors = self.gpu_tracker.get_nearest_neighbors(unit, k=20)
             # neighbors is list of (unit, dist)
             
             for enemy, dist in neighbors:
                 if enemy.faction != unit.faction and enemy.is_alive():
                     if max_distance is None or dist <= max_distance:
                         return enemy
             return None

        # [CPU Fallback Path]
        # Query 10 nearest units as candidates
        candidates = self.spatial_index.query_nearest(unit.grid_x, unit.grid_y, count=10)
        
        # Filter for living enemies
        enemies = []
        for u, dist in candidates:
            if u != unit and u.faction != unit.faction and u.is_alive():
                if max_distance is None or dist <= max_distance:
                    enemies.append((u, dist))
        
        if not enemies:
            return None
            
        # Results from query_nearest are already sorted by distance
        return enemies[0][0]
