import math
from typing import List, Tuple, Any, Dict

class Formation:
    """
    Manages a group of entities in various geometric shapes (Rectangle, Wedge, Loose, Wall).
    """
    def __init__(self, entities: List[Any], columns: int = 10, spacing: float = 1.0, formation_type: str = "Rectangle"):
        self.entities = entities
        self.columns = columns
        self.spacing = spacing
        self.formation_type = formation_type
        self.center_x = 0.0
        self.center_y = 0.0
        self.facing = 0.0 # Degrees (Compass Grid: 0=N, 90=E)
        
    def get_modifiers(self) -> Dict[str, float]:
        """Returns stat modifiers applied to all units in this formation."""
        # --- Ground Formations ---
        if self.formation_type == "Wedge":
            return {"movement_speed_mult": 1.2, "charge_damage_mult": 1.5, "defense_mult": 0.8}
        elif self.formation_type == "Loose":
             return {"aoe_resilience": 2.0, "defense_mult": 0.9}
        elif self.formation_type == "Wall":
             return {"defense_mult": 1.3, "movement_speed_mult": 0.7}
        
        # --- Fleet Formations (Phase 30) ---
        elif self.formation_type == "Line of Battle":
            return {"damage_mult": 1.15, "ap_bonus": 10, "movement_speed_mult": 0.8}
        elif self.formation_type == "Assault Spearhead":
            return {"movement_speed_mult": 1.25, "accuracy_mult": 1.2, "defense_mult": 0.85}
        elif self.formation_type == "Escort Screen":
            # Modified by unit type externally? Or use tags in phase
            return {"evasion_mult": 1.3, "shield_regen_mult": 1.2}
            
        return {}
        
    def update_center(self):
        if not self.entities: return
        self.center_x = sum(e.grid_x for e in self.entities) / len(self.entities)
        self.center_y = sum(e.grid_y for e in self.entities) / len(self.entities)
        
    def get_slot_offset(self, index: int) -> Tuple[float, float]:
        """
        Calculates the relative (x, y) offset based on formation type.
        """
        if self.formation_type == "Wedge":
            return self._get_wedge_offset(index)
        elif self.formation_type == "Wall":
             return self._get_wall_offset(index)
        elif self.formation_type == "Loose":
             return self._get_rect_offset(index, spacing_mult=2.5)
        else: # Default Rectangle
            return self._get_rect_offset(index)

    def _get_rect_offset(self, index: int, spacing_mult: float = 1.0) -> Tuple[float, float]:
        spacing = self.spacing * spacing_mult
        row = index // self.columns
        col = index % self.columns
        
        rows = (len(self.entities) + self.columns - 1) // self.columns
        offset_x = (col - (self.columns - 1) / 2) * spacing
        # Invert Y: Row 0 is at the FRONT (+Forward)
        offset_y = - (row - (rows - 1) / 2.0) * spacing
        
        return self._rotate_offset(offset_x, offset_y)

    def _get_wedge_offset(self, index: int) -> Tuple[float, float]:
        """Triangular wedge. Row R has R+1 units. Row 0 (Tip) is Forward."""
        row = int(math.sqrt(2 * index + 0.25) - 0.5)
        row_start_index = row * (row + 1) // 2
        pos_in_row = index - row_start_index
        
        offset_x = (pos_in_row - row / 2.0) * self.spacing
        # Row 0 is Tip. Row 1 is BEHIND it (-oy).
        offset_y = -row * self.spacing
        
        return self._rotate_offset(offset_x, offset_y)

    def _get_wall_offset(self, index: int) -> Tuple[float, float]:
        """Vertical wall. Column 0 is Front Layer."""
        height = self.columns 
        layer = index // height
        pos = index % height
        
        # Layer 0 is Front (+oy)
        offset_x = (pos - (height - 1) / 2.0) * self.spacing
        offset_y = -layer * self.spacing 
        
        return self._rotate_offset(offset_x, offset_y)

    def _rotate_offset(self, ox: float, oy: float) -> Tuple[float, float]:
        """
        Rotates relative offsets to align with grid facing.
        Facing: 0=North (-Y), 90=East (+X), 180=South (+Y), 270=West (-X).
        Forward (oy) aligns with facing. Sideways (ox) is perpendicular.
        """
        rad = math.radians(self.facing)
        cos_f = math.cos(rad)
        sin_f = math.sin(rad)
        
        # Forward Vector: (sin(f), -cos(f))
        # Sideways Vector: (cos(f), sin(f))
        rot_x = ox * cos_f + oy * sin_f
        rot_y = ox * sin_f - oy * cos_f
        
        return rot_x, rot_y

    def get_target_positions(self) -> List[Tuple[float, float]]:
        """
        Returns absolute (x, y) target positions for every entity.
        """
        self.update_center()
        positions = []
        for i in range(len(self.entities)):
            ox, oy = self.get_slot_offset(i)
            positions.append((self.center_x + ox, self.center_y + oy))
        return positions
