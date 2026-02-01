from typing import List, Optional, Tuple, Any, Dict
from dataclasses import dataclass

@dataclass
class BoundingBox:
    """Axis-aligned bounding box for spatial queries."""
    x: float
    y: float
    width: float
    height: float
    
    def contains(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)
                
    def intersects(self, other: 'BoundingBox') -> bool:
        return not (self.x + self.width < other.x or
                  other.x + other.width < self.x or
                  self.y + self.height < other.y or
                  other.y + other.height < self.y)

class QuadTreeNode:
    """Node in the quadtree spatial partition."""
    
    MAX_OBJECTS = 10
    MAX_DEPTH = 8
    
    def __init__(self, bounds: BoundingBox, depth: int = 0):
        self.bounds = bounds
        self.depth = depth
        self.objects: List[Any] = []
        self.children: Optional[List['QuadTreeNode']] = None
        
    def insert(self, obj: Any) -> bool:
        """Insert an object into the quadtree. Object must have grid_x and grid_y attributes."""
        if not hasattr(obj, 'grid_x') or not hasattr(obj, 'grid_y'):
            return False

        if not self.bounds.contains(obj.grid_x, obj.grid_y):
            return False
            
        if self.children is None:
            if len(self.objects) < self.MAX_OBJECTS or self.depth >= self.MAX_DEPTH:
                self.objects.append(obj)
                return True
            self._split()
            
        # Try to insert into children
        for child in self.children:
            if child.insert(obj):
                return True
                
        # If it fits in bounds but children failed (shouldn't happen with correct split), 
        # or it's on a boundary, keep in this node
        self.objects.append(obj)
        return True
        
    def remove(self, obj: Any) -> bool:
        """Remove an object from the quadtree."""
        if not hasattr(obj, 'grid_x') or not hasattr(obj, 'grid_y'):
            return False

        if not self.bounds.contains(obj.grid_x, obj.grid_y):
            return False
            
        if obj in self.objects:
            self.objects.remove(obj)
            return True
            
        if self.children:
            for child in self.children:
                if child.remove(obj):
                    return True
                    
        return False
        
    def query_range(self, bounds: BoundingBox) -> List[Any]:
        """Query all objects within a bounding box."""
        found = []
        
        if not self.bounds.intersects(bounds):
            return found
            
        for obj in self.objects:
            if bounds.contains(obj.grid_x, obj.grid_y):
                found.append(obj)
                
        if self.children:
            for child in self.children:
                found.extend(child.query_range(bounds))
                
        return found
        
    def query_circle(self, center_x: float, center_y: float, 
                    radius: float) -> List[Any]:
        """Query all objects within a circular radius."""
        # Create bounding box for circle for initial filtering
        bounds = BoundingBox(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2
        )
        
        candidates = self.query_range(bounds)
        
        # Filter by actual Euclidean distance
        found = []
        radius_sq = radius * radius
        for obj in candidates:
            dx = obj.grid_x - center_x
            dy = obj.grid_y - center_y
            if dx*dx + dy*dy <= radius_sq:
                found.append(obj)
                
        return found
        
    def query_nearest(self, center_x: float, center_y: float,
                       count: int = 1) -> List[Tuple[Any, float]]:
        """Query N nearest objects to a point."""
        # This is a naive implementation: query a reasonably large range first
        # For a truly optimized nearest neighbor search, we would need a more complex
        # algorithm that traverses the tree by distance.
        # Given our 100x100 grid, querying a 50x50 area is usually sufficient or 
        # we can just query the whole tree and sort.
        
        # Implementation: Start with a radius that likely contains 'count' objects
        # and expand if necessary.
        radius = 10.0
        while radius <= self.bounds.width:
            candidates = self.query_circle(center_x, center_y, radius)
            if len(candidates) >= count:
                break
            radius *= 2.0
        else:
            # Last resort: query entire tree
            candidates = self.query_range(BoundingBox(0, 0, 1000, 1000)) # Larger than grid

        results = []
        for obj in candidates:
            dx = obj.grid_x - center_x
            dy = obj.grid_y - center_y
            dist = (dx*dx + dy*dy)**0.5
            results.append((obj, dist))
            
        results.sort(key=lambda x: x[1])
        return results[:count]
        
    def _split(self) -> None:
        """Split this node into 4 children."""
        half_w = self.bounds.width / 2
        half_h = self.bounds.height / 2
        mid_x = self.bounds.x + half_w
        mid_y = self.bounds.y + half_h
        
        self.children = [
            QuadTreeNode(BoundingBox(self.bounds.x, self.bounds.y, half_w, half_h), self.depth + 1),  # Top-Left
            QuadTreeNode(BoundingBox(mid_x, self.bounds.y, half_w, half_h), self.depth + 1),          # Top-Right
            QuadTreeNode(BoundingBox(self.bounds.x, mid_y, half_w, half_h), self.depth + 1),          # Bottom-Left
            QuadTreeNode(BoundingBox(mid_x, mid_y, half_w, half_h), self.depth + 1),                  # Bottom-Right
        ]
        
        # Re-insert existing objects into children
        old_objects = self.objects
        self.objects = []
        for obj in old_objects:
            moved = False
            for child in self.children:
                if child.insert(obj):
                    moved = True
                    break
            if not moved:
                self.objects.append(obj) # Keep it here if it doesn't fit in children

class QuadTree:
    """
    Quadtree spatial partition for efficient spatial queries.
    Provides O(log n) average case for range and nearest neighbor queries.
    """
    
    def __init__(self, width: float = 100, height: float = 100):
        self.width = width
        self.height = height
        self.root = QuadTreeNode(BoundingBox(0, 0, width, height))
        
    def insert(self, obj: Any) -> bool:
        """Insert an object into the spatial partition."""
        return self.root.insert(obj)
        
    def remove(self, obj: Any) -> bool:
        """Remove an object from the spatial partition."""
        return self.root.remove(obj)
        
    def query_range(self, x: float, y: float, 
                   width: float, height: float) -> List[Any]:
        """Query all objects within a rectangular area."""
        bounds = BoundingBox(x, y, width, height)
        return self.root.query_range(bounds)
        
    def query_circle(self, center_x: float, center_y: float, 
                    radius: float) -> List[Any]:
        """Query all objects within a circular radius."""
        return self.root.query_circle(center_x, center_y, radius)
        
    def query_nearest(self, center_x: float, center_y: float,
                       count: int = 1) -> List[Tuple[Any, float]]:
        """Query N nearest objects to a point."""
        return self.root.query_nearest(center_x, center_y, count)
    
    def clear(self) -> None:
        """Clear all objects from the spatial partition."""
        self.root = QuadTreeNode(BoundingBox(0, 0, self.width, self.height))
