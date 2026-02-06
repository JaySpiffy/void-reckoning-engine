from typing import List, Dict, Any
from src.combat.combat_simulator import Unit

class ArmyGroup:
    """
    Phase 16: Represents a specific fighting force on a planet's surface.
    Moves between Province Nodes.
    """
    def __init__(self, army_id, faction, units, location_node):
        """
        Initializes an ArmyGroup representing a land force.
        
        Args:
            army_id (str): Unique identifier.
            faction (str): Faction capability.
            units (list): List of Unit objects in this army.
            location_node (GraphNode): Current position on the province graph.
        """
        self.id = army_id
        self.faction = faction
        self.units = list(units) if units else [] # List of combat_simulator.Unit
        self.location = location_node # GraphNode (Province/LZ/Capital)
        self.destination = None # GraphNode target
        self.is_destroyed = False
        
        # Phase 33: Total War Mechanics
        self.state = "IDLE" # IDLE, MOVING, GARRISONED, EMBARKED
        self.transport_fleet = None # Reference to Fleet object if EMBARKED
        self.movement_points = 1.0 # Base movement per turn
        self.current_mp = 1.0
        self.public_order_bonus = 0 # If Garrisoned
        self._is_engaged = False
        
        # [FEATURE] Strategic Retreat Limit
        self.has_retreated_this_turn = False

        self._capability_matrix_dirty = True
        self._cached_capability_matrix = {}
        
    def reset_turn(self):
        """Replenishes movement points at start of turn."""
        self.current_mp = self.movement_points

    def reset_turn_flags(self):
        """Resets turn-based behavior flags at start of turn."""
        self.has_retreated_this_turn = False
        self.reset_turn()

    def move_to(self, target_node, engine=None):
        """
        Orders the army to move to a specific node on the hex map.
        Sets the destination and changes state to MOVING.
        """
        if self.location == target_node:
            return True # Already there

        self.destination = target_node
        self.state = "MOVING"
        
        # Immediate movement attempt if we have MP remaining
        if self.current_mp > 0 and engine:
             self.update_movement(engine)
        return True

    def update_movement(self, engine):
        """
        Processes movement along a path to the destination.
        Deducts MP based on terrain and handles arrival.
        """
        if self.state != "MOVING" or not self.destination:
            return

        if self.location == self.destination:
            self.state = "IDLE"
            self.destination = None
            return

        # 1. Get Path (A* terrain-aware pathfinding)
        # Using engine.pathfinder directly
        if not hasattr(engine, 'pathfinder'):
             return

        path_nodes, cost, meta = engine.pathfinder.find_path(self.location, self.destination, is_ground=True)
        
        if not path_nodes or len(path_nodes) < 2:
             # Cannot find path or blocked
             if engine.logger:
                  engine.logger.campaign(f"  > [BLOCKED] Army {self.id} cannot find path to {self.destination.id}")
             self.state = "IDLE"
             self.destination = None
             return

        # 2. Step through nodes while MP allows
        while self.current_mp > 0 and self.destination and self.location != self.destination:
             # Re-evaluate path step by step to handle dynamic blockades or terrain changes
             current_path, _, _ = engine.pathfinder.find_path(self.location, self.destination, is_ground=True)
             if not current_path or len(current_path) < 2:
                  break
                  
             next_node = current_path[1]
             
             # Calculate Terrain Cost
             terrain_cost = 1.0
             if hasattr(next_node, 'terrain_type'):
                  terrain = next_node.terrain_type
                  if terrain == "Mountain":
                       terrain_cost = 2.0
                  elif terrain == "Water":
                       # Should not happen with ground pathfinding, but safety first
                       break
             
             if self.current_mp >= terrain_cost:
                  self.current_mp -= terrain_cost
                  old_loc = self.location
                  self.location = next_node
                  
                  if hasattr(old_loc, 'armies') and self in old_loc.armies:
                       old_loc.armies.remove(self)
                  if hasattr(next_node, 'armies') and self not in next_node.armies:
                       next_node.armies.append(self)
                  
                  if engine.logger:
                       engine.logger.campaign(f"  > [MOVE] Army {self.id} moved to {next_node.id} (Cost: {terrain_cost}, MP Left: {self.current_mp})")
             else:
                  # Not enough MP
                  break
        
        # Check if arrived after loop
        if self.location == self.destination:
            self.state = "IDLE"
            self.destination = None
            if engine.logger:
                engine.logger.campaign(f"Army {self.id} arrived at {self.location.id}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Serializes army state for Save V2."""
        return {
            "id": self.id,
            "faction": self.faction,
            "units": [u.to_dict() for u in self.units],
            "location_id": getattr(self.location, "id", "unknown"),
            "destination_id": getattr(self.destination, "id", None),
            "state": self.state,
            "is_destroyed": self.is_destroyed,
            "is_destroyed": self.is_destroyed,
            "transport_fleet_id": getattr(self.transport_fleet, "id", None),
            "has_retreated_this_turn": self.has_retreated_this_turn
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any], location_node: Any) -> 'ArmyGroup':
        """Hydrates an ArmyGroup from a dictionary (Save V2)."""
        from src.builders.unit_builder import UnitBuilder
        
        units = []
        for u_data in data.get("units", []):
            units.append(UnitBuilder.from_dict(u_data))
            
        army = cls(
            army_id=data["id"],
            faction=data["faction"],
            units=units,
            location_node=location_node
        )
        army.state = data.get("state", "IDLE")
        army.is_destroyed = data.get("is_destroyed", False)
        army.is_destroyed = data.get("is_destroyed", False)
        army._is_engaged = data.get("is_engaged", False)
        army.has_retreated_this_turn = data.get("has_retreated_this_turn", False)
        
        return army

    @property
    def is_engaged(self):
        return self._is_engaged
    
    @is_engaged.setter
    def is_engaged(self, value):
        self._is_engaged = value
        
    def retreat(self, target_node):
        """
        Phase 18: Armies can now break engagement to retreat.
        [LIMIT] Can only retreat once per turn.
        """
        if self.has_retreated_this_turn:
            print(f"  > [FORCED FIGHT] Army {self.id} has already retreated this turn and MUST STAND AND FIGHT!")
            return False

        if not self.is_engaged:
            self.destination = target_node
            self.state = "MOVING"
            self.has_retreated_this_turn = True
            return True
            
        # If engaged, breaking out requires a special check or just 
        # unlocking the unit.
        print(f"  > [RETREAT] Army {self.id} BREAKING ENGAGEMENT to retreat to {target_node.name if hasattr(target_node, 'name') else target_node}")
        self.is_engaged = False
        self.destination = target_node
        self.state = "MOVING"
        self.has_retreated_this_turn = True
        return True

    def found_city(self, engine):
        """
        [FEATURE R23] Transforms the current hex into a Province Capital (City).
        Consumes units as settlers.
        """
        if not self.location or not hasattr(self.location, 'can_found_city'):
            return False, "Invalid location"
            
        if not self.location.can_found_city():
            return False, f"Terrain {getattr(self.location, 'terrain_type', 'Unknown')} is unsuitable for a city."

        if not self.units:
            return False, "No units to settle."

        # 1. Determine Settlement Cost (Abstracted population)
        # Check for Settler trait (halves cost)
        has_settlers = any("Settler" in getattr(u, 'traits', []) for u in self.units)
        
        # Base: Consumes up to 10 units or 50% of the army
        # Settler: Consumes up to 5 units or 25% of the army
        base_rate = 0.25 if has_settlers else 0.5
        base_min = 5 if has_settlers else 10
        
        target_consumption = max(base_min, int(len(self.units) * base_rate))
        actual_consumed = 0
        
        # Priority: Pioneers/Settlers move to the front of consumption list if we add them later
        # For now, just pop from the end
        while actual_consumed < target_consumption and self.units:
            self.units.pop()
            actual_consumed += 1
            
        # 2. Transform the Hex
        self.location.terrain_type = "City"
        self.location.type = "ProvinceCapital"
        self.location.building_slots = 5
        self.location.max_tier = 4
        self.location.name = f"Colony {self.location.q},{self.location.r}"
        
        # 3. Update Planet/Economy
        planet = self.location.metadata.get("object")
        if planet and hasattr(planet, 'recalc_stats'):
            planet.recalc_stats()
            planet.update_economy_cache()
            
        # 4. Cleanup Army
        if not self.units:
            self.is_destroyed = True
            if hasattr(self.location, 'armies') and self in self.location.armies:
                self.location.armies.remove(self)
        
        # 5. Telemetry
        if engine and getattr(engine, 'telemetry', None):
            from src.reporting.telemetry import EventCategory
            engine.telemetry.log_event(
                EventCategory.CONSTRUCTION,
                "city_founded",
                {
                    "planet": planet.name if planet else "Unknown",
                    "hex": f"{self.location.q},{self.location.r}",
                    "consumed_units": actual_consumed,
                    "army_id": self.id
                },
                turn=getattr(engine, 'turn_counter', 0),
                faction=self.faction
            )
            
        return True, f"City founded on {self.location.id}. Consumed {actual_consumed} units."

    @property
    def power(self):
        return sum(u.strength for u in self.units)

    def remove_casualties(self, count):
        """Removes 'count' units from the army. Returns actual removed count."""
        removed = 0
        for _ in range(count):
            if self.units:
                self.units.pop()
                removed += 1
        if not self.units:
            self.is_destroyed = True
        return removed
            
    def _get_unit_size(self, u):
        size = 1
        tags = u.abilities.get("Tags", [])
        if "Vehicle" in tags: size = 2
        if "Monster" in tags: size = 3
        if "Titanic" in tags: size = 10
        return size

    def get_total_size(self):
        total = 0
        for u in self.units:
            total += self._get_unit_size(u)
        return total

    def get_capability_matrix(self) -> Dict[str, int]:
        """
        Categorizes land units into refined roles.
        Returns: {"Infantry": int, "Armor": int, "Artillery": int, "Titan": int, "Scout": int}
        """
        if not self._capability_matrix_dirty:
            return self._cached_capability_matrix
            
        matrix = {
            "Infantry": 0,
            "Armor": 0,
            "Artillery": 0,
            "Titan": 0,
            "Scout": 0
        }
        
        for u in self.units:
            # Classification logic aligned with RecruitmentService
            roles = getattr(u, "tactical_roles", [])
            tags = u.abilities.get("Tags", []) if hasattr(u, "abilities") else []
            traits = getattr(u, "traits", [])
            name = u.name.lower()
            
            if "Titan" in tags or "Super-Heavy" in tags or "Titan" in roles or u.cost > 1000:
                matrix["Titan"] += 1
            elif "Tank" in tags or "Vehicle" in tags or "Armor" in tags or "Monster" in tags or "Armor" in roles:
                matrix["Armor"] += 1
            elif "Artillery" in tags or "Ranged" in tags or "Artillery" in roles:
                matrix["Artillery"] += 1
            elif "Scout" in traits or "Infiltrator" in tags or "Scout" in roles:
                matrix["Scout"] += 1
            else:
                matrix["Infantry"] += 1

        self._cached_capability_matrix = matrix
        self._capability_matrix_dirty = False
        return matrix

    def split_off(self, unit_count=None, capacity_limit=None, ratio=0.5):
        """
        Splits off a new ArmyGroup. 
        If capacity_limit is provided, splits based on volume (e.g. for transport). 
        Otherwise uses unit_count or ratio.
        """
        if not self.units:
            return None
            
        new_units = []
        remaining_units = []
        
        if capacity_limit is not None:
             current_load = 0
             for u in self.units:
                u_size = self._get_unit_size(u)
                if current_load + u_size <= capacity_limit:
                    new_units.append(u)
                    current_load += u_size
                else:
                    remaining_units.append(u)
        else:
            total = len(self.units)
            if unit_count is not None:
                move_count = min(unit_count, total)
            else:
                move_count = int(total * ratio)
            
            if move_count <= 0:
                return None
                
            new_units = self.units[-move_count:]
            remaining_units = self.units[:-move_count]
            
        if not new_units:
            return None # Cannot split something small enough?
            
        # Apply Split
        self.units = remaining_units
        if not self.units:
            self.is_destroyed = True # Phase 36: Destroy empty shell
            
        print(f"DEBUG: Splitting Army {self.id}. New size: {len(self.units)}. Split force: {len(new_units)}")
        
        # Create New Army
        # Prevent recursive naming (e.g. Name_Detachment_Detachment)
        base_id = self.id.split("_Detachment")[0]
        # Use a short random suffix to ensure uniqueness without exploding length
        import random
        suffix = random.randint(1000, 9999)
        new_id = f"{base_id}_Detachment_{suffix}"
        
        new_army = ArmyGroup(new_id, self.faction, new_units, self.location)
        new_army.state = self.state
        
        self._capability_matrix_dirty = True
        return new_army

    def merge_with(self, other_army):
        """Absorbs units from another army group."""
        if other_army.faction != self.faction:
            return False
            
        self.units.extend(other_army.units)
        other_army.units = [] # Empty the other army
        other_army.is_destroyed = True
        self._capability_matrix_dirty = True
        return True
