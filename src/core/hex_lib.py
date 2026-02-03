import math
from dataclasses import dataclass
from typing import List, Tuple, Set, Iterator

@dataclass(frozen=True)
class Hex:
    """
    Immutable value object representing a Hexagon in Axial Coordinates (q, r).
    s is derived as -q - r.
    """
    q: int
    r: int

    @property
    def s(self) -> int:
        return -self.q - self.r

    def __add__(self, other: 'Hex') -> 'Hex':
        return Hex(self.q + other.q, self.r + other.r)

    def __sub__(self, other: 'Hex') -> 'Hex':
        return Hex(self.q - other.q, self.r - other.r)

    def __mul__(self, other: int) -> 'Hex':
        if isinstance(other, int):
            return Hex(self.q * other, self.r * other)
        return NotImplemented
        
    def __rmul__(self, other: int) -> 'Hex':
        return self.__mul__(other)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hex):
            return False
        return self.q == other.q and self.r == other.r

    def __hash__(self) -> int:
        return hash((self.q, self.r))

    def length(self) -> int:
        """Returns the distance from (0, 0, 0)."""
        return int((abs(self.q) + abs(self.r) + abs(self.s)) / 2)

    def distance(self, other: 'Hex') -> int:
        """Returns the Manhattan distance on the hex grid."""
        return (self - other).length()
    
    def neighbor(self, direction: int) -> 'Hex':
        """Returns the neighbor in the given direction (0-5)."""
        return self + HEX_DIRECTIONS[direction % 6]
    
    def get_neighbors(self) -> List['Hex']:
        """Returns all 6 adjacent hexes."""
        return [self + d for d in HEX_DIRECTIONS]

    def to_pixel(self, size: float) -> Tuple[float, float]:
        """Converts axial coords to pixel (x, y) for visualization."""
        x = size * (3/2 * self.q)
        y = size * (math.sqrt(3)/2 * self.q + math.sqrt(3) * self.r)
        return (x, y)

    @staticmethod
    def from_pixel(x: float, y: float, size: float) -> 'Hex':
        """Fractional hex from pixel, then rounded to nearest integer hex."""
        q = (2./3 * x) / size
        r = (-1./3 * x + math.sqrt(3)/3 * y) / size
        return _hex_round(q, r)
        
    def __repr__(self):
        return f"Hex({self.q}, {self.r})"


# Directions for neighbors (starting East, going clockwise?)
# Convention: 0=Right(East), 1=BottomRight, 2=BottomLeft, 3=Left, 4=TopLeft, 5=TopRight
HEX_DIRECTIONS = [
    Hex(1, 0), Hex(0, 1), Hex(-1, 1), 
    Hex(-1, 0), Hex(0, -1), Hex(1, -1)
]

def _hex_round(fq: float, fr: float) -> Hex:
    """Rounds fractional coordinates to the nearest valid integer hex."""
    fs = -fq - fr
    q = round(fq)
    r = round(fr)
    s = round(fs)

    q_diff = abs(q - fq)
    r_diff = abs(r - fr)
    s_diff = abs(s - fs)

    if q_diff > r_diff and q_diff > s_diff:
        q = -r - s
    elif r_diff > s_diff:
        r = -q - s
    # s is implied, no need to set it

    return Hex(q, r)

class HexGrid:
    """
    Utility class for grid operations (rings, spirals, storage).
    """
    @staticmethod
    def get_ring(center: Hex, radius: int) -> List[Hex]:
        """Returns all hexes exactly 'radius' distance away."""
        if radius <= 0: return [center] if radius == 0 else []
        
        results = []
        # Start at neighbor 4 (TopLeftish) scaled by radius
        # Typically ring algorithm: 
        # Start at center + (direction_4 * radius)
        # Then walk radius steps in each of the 6 directions
        
        current = center + (HEX_DIRECTIONS[4] * radius)
        
        for i in range(6):
            for _ in range(radius):
                results.append(current)
                current = current.neighbor(i)
                
        return results

    @staticmethod
    def get_spiral(center: Hex, radius: int) -> Iterator[Hex]:
        """Generates hexes in a spiral outward from center."""
        yield center
        for r in range(1, radius + 1):
            
            # Start at neighbor 4 scaled by ring radius
            current = center + (HEX_DIRECTIONS[4] * r)
            
            for i in range(6):
                for _ in range(r):
                    yield current
                    current = current.neighbor(i)
