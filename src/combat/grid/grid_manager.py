from typing import List, Optional, Any, Dict
from src.combat.tactical_grid import TacticalGrid

class GridManager:
    """
    Manages tactical grid and spatial queries (Phase 4).
    Wraps TacticalGrid for better abstraction.
    """
    def __init__(self, width: int, height: int, map_type: str = "Ground"):
        self.width = width
        self.height = height
        self.grid = TacticalGrid(width, height, map_type=map_type)
        
    def place_unit(self, unit: Any, x: int, y: int) -> bool:
        return self.grid.place_unit(unit, x, y)
        
    def get_distance(self, unit_a: Any, unit_b: Any) -> float:
        return self.grid.get_distance(unit_a, unit_b)
        
    def get_units_in_radius(self, x: float, y: float, radius: float) -> List[Any]:
        return self.grid.query_units_in_range(x, y, radius)
        
    def is_valid_tile(self, x: int, y: int) -> bool:
        return self.grid.is_valid_tile(x, y)
        
    def is_occupied(self, x: int, y: int) -> bool:
        return self.grid.is_occupied(x, y)
        
    def move_unit(self, unit: Any, new_x: int, new_y: int) -> None:
        return self.grid.move_unit(unit, new_x, new_y)

    def remove_unit(self, unit: Any) -> bool:
        return self.grid.remove_unit(unit)
        
    def get_unit_at(self, x: int, y: int) -> Optional[Any]:
        return self.grid.get_unit_at(x, y)

    def get_valid_moves(self, unit: Any) -> List[tuple]:
        return self.grid.get_valid_moves(unit)
    
    def find_nearest_enemy(self, unit: Any, max_distance: Optional[float] = None) -> Optional[Any]:
        return self.grid.find_nearest_enemy(unit, max_distance)
