
from typing import List, Any, Dict, Set

class SpatialPoint:
    def __init__(self, x: float, y: float, data: Any):
        self.x = x
        self.y = y
        self.data = data

class SpatialGrid:
    """
    A simple 2D spatial grid for fast radius queries.
    Used to optimize Fleet-to-System distance checks (O(1) vs O(N)).
    """
    def __init__(self, width: float, height: float, cell_size: float = 50.0):
        self.cell_size = cell_size
        self.grid: Dict[str, List[SpatialPoint]] = {}
        self.width = width
        self.height = height

    def _get_key(self, x: float, y: float) -> str:
        cx = int(x // self.cell_size)
        cy = int(y // self.cell_size)
        return f"{cx},{cy}"

    def add(self, x: float, y: float, data: Any):
        key = self._get_key(x, y)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(SpatialPoint(x, y, data))

    def query_radius(self, x: float, y: float, radius: float) -> List[Any]:
        """Returns all items within radius (approximate/bucketted)."""
        # Determine strict bounds of query
        min_x, max_x = x - radius, x + radius
        min_y, max_y = y - radius, y + radius
        
        # Determine cell range
        start_cx = int(min_x // self.cell_size)
        end_cx = int(max_x // self.cell_size)
        start_cy = int(min_y // self.cell_size)
        end_cy = int(max_y // self.cell_size)
        
        results = []
        checked_keys = set()
        
        # Check all overlapping cells
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                key = f"{cx},{cy}"
                if key in checked_keys: continue
                checked_keys.add(key)
                
                if key in self.grid:
                    # Fine-grained check
                    for point in self.grid[key]:
                        # Distance squared check
                        dx = point.x - x
                        dy = point.y - y
                        if (dx*dx + dy*dy) <= (radius * radius):
                            results.append(point.data)
                            
        return results

    def clear(self):
        self.grid.clear()
