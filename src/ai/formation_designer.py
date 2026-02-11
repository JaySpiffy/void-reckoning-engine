import math
import random
from typing import List, Dict, Tuple, Any

class FormationDesigner:
    """
    Analyzes fleet composition and designs a tactical formation.
    Assigns units to Task Groups (Screen, Main, Rear, Flank) and 
    calculates relative offsets.
    """
    
    # Templates
    TEMPLATE_BOX = "BOX"
    TEMPLATE_WEDGE = "WEDGE"
    TEMPLATE_SPHERE = "SPHERE"
    TEMPLATE_ECHELON = "ECHELON"
    
    def __init__(self):
        pass
        
    def design_formation(self, fleet) -> Dict[str, Tuple[float, float]]:
        """
        Main entry point. 
        Returns a dict of {unit_id: (rel_x, rel_y)} relative to fleet center (0,0).
        """
        if not fleet or not fleet.units:
            return {}
            
        # 1. Analyze Composition & Assign Task Groups
        groups = self._assign_task_groups(fleet.units)
        
        # 2. Select Template (based on Doctrine or random)
        template = self._select_template(fleet)
        
        # 3. Calculate Offsets
        offsets = self._calculate_offsets_from_template(groups, template)
        
        # 4. Save metadata to fleet
        fleet.formation_settings = {
            "template": template,
            "groups": {k: [u.name for u in v] for k, v in groups.items()}
        }
        fleet.saved_formation = offsets
        
        return offsets

    def _assign_task_groups(self, units: List[Any]) -> Dict[str, List[Any]]:
        """
        Sorts units into tactical buckets.
        """
        groups = {
            "SCREEN": [],
            "MAIN": [],
            "REAR": [],
            "FLANK": []
        }
        
        for u in units:
            # Logic: Class/Role based
            u_class = getattr(u, 'ship_class', 'Escort')
            tags = u.abilities.get("Tags", []) if hasattr(u, "abilities") else []
            
            if "Transport" in tags or getattr(u, 'transport_capacity', 0) > 0:
                groups["REAR"].append(u)
            elif "Capital" in tags or u_class in ["Battleship", "Titan", "Dreadnought"]:
                groups["MAIN"].append(u)
            elif "Carrier" in tags:
                groups["REAR"].append(u)
            elif u_class == "Cruiser":
                 # Cruisers can be Flank or Main depending on loadout? 
                 # Randomize for flavor or check weapon range
                 groups["MAIN"].append(u)
            elif u_class == "Escort" or u_class == "Frigate":
                 # 20% Flank, 80% Screen
                 if random.random() < 0.2:
                     groups["FLANK"].append(u)
                 else:
                     groups["SCREEN"].append(u)
            else:
                 groups["MAIN"].append(u)
                 
        return groups

    def _select_template(self, fleet) -> str:
        """
        Decides the geometric shape.
        """
        # Could be based on Faction Doctrine
        return random.choice([
            self.TEMPLATE_BOX, 
            self.TEMPLATE_WEDGE, 
            self.TEMPLATE_SPHERE,
            self.TEMPLATE_ECHELON
        ])

    def _calculate_offsets_from_template(self, groups: Dict[str, List[Any]], template: str) -> Dict[str, Tuple[float, float]]:
        """
        Generates (x, y) offsets. 
        Axis: X is width, Y is depth (Front is +Y? No, usually +Y is up, let's say Facing is +X or +Y).
        Standard Grid: 
           +Y = North (Rear?) 
           -Y = South (Front?)
           
        Let's assume Fleet Forward is +Y.
        Center is (0,0).
        """
        offsets = {}
        
        # Spacing Constants
        SPACING = 4.0 
        
        # 1. Place MAIN Group (Center)
        # Main group usually forms the core.
        main_units = groups["MAIN"]
        self._layout_group(main_units, offsets, center=(0,0), shape=template, spacing=SPACING * 2)
        
        # 2. Place SCREEN Group (Front)
        screen_units = groups["SCREEN"]
        # In front of Main. 
        # Calculate Main's bounding box to know where "Front" is.
        # Simple heuristic: Front is Y + 15
        self._layout_group(screen_units, offsets, center=(0, 15), shape="ARC", spacing=SPACING)
        
        # 3. Place REAR Group (Back)
        rear_units = groups["REAR"]
        self._layout_group(rear_units, offsets, center=(0, -15), shape="BOX", spacing=SPACING * 2)
        
        # 4. Place FLANK Groups (Sides)
        flank_units = groups["FLANK"]
        # Split left/right
        left_flank = flank_units[:len(flank_units)//2]
        right_flank = flank_units[len(flank_units)//2:]
        
        self._layout_group(left_flank, offsets, center=(-20, 0), shape="LINE_VERT", spacing=SPACING)
        self._layout_group(right_flank, offsets, center=(20, 0), shape="LINE_VERT", spacing=SPACING)
        
        # Transform Object Keys to IDs for persistence
        final_offsets = {}
        for u, pos in offsets.items():
            uid = getattr(u, 'id', id(u))
            final_offsets[str(uid)] = pos
            
        return final_offsets

    def _layout_group(self, units: List[Any], offsets_out: Dict, center: Tuple[float, float], shape: str, spacing: float):
        """
        Lays out a specific list of units around a center point in a shape.
        """
        count = len(units)
        if count == 0: return
        
        cx, cy = center
        
        if shape == "BOX":
            # Grid layout
            cols = math.ceil(math.sqrt(count))
            rows = math.ceil(count / cols)
            
            for i, u in enumerate(units):
                r = i // cols
                c = i % cols
                # Center the grid
                x = cx + (c - cols/2) * spacing
                y = cy + (r - rows/2) * spacing
                offsets_out[u] = (x, y)
                
        elif shape == "LINE_VERT":
            # Line along Y axis
            start_y = cy - (count * spacing) / 2
            for i, u in enumerate(units):
                offsets_out[u] = (cx, start_y + i * spacing)
                
        elif shape == "ARC" or shape == self.TEMPLATE_WEDGE: # Wedge is essentially a V-shape arc
            # Arc facing +Y
            width = count * spacing
            radius = width # arbitrary radius
            angle_step = (math.pi / 2) / max(1, count) # Spread over 90 degrees
            start_angle = (math.pi - (math.pi/2)) / 2 # Centered on 90 deg (Up) -> 45 to 135
            
            # Actually easier: Simple V shape (Wedge)
            # Center is tip.
            # Alternating left/right and back
            offsets_out[units[0]] = (cx, cy) # Tip
            
            for i in range(1, count):
                layer = (i + 1) // 2
                side = 1 if i % 2 != 0 else -1
                
                # Back and Out
                x = cx + (side * layer * spacing)
                y = cy - (layer * spacing * 0.5) # Slight sweep back
                offsets_out[units[i]] = (x, y)

        elif shape == self.TEMPLATE_SPHERE or shape == "SPHERE":
            # Circle
            radius = math.sqrt(count) * spacing * 0.8
            for i, u in enumerate(units):
                angle = (2 * math.pi * i) / count
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                offsets_out[u] = (x, y)

        else:
            # Default Blobs (Box fallback)
            cols = math.ceil(math.sqrt(count))
            for i, u in enumerate(units):
                r = i // cols
                c = i % cols
                x = cx + (c - cols/2) * spacing
                y = cy + (r - cols/2) * spacing # Typo in rows usage, fixed here
                offsets_out[u] = (x, y)
