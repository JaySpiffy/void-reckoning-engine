import random
import time
import copy
from typing import Dict, Any, List
import numpy as np
from src.models.unit import Unit, Ship, Regiment
from src.core.simulation_topology import GraphNode
from src.models.army import ArmyGroup
from src.core import balance as bal
from src.utils.profiler import profile_method
from src.reporting.telemetry import EventCategory
from src.config import logging_config
import json
import weakref

# Combat Doctrines
DOCTRINE_CHARGE = "CHARGE"
DOCTRINE_KITE = "KITE"
DOCTRINE_DEFEND = "DEFEND"

class Fleet:
    def __init__(self, fleet_id, faction, start_planet):
        """
        Initializes a Fleet (navy) object.
        
        Args:
            fleet_id (str): Unique fleet ID.
            faction (str): Faction owner.
            start_planet (Planet): Starting location.
        """
        self.id = fleet_id
        self.faction = faction
        self.location = start_planet # Planet Object
        self.destination = None # Planet Object
        self.travel_progress = 0
        self.travel_duration = 0
        
        self.units = [] # List of Unit objects
        self.is_destroyed = False
        
        # Economy (Local fleet fund)
        self.requisition = bal.FLEET_STARTING_REQ
        
        # Phase 33: Transport Capacity
        self.cargo_armies = [] # List of ArmyGroup objects embarkred

        # Phase 15: Graph Movement
        self.current_node = None # GraphNode
        self.route = [] # List of GraphNode (Path)
        self.travel_progress = 0
        self.current_edge_cost = 0
        
        # Phase 17: Persistent Warfare
        self.is_engaged = False
        
        # Initialize Node Position
        # Fix for "No Graph Node" Error: Handle GraphNode passed directly
        if hasattr(self.location, "node_reference"):
            self.current_node = self.location.node_reference
        elif isinstance(self.location, GraphNode):
            self.current_node = self.location
            # ensure location is kept as the node if it's a node
        elif hasattr(self.location, "type") and self.location.type in ["FluxPoint", "DeepSpace", "Planet"]:
             # Duck typing for GraphNode
             self.current_node = self.location
             
        self.is_scout = False
        self.exploration_target_system = None
        self.patrol_turns = 0
        
        # Phase 5: Theater Operations
        self.assigned_theater_id = None # Logic: If set, restricts movement to theater systems.

        # Phase 23: Portal Transit State
        self.in_portal_transit = False
        self.portal_entry_turn = None
        self.portal_destination_universe = None
        self.portal_exit_node_id = None
        self.portal_aware = False # Flag for AI/Logic to know this fleet understands portals
        
        # Phase 16.5: Attacker-Lose Logic
        self.arrived_this_turn = False
        
        # Performance Caching Flags
        self._speed_dirty = True
        self._cached_speed = bal.FLEET_SPEED_DEFAULT
        
        # Phase 6: Advanced Tactics
        # "CLOSE_QUARTERS", "KITE", "HOLD_GROUND", "HIT_AND_RUN"
        self.tactical_directive = "HOLD_GROUND" 
        self._power_dirty = True
        self._cached_power = 0
        self._transport_capacity_dirty = True
        self._cached_transport_capacity = 0
        self._used_capacity_dirty = True
        self._cached_used_capacity = 0

        self._capability_matrix_dirty = True
        self._cached_capability_matrix = {}
        
        # Movement Telemetry Tracking
        self._movement_start_turn = None
        self._movement_start_location = None
        self._movement_path_length = 0
        self._movement_nodes_visited = []
        self._movement_expected_duration = 0
        
        # [FEATURE] Strategic Retreat Limit
        self.has_retreated_this_turn = False
    
    def reset_turn_flags(self):
        """Resets turn-based behavior flags at start of turn."""
        self.arrived_this_turn = False
        self.has_retreated_this_turn = False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes fleet state for Save V2."""
        return {
            "id": self.id,
            "faction": self.faction,
            "location_name": getattr(self.location, "name", "unknown"),
            "destination_name": getattr(self.destination, "name", None),
            "travel_progress": self.travel_progress,
            "travel_duration": self.travel_duration,
            "is_destroyed": self.is_destroyed,
            "requisition": self.requisition,
            "units": [u.to_dict() for u in self.units],
            "cargo_armies": [a.to_dict() for a in self.cargo_armies],
            "tactical_directive": self.tactical_directive,
            "has_retreated_this_turn": self.has_retreated_this_turn,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], location: Any) -> 'Fleet':
        """Hydrates a Fleet from a dictionary (Save V2)."""
        from src.builders.unit_builder import UnitBuilder
        
        fleet = cls(
            fleet_id=data["id"],
            faction=data["faction"],
            start_planet=location
        )
        fleet.units = [UnitBuilder.from_dict(u_data) for u_data in data.get("units", [])]
        for u in fleet.units:
             if hasattr(u, 'set_fleet'): u.set_fleet(fleet)
        fleet.travel_progress = data.get("travel_progress", 0)
        fleet.travel_duration = data.get("travel_duration", 0)
        fleet.is_destroyed = data.get("is_destroyed", False)
        fleet.requisition = data.get("requisition", bal.FLEET_STARTING_REQ)
        fleet.tactical_directive = data.get("tactical_directive", "HOLD_GROUND")
        fleet.tactical_directive = data.get("tactical_directive", "HOLD_GROUND")
        fleet.is_scout = data.get("is_scout", False)
        fleet.has_retreated_this_turn = data.get("has_retreated_this_turn", False)
        
        return fleet

    # Phase 39: Speed Base
    # self.speed is now a property based on contents (see below)

    @property
    def speed(self) -> int:
        """
        Calculates fleet speed based on the slowest ship class.
        Escort: 8, Cruiser: 4, Battleship: 2. Default: 8.
        """
        if not self._speed_dirty:
            return self._cached_speed
            
        if not self.units:
            self._cached_speed = bal.FLEET_SPEED_DEFAULT
            self._speed_dirty = False
            return self._cached_speed
            
        slowest = bal.FLEET_SPEED_ESCORT
        for u in self.units:
            s_class = getattr(u, 'ship_class', 'Escort')
            if s_class == "Battleship":
                slowest = bal.FLEET_SPEED_BATTLESHIP
                break # Hard cap
            elif s_class == "Cruiser":
                slowest = min(slowest, bal.FLEET_SPEED_CRUISER)
        
        # Scouting override
        if self.is_scout and slowest > bal.FLEET_SPEED_CRUISER:
            slowest = bal.FLEET_SPEED_SCOUT_OVERRIDE
            
        # Apply Strategic Speed Modifier (Phase 11 Refinement)
        if hasattr(self, 'engine') and self.engine:
            faction_obj = self.engine.factions.get(self.faction)
            if faction_obj:
                # Modifiers > 1.0 (faster) or < 1.0 (slower)
                slowest = int(slowest * faction_obj.get_modifier("strategic_speed_mult", 1.0))
                
        self._cached_speed = slowest
        self._speed_dirty = False
        return slowest


    @property
    def is_in_orbit(self) -> bool:
        """Checks if the fleet is stationary at a planet node."""
        if self.destination:
            return False
        if self.current_node and self.current_node.type == "Planet":
            return True
        return False

    # Optimization 4.2: Vectorized Upkeep (R4)
    def update_upkeep_cache(self):
        """Recalculates cached upkeep using NumPy for speed."""
        # Extract upkeeps into a list (still O(N) but the summation is vectorized)
        unit_upkeeps = [getattr(u, 'upkeep', 0) for u in self.units]
        
        # Cargo (Armies)
        for ag in self.cargo_armies:
            unit_upkeeps.extend([getattr(u, 'upkeep', 0) for u in ag.units])
        
        if unit_upkeeps:
            self._cached_upkeep = int(np.sum(unit_upkeeps))
        else:
            self._cached_upkeep = 0

    @property
    def upkeep(self):
        """Returns total upkeep of the fleet (Cached)."""
        if not hasattr(self, '_cached_upkeep'):
             self.update_upkeep_cache()
        return self._cached_upkeep

    def merge_with(self, other_fleet: 'Fleet') -> bool:
        """
        Optimization 3.3: Set-Based Fleet Merging.
        Transfers all units from other_fleet to self efficiently.
        Returns True if successful.
        """
        if not other_fleet or other_fleet.is_destroyed:
            return False
            
        if other_fleet == self:
            return False

        # Optimization: Use sets for O(1) duplicate checks
        my_unit_ids = {id(u) for u in self.units}
        transferred_count = 0
        
        # Transfer Units
        # We copy the list slice to avoid modification issues during iteration, 
        # though we are clearing the other fleet anyway.
        for unit in list(other_fleet.units):
            # Duplicate Guard
            if id(unit) in my_unit_ids:
                # If it's the exact same object, easy.
                continue
                
            # Transfer ownership
            # Use set_fleet method as fleet is a read-only property on Unit
            if hasattr(unit, 'set_fleet'):
                unit.set_fleet(self)
            else:
                # Fallback for mocks or legacy objects
                unit.fleet = self
            
            # Update internal references if needed (handled by set_fleet usually)
            
            self.units.append(unit)
            my_unit_ids.add(id(unit))
            transferred_count += 1
            
        # Transfer Cargo/Armies
        if hasattr(other_fleet, 'cargo_armies'):
            for army in list(other_fleet.cargo_armies):
                if army not in self.cargo_armies:
                    # check capacity? 'Deathball' usually implies forcing merge regardless of capacity overflow risks?
                    # Or we should respect it.
                    # For now, we transfer ownership.
                    self.cargo_armies.append(army)
                    # Army parent/fleet ref update?
                    # ArmyGroup doesn't strictly link to Fleet object, usually just tracking location.
                    pass
        
        # Transfer Resources
        self.requisition += other_fleet.requisition
        other_fleet.requisition = 0
        
        # Invalidate Caches
        self.invalidate_caches() # Changed from invalidate_power_cache() to existing invalidate_caches()
        self.update_upkeep_cache() # New Optimization 4.2
        
        # Clear Data from Other
        other_fleet.units.clear()
        other_fleet.cargo_armies.clear()
        other_fleet.is_destroyed = True
        
        return transferred_count > 0

    @property
    def alive_units(self):
        """Generator yielding only active/alive units."""
        for u in self.units:
            if u.is_alive():
                yield u

    @property
    def alive_ships(self):
        """Generator yielding only active/alive ships."""
        for u in self.units:
            if isinstance(u, Ship) and u.is_alive():
                yield u
    


    def batch_calculate_power(self) -> int:
        """
        Optimization 2.3: Batch Power Calculation
        Updates unit strengths and sums fleet power in a single pass.
        """
        total = 0
        # Optimization 3.2: Use generator for filtered view
        for u in self.alive_units:
            # If unit has no cached strength (it was invalidated), recalculate it
            if not hasattr(u, '_cached_strength'):
                 u._cached_strength = u._calculate_strength()
            total += u._cached_strength
        return total

    @property
    def power(self):
        """Calculates total combat power of all ships in fleet. (Cached)"""
        if not self._power_dirty:
            return self._cached_power
            
        self._cached_power = self.batch_calculate_power()
        self._power_dirty = False
        return self._cached_power

    def get_capability_matrix(self) -> Dict[str, int]:
        """
        Categorizes units into refined roles for AI decision making.
        Returns: {"Escort": int, "Cruiser": int, "Battleship": int, "Transport": int, "Scout": int}
        """
        if not self._capability_matrix_dirty:
            return self._cached_capability_matrix
            
        matrix = {
            "Escort": 0,
            "Cruiser": 0,
            "Battleship": 0,
            "Transport": 0,
            "Scout": 0
        }
        
        for u in self.alive_units:
            # 1. Base Class Roles
            s_class = getattr(u, 'ship_class', 'Escort')
            if s_class in matrix:
                matrix[s_class] += 1
            
            # 2. Functional Roles (can overlap with base class)
            if getattr(u, 'transport_capacity', 0) > 0:
                matrix["Transport"] += 1
                
            tags = u.abilities.get("Tags", []) if hasattr(u, "abilities") else []
            traits = getattr(u, "traits", [])
            if "Scout" in tags or "Scout" in traits or getattr(u, "is_scout", False):
                matrix["Scout"] += 1

        self._cached_capability_matrix = matrix
        self._capability_matrix_dirty = False
        return matrix

    @property
    def transport_capacity(self):
        """Calculates total transport capacity of all ships in fleet. (Cached)"""
        if not self._transport_capacity_dirty:
            return self._cached_transport_capacity
            
        total = 0
        for u in self.units:
            if hasattr(u, "transport_capacity"):
                total += u.transport_capacity
        
        self._cached_transport_capacity = total
        self._transport_capacity_dirty = False
        return total

    @property
    def used_capacity(self):
        """Calculates currently used capacity by embarked armies. (Cached)"""
        if not self._used_capacity_dirty:
            return self._cached_used_capacity
            
        used = 0
        for ag in self.cargo_armies:
            for u in ag.units:
                size = bal.TRANSPORT_SIZE_DEFAULT
                tags = u.abilities.get("Tags", [])
                if "Vehicle" in tags: size = bal.TRANSPORT_SIZE_VEHICLE
                if "Monster" in tags: size = bal.TRANSPORT_SIZE_MONSTER
                if "Titanic" in tags: size = bal.TRANSPORT_SIZE_TITANIC
                used += size
                
        self._cached_used_capacity = used
        self._used_capacity_dirty = False
        return used

    def can_transport(self, army_group):
        """Checks if there is enough space to transport the given ArmyGroup."""
        needed = 0
        for u in army_group.units:
            size = bal.TRANSPORT_SIZE_DEFAULT
            tags = u.abilities.get("Tags", [])
            if "Vehicle" in tags: size = bal.TRANSPORT_SIZE_VEHICLE
            if "Monster" in tags: size = bal.TRANSPORT_SIZE_MONSTER
            if "Titanic" in tags: size = bal.TRANSPORT_SIZE_TITANIC
            needed += size
            
        remaining = self.transport_capacity - self.used_capacity
        return remaining >= needed


    def add_unit(self, unit_template):
        # Determine specific class
        is_ship = unit_template.is_ship()
        
        if is_ship:
             new_unit = Ship(
                name=unit_template.name,
                ma=unit_template.ma,
                md=unit_template.md,
                hp=unit_template.current_hp, # Use current or max? New unit should be fresh? Usually templates are fresh.
                armor=unit_template.armor,
                damage=unit_template.damage,
                abilities=unit_template.abilities.copy(),
                faction=self.faction,
                authentic_weapons=unit_template.authentic_weapons.copy(),
                rank=unit_template.rank,
                shield=getattr(unit_template, "shield_max", 0),
                traits=unit_template.traits.copy() if hasattr(unit_template, "traits") else [],
                cost=unit_template.cost,
                blueprint_id=getattr(unit_template, "blueprint_id", None),
                unit_class=getattr(unit_template, "unit_class", "Escort"),
                domain=getattr(unit_template, "domain", "space"),
                components_data=copy.deepcopy(getattr(unit_template, "components_data", [])),
                transport_capacity=getattr(unit_template, "transport_capacity", 0)
            )
        else:
             new_unit = Regiment(
                name=unit_template.name,
                ma=unit_template.ma,
                md=unit_template.md,
                hp=unit_template.current_hp,
                armor=unit_template.armor,
                damage=unit_template.damage,
                abilities=unit_template.abilities.copy(),
                faction=self.faction,
                authentic_weapons=unit_template.authentic_weapons.copy(),
                rank=unit_template.rank,
                traits=unit_template.traits.copy() if hasattr(unit_template, "traits") else [],
                cost=unit_template.cost,
                blueprint_id=getattr(unit_template, "blueprint_id", None),
                unit_class=getattr(unit_template, "unit_class", "Infantry"),
                domain=getattr(unit_template, "domain", "ground"),
                components_data=copy.deepcopy(getattr(unit_template, "components_data", []))
            )
            
        # Copy extra props
        new_unit.leadership = getattr(unit_template, "leadership", bal.UNIT_DEFAULT_LEADERSHIP)
        new_unit.resonator_mastery = getattr(unit_template, "resonator_mastery", 0)
        
        # Phase 1-4 Stat Copying
        new_unit.transport_capacity = getattr(unit_template, "transport_capacity", 0)
        new_unit.upkeep = getattr(unit_template, "upkeep", 0)
        new_unit.build_time = getattr(unit_template, "build_time", 1)
        new_unit.tier = getattr(unit_template, "tier", 1)
        new_unit.xp_gain_rate = getattr(unit_template, "xp_gain_rate", 100)
        
        # Combat Stats
        new_unit.bs = getattr(unit_template, "bs", 35)
        new_unit.charge_bonus = getattr(unit_template, "charge_bonus", 0)
        new_unit.weapon_range_default = getattr(unit_template, "weapon_range_default", 24)
        
        # Flavor Stats
        new_unit.fear_rating = getattr(unit_template, "fear_rating", 0)
        new_unit.morale_aura = getattr(unit_template, "morale_aura", 0)
        new_unit.regen_hp_per_turn = getattr(unit_template, "regen_hp_per_turn", 0)
        new_unit.stealth_rating = getattr(unit_template, "stealth_rating", 0)
        new_unit.suppression_resistance = getattr(unit_template, "suppression_resistance", 0)
        new_unit.suppression_power = getattr(unit_template, "suppression_power", 0)
        new_unit.detection_range = getattr(unit_template, "detection_range", bal.DETECTION_RANGE_BASE)

        self.units.append(new_unit)
        if hasattr(new_unit, 'set_fleet'): new_unit.set_fleet(self)
        self.invalidate_caches()
        self.update_upkeep_cache() # Optimization 4.2

    @classmethod
    def merge_multiple_fleets(cls, target_fleet, other_fleets):
        """Merges a list of fleets into the target_fleet. (Refactored R4)"""
        for f in other_fleets:
            if f.id == target_fleet.id: continue
            if f.faction != target_fleet.faction: continue
            
            target_fleet.merge_with(f)
            
        return True

    def split_off(self, unit_count=None, ratio=0.5):
        """
        Splits off units into a new fleet at the same location.
        If unit_count is None, uses ratio.
        """
        if not self.units:
            return None
            
        total_units = len(self.units)
        if unit_count is not None:
            move_count = min(unit_count, total_units)
        else:
            move_count = int(total_units * ratio)
            
        if move_count <= 0:
            return None
            
        # 1. Select units to move (stochastic or end-weighted)
        new_units = self.units[-move_count:]
        self.units = self.units[:-move_count]
        
        # 2. Proportional Requisition scaling
        req_to_move = int(self.requisition * (move_count / total_units))
        self.requisition -= req_to_move
        
        # 3. Create New Fleet instance
        import random
        suffix = random.randint(1000, 9999)
        new_id = f"{self.id}_Split_{suffix}"
        
        new_fleet = self.__class__(new_id, self.faction, self.location)
        new_fleet.units = new_units
        for u in new_units:
             if hasattr(u, 'set_fleet'): u.set_fleet(new_fleet)
        new_fleet.requisition = req_to_move
        
        # 4. Finalize
        if not self.units:
            self.is_destroyed = True
            
        self.invalidate_caches()
        new_fleet.invalidate_caches()
        
        return new_fleet

    def invalidate_caches(self):
        """Marks all cached properties as dirty."""
        self._speed_dirty = True
        self._power_dirty = True
        self._transport_capacity_dirty = True
        self._used_capacity_dirty = True
        self._capability_matrix_dirty = True

    def invalidate_used_capacity(self):
        """Marks the used capacity cache as dirty."""
        self._used_capacity_dirty = True

    def register_with_cache_manager(self, cache_manager):
        """Registers fleet cache invalidation with the provided CacheManager."""
        cache_manager.register_cache(self.invalidate_caches, f"fleet_{self.id}")
    def _log_fleet_movement_event(self, status: str, engine=None, **kwargs):
        """
        Logs fleet movement telemetry events.
        
        Args:
            status: Movement status (started, completed, intercepted, blocked, portal_transit)
            engine: CampaignEngine instance for telemetry access
            **kwargs: Additional event-specific data
        """
        if not engine or not hasattr(engine, 'telemetry'):
            return
        
        turn = getattr(engine, 'turn_counter', 0)
        
        if status == 'started':
            self._movement_expected_duration = kwargs.get('estimated_turns', 0)
        
        actual_turns = turn - self._movement_start_turn if self._movement_start_turn else 0
        
        # Phase 9: Movement Delay Tracking
        if status in ['completed', 'intercepted', 'blocked'] and self._movement_expected_duration > 0:
            delay = actual_turns - self._movement_expected_duration
            if delay > 2:
                engine.telemetry.log_event(
                    EventCategory.MOVEMENT,
                    "movement_delay",
                    {
                        "fleet_id": self.id,
                        "faction": self.faction,
                        "turn": turn,
                        "expected_turns": self._movement_expected_duration,
                        "actual_turns": actual_turns,
                        "delay": delay,
                        "reason": status,
                        "from": getattr(self._movement_start_location, 'name', 'unknown'),
                        "to": getattr(self.destination, 'name', 'unknown')
                    },
                    turn=turn,
                    faction=self.faction
                )

        # Build route node list
        route_nodes = []
        if self.route:
            route_nodes = [node.id for node in self.route]
        elif self.destination:
            n_ref = getattr(self.destination, 'node_reference', None)
            if isinstance(n_ref, dict):
                route_nodes = [n_ref.get('id', 'unknown')]
            else:
                route_nodes = [getattr(n_ref, 'id', 'unknown') if n_ref else 'unknown']
        
        # Get fleet composition
        composition = {
            'total_units': len([u for u in self.units if u.is_alive()]),
            'ships': len([u for u in self.units if isinstance(u, Ship) and u.is_alive()]),
            'regiments': len([u for u in self.units if isinstance(u, Regiment) and u.is_alive()]),
            'transport_capacity': self.transport_capacity,
            'used_capacity': self.used_capacity
        }
        
        event_data = {
            'fleet_id': self.id,
            'faction': self.faction,
            'turn': turn,
            'status': status,
            'source_location': getattr(self._movement_start_location, 'name', 'unknown') if self._movement_start_location else getattr(self.location, 'name', 'unknown'),
            'current_location': getattr(self.location, 'name', 'unknown'),
            'destination': getattr(self.destination, 'name', 'unknown') if self.destination else None,
            'path_length': self._movement_path_length,
            'estimated_turns': kwargs.get('estimated_turns', 0),
            'actual_turns': turn - self._movement_start_turn if self._movement_start_turn else 0,
            'route_nodes': route_nodes,
            'fleet_composition': composition,
            'speed': self.speed,
            'is_scout': self.is_scout,
            'cargo_armies': len(self.cargo_armies)
        }
        
        # Add status-specific data
        if status == 'intercepted':
            event_data['intercepting_faction'] = kwargs.get('intercepting_faction', 'unknown')
        elif status == 'blocked':
            event_data['block_reason'] = kwargs.get('block_reason', 'unknown')
        elif status == 'portal_transit':
            event_data['dest_universe'] = kwargs.get('dest_universe', 'unknown')
        
        engine.telemetry.log_event(EventCategory.MOVEMENT, 'fleet_movement', event_data)
    
    def _log_path_efficiency(self, engine=None, pathfinding_time=0.0, cache_hit=False):
        """
        Logs path efficiency metrics.
        
        Args:
            engine: CampaignEngine instance for telemetry access
            pathfinding_time: Time taken for pathfinding in seconds
            cache_hit: Whether path was retrieved from cache
        """
        if not engine or not hasattr(engine, 'telemetry'):
            return
        
        turn = getattr(engine, 'turn_counter', 0)
        
        # Calculate efficiency metrics
        path_length = len(self._movement_nodes_visited) if self._movement_nodes_visited else 0
        optimal_length = self._movement_path_length if self._movement_path_length > 0 else 1
        efficiency_ratio = path_length / optimal_length if optimal_length > 0 else 1.0
        
        # Get cache statistics
        cache_stats = {}
        if engine.pathfinder and hasattr(engine.pathfinder, 'cache_stats'):
            cache_stats = engine.pathfinder.cache_stats
        
        event_data = {
            'fleet_id': self.id,
            'faction': self.faction,
            'turn': turn,
            'pathfinding_time': pathfinding_time,
            'path_length': path_length,
            'optimal_path_length': optimal_length,
            'efficiency_ratio': min(efficiency_ratio, 1.0),  # Cap at 1.0
            'cache_hit': cache_hit,
            'cache_stats': cache_stats,
            'source_location': getattr(self._movement_start_location, 'name', 'unknown') if self._movement_start_location else getattr(self.location, 'name', 'unknown'),
            'destination': getattr(self.destination, 'name', 'unknown') if self.destination else None,
            'fleet_speed': self.speed,
            'is_scout': self.is_scout
        }
        
        engine.telemetry.log_event(EventCategory.MOVEMENT, 'path_efficiency', event_data)

    @profile_method
    def move_to(self, target_planet, force=False, turn=0, engine=None):
        if self.is_engaged and not force:
            print(f"Fleet {self.id} is ENGAGED in combat and cannot move! Issue RETREAT order to break contact.")
            return

        if self.route and not force:
            print(f"Fleet {self.id} is already moving! Overwriting orders.")
            
        if self.location == target_planet:
            if engine and engine.logger: engine.logger.debug(f"Fleet {self.id} is already at {target_planet.name}")
            return

        # Phase 5: Theater Locking
        if self.assigned_theater_id and not force:
            # Check if target is in assigned theater
            # We need TheaterManager access or checking metadata on nodes?
            # Or easier: We check if the order is "REDEPLOY" or similar.
            # But here "force" is the override.
            # If we don't have theater context, we can't strict check easily without engine lookups.
            # Assuming 'force' is used by StrategicPlanner when changing theaters.
            pass # Implemented in StrategicPlanner (it shouldn't issue orders outside theater).
            # But strictly enforcing it here prevents accidental wandering.
            if engine and hasattr(engine, 'ai_manager') and hasattr(engine.ai_manager, 'theater_manager'):
                 tm = engine.ai_manager.theater_manager
                 theater = tm.theaters.get(self.assigned_theater_id)
                 if theater:
                      # Check if target system is in theater
                      sys_name = target_planet.system.name if hasattr(target_planet, 'system') else None
                      if sys_name and sys_name not in theater.system_names:
                           print(f"  > [DENIED] Fleet {self.id} (Theater: {theater.name}) denied move to {sys_name} (Outside AO).")
                           return

        # Phase 14: FTL Inhibition (Starbases)
        # Check if we are currently in a system with a hostile inhibitor
        current_system = getattr(self.location, 'system', None)
        if current_system and engine:
            for sb in current_system.starbases:
                # Check if hostile and inhibitor active
                if sb.faction != self.faction and getattr(sb, 'ftl_inhibitor', False) and sb.is_alive():
                    # Check if we are trying to leave the system
                    target_system = getattr(target_planet, 'system', None)
                    if target_system != current_system and not force:
                        # BLOCKED
                        print(f"  > [ALERT] Fleet {self.id} movement BLOCKED by FTL Inhibitor on {sb.name} in {current_system.name}!")
                        if engine.logger:
                            engine.logger.campaign(f"[FTL DENIED] Fleet {self.id} attempted to leave {current_system.name} but was trapped by {sb.name}.")
                        return

        # --- PHASE 15: GRAPH NAVIGATION ---
        if not self.current_node:
             # Try to recover node from location
             if hasattr(self.location, "node_reference"):
                 self.current_node = self.location.node_reference
             elif hasattr(self.location, "edges"): # Duck type for GraphNode
                 self.current_node = self.location
             else:
                 if engine and engine.logger: engine.logger.error(f"Error: Fleet {self.id} has no Graph Node! Loc: {self.location}")
                 return

        target_node = getattr(target_planet, "node_reference", None)
        if not target_node and hasattr(target_planet, "edges"): # Duck type
             target_node = target_planet

        # [FIX] Auto-recovery of current_node if it became None
        if self.current_node is None and self.location is not None:
            if hasattr(self.location, "node_reference"):
                self.current_node = self.location.node_reference
            elif isinstance(self.location, GraphNode):
                self.current_node = self.location
            elif hasattr(self.location, "type") and self.location.type in ["FluxPoint", "DeepSpace", "Planet"]:
                self.current_node = self.location

        if not target_node:
             if engine and engine.logger: 
                  target_name = target_planet.name if hasattr(target_planet, 'name') else str(target_planet)
                  engine.logger.error(f"Error: Target {target_name} has no Graph Node reference!")
             return
        
        if not self.current_node:
             if engine and engine.logger:
                  engine.logger.error(f"Error: Fleet {self.id} has no current_node and cannot recover it from location {self.location}")
             return
             
        # Pathfinding
        pathfinding_start = time.time()
        cache_hit = False
        
        if engine:
             cached_path, cost, path_meta = engine.find_cached_path(self.current_node, target_node, turn)
             cache_hit = path_meta.get('cache_hit', False)
             
             # Phase 23: Check for cross-universe warning
             if path_meta.get("requires_handoff"):
                 if engine and engine.logger: engine.logger.info(f"  > [NAV] Fleet {self.id} route includes cross-universe portal to {path_meta.get('dest_universe', 'Unknown')}")
                 self.portal_aware = True
        else:
             print(f"Warning: Fleet {self.id} moving without Engine context. Pathfinding disabled.")
             return
             
        pathfinding_time = time.time() - pathfinding_start
        
        # COPY path to avoid mutating cache
        path = list(cached_path) if cached_path else None
        
        if not path:
             # Reduce Logging Spam: Only print if this specific failure hasn't been logged this turn
             if engine and engine.pathfinder.log_path_failure(self.current_node, target_node):
                  if engine and engine.logger: 
                       # [FIX] Robust logging with getattr to avoid AttributeError if nodes are None
                       start_id = getattr(self.current_node, 'id', 'None')
                       end_id = getattr(target_node, 'id', 'None')
                       target_name = getattr(target_planet, 'name', 'Unknown Target')
                       engine.logger.error(f"Fleet {self.id} cannot find path to {target_name} (Disconnected Graph from {start_id} to {end_id})")
             return
             
        # Path includes start node, so remove it for "next steps"
        if path and (path[0] == self.current_node or path[0].id == self.current_node.id):
            path.pop(0)
            
        self.route = path
        self.destination = target_planet # RESTORED Fix 53: Prevents AI overwriting active orders
        
        # Initialize movement tracking
        self._movement_start_turn = getattr(engine, 'turn_counter', 0)
        self._movement_start_location = self.location
        self._movement_path_length = len(path) if path else 0
        self._movement_nodes_visited = [self.current_node.id]
        
        # Log path efficiency
        self._log_path_efficiency(engine, pathfinding_time, cache_hit)
        
        # Phase 39: Speed & Scanning
        self.scanning_range = bal.SCAN_RANGE_BASE
        if any(u.is_capital for u in self.units if hasattr(u, 'is_capital')):
             self.scanning_range = bal.SCAN_RANGE_CAPITAL

        turns = int(cost / self.speed) + 1
        
        # DEBUG: Print Full Route
        route_names = [n.name for n in self.route]
        print(f"Fleet {self.id} plotting course to {target_planet.name}. Path: {route_names} (Est: {turns} turns).")
        
        # Log fleet movement started
        self._log_fleet_movement_event('started', engine, estimated_turns=turns)

    def retreat(self, target_planet):
        """
        Special order to break engagement and move.
        [LIMIT] Can only retreat once per turn.
        """
        if self.has_retreated_this_turn:
            print(f"Fleet {self.id} has already retreated this turn and MUST STAND AND FIGHT!")
            return False

        if self.is_engaged:
            print(f"Fleet {self.id} is RETREATING from battle!")
            self.is_engaged = False # Break Lock
            self.has_retreated_this_turn = True
            self.move_to(target_planet, force=True) # Force move (override existing orders)
            return True
        return False

    @profile_method
    def update_movement(self, engine=None):
        if self.is_engaged:
            return False

        if not self.route:
            # SCOUT PATROL LOGIC
            if self.is_scout and self.exploration_target_system:
                 is_in_system = False
                 # Check location system
                 if hasattr(self.location, 'system') and self.location.system == self.exploration_target_system:
                     is_in_system = True
                 elif hasattr(self.current_node, 'metadata') and 'system' in self.current_node.metadata:
                     if self.current_node.metadata['system'] == self.exploration_target_system:
                         is_in_system = True
                         
                 if is_in_system:
                     self.patrol_turns += 1
                     self.scanning_range = bal.SCAN_RANGE_SCOUT_PATROL 
                     
                     if self.patrol_turns < 3:
                         if hasattr(self.current_node, 'edges'):
                             valid_neighbors = []
                             for e in self.current_node.edges:
                                 if e.distance < 5:
                                     valid_neighbors.append(e.target)
                             
                             if valid_neighbors:
                                 next_hop = random.choice(valid_neighbors)
                                 self.route = [next_hop]
                                 p_obj = next_hop.metadata.get("object")
                                 if p_obj: 
                                     self.destination = p_obj
                                 return False 
                     else:
                         self.exploration_target_system = None 
                         self.patrol_turns = 0
                         return True
                         
            return False # Not moving
            
        # Phase 39: Fleet Speed (Multi-step)
        # Speed is now dynamic property based on fleet composition.
        
        remaining_movement = self.speed
        
        while remaining_movement > 0 and self.route:
            # Get Next Step
            next_node = self.route[0]
            
            # Determine Edge Cost (if not already traversing)
            if self.current_edge_cost == 0:
                 # Find edge connecting current to next
                 edge = None
                 edge_found = False
                 for e in self.current_node.edges:
                     if e.target == next_node:
                         edge = e
                         edge_found = True
                         break
                 
                 # Phase 51: Path Repair (Robustness)
                 # If no direct edge exists, check if we skipped a local node (e.g. Planet -> RemoteGate skipping LocalGate)
                 if not edge_found:
                    # Look for an intermediate neighbor
                     for e_intermediate in self.current_node.edges:
                         intermediate = e_intermediate.target
                         # Check if intermediate connects to next_node
                         valid_link = any(e2.target == next_node for e2 in intermediate.edges)
                         if valid_link:
                             if engine and engine.logger: engine.logger.debug(f"  > [NAV] FIXED PATH for {self.id}: Inserted {intermediate.name} between {self.current_node.name} and {next_node.name}")
                             self.route.insert(0, intermediate)
                             next_node = intermediate # Update next_node to the intermediate one
                             
                             # Assign the intermediate edge to `edge` for subsequent checks
                             edge = e_intermediate
                             edge_found = True
                             break # Found an intermediate, break from this inner loop
                             
                 if not edge_found:
                     if engine and engine.logger: engine.logger.error(f"Critical Path Error: No edge from {self.current_node.id} to {next_node.id}")
                     # Force stop to prevent crash loop, but don't crash sim
                     self.destination = None 
                     self.route = []
                     return False
                      
                 if not edge.is_traversable():
                      if engine and engine.logger: engine.logger.warning(f"Fleet {self.id} blocked by Flux Storm/Hazard!")
                      self.route = [] # Stop moving
                      self._log_fleet_movement_event('blocked', engine, block_reason='flux_storm_or_hazard')
                      return False
                     
                 self.current_edge_cost = edge.distance
            
            # Process Travel Step
            # movement cost is 1 per 'distance unit'. 
            # If edge.distance is 1 (standard), consumes 1 movement.
            # If default edge is 1, and speed is 4, we move 4 nodes.
            
            # Spend movement to progress
            spend = min(remaining_movement, self.current_edge_cost - self.travel_progress)
            self.travel_progress += spend
            remaining_movement -= spend
            
            if self.travel_progress >= self.current_edge_cost:
                # Arrived at Next Node
                self.current_node = next_node
                self.arrived_this_turn = True # Phase 16.5: Mark as Attacker if battle occurs
                
                # [Optimization] Invalidate spatial indices upon arrival
                if engine and hasattr(engine, 'battle_manager'):
                     engine.battle_manager.mark_indices_dirty()
                self.route.pop(0) # Remove visited
                
                # Update High-Level Location
                planet_obj = self.current_node.metadata.get("object")
                if planet_obj:
                    self.location = planet_obj
                elif self.current_node.type == "Planet": # Fallback
                    self.location = self.current_node
                
                # Phase 110: Interception Check (Choke Points)
                if engine and self.location and not self.is_engaged:
                    # Arrived at Portal? (Phase 22)
                    if self.current_node.is_portal():
                        dest_universe = self.current_node.metadata.get("portal_dest_universe")
                        if engine and dest_universe != engine.universe_name:
                            print(f"  > [PORTAL] Fleet {self.id} reached Portal to {dest_universe}!")
                            
                            # Log portal transit
                            self._log_fleet_movement_event('portal_transit', engine, dest_universe=dest_universe)
                            
                            # Phase 23: Hand-off Logic
                            transit_result = self.traverse_portal(engine)
                            if transit_result:
                                # Signal Engine (or caller) that hand-off occurred
                                # We return a special status dict
                                return {"status": "PORTAL_TRANSIT", "package": transit_result}
                            
                            self.route = []
                            self.destination = None
                            return "PORTAL_REACHED"

                    # Look for hostile fleets at this node
                    # [FIX] War-Only Interception: Only stop if the other faction is at WAR.
                    dm = getattr(engine, 'diplomacy', None)
                    
                    hostile_present = any(f.faction != self.faction and f.location == self.location and not f.is_destroyed and any(u.is_alive() for u in f.units) for f in engine.fleets)
                    intercepting_faction = None

                    if hostile_present:
                         # Phase 33: Interception Logic
                         if engine:
                            # [FIX] Reset hostile_present to confirm via detailed check (diplomacy)
                            hostile_present = False 
                            
                            for f in engine.fleets:
                                if f.faction == self.faction: continue
                                if f.location != self.location:
                                     continue
                                if f.is_destroyed: continue
                                if not any(u.is_alive() for u in f.units):
                                     continue
                            
                                # Use Diplomacy Manager if available
                                intercept = True # Default to legacy behavior (hostile)
                                if dm:
                                    treaty = dm.get_treaty(self.faction, f.faction)
                                    if treaty != "War":
                                        intercept = False
                                
                                if intercept:
                                    hostile_present = True
                                    intercepting_faction = f.faction
                                    break

                    if hostile_present:
                        print(f"  > [INTERCEPTED] Fleet {self.id} stopped at {getattr(self.location, 'name', 'node')} by hostile forces ({intercepting_faction})!")
                        self.route = []
                        self.destination = None
                        # Reset Step
                        self.travel_progress = 0
                        self.current_edge_cost = 0
                        self._log_fleet_movement_event('intercepted', engine, intercepting_faction=intercepting_faction)
                        return "INTERCEPTED"

                # Reset Step
                self.travel_progress = 0
                self.current_edge_cost = 0
                
                # Check Final Arrival
                if not self.route:
                     self.destination = None
                     self._log_fleet_movement_event('completed', engine)
                     return True # Arrived at Final Dest
                     
        return False # Still moving (or finished this turn but not final dest)

    def prepare_for_portal_transit(self) -> Dict[str, Any]:
        """
        Serializes fleet state for an inter-universe hand-off (Phase 22/23).
        Returns a 'Universal Fleet Package'.
        """
        package = {
            "fleet_id": self.id,
            "faction": self.faction,
            "units": [u.to_dict() for u in self.units if u.is_alive()],
            "cargo": [ag.to_dict() for ag in self.cargo_armies],
            "requisition": self.requisition,
            "source_universe": getattr(self.current_node, 'metadata', {}).get("source_universe", "unknown"),
            "portal_exit_coords": self.current_node.metadata.get("portal_dest_coords"),
            "original_destination": getattr(self.destination, 'name', None) if self.destination else None,
            
            # Phase 23 Extended Metadata
            "timestamp": 0, # Should be filled by caller with turn number if possible
            "source_node_id": getattr(self.current_node, 'id', 'unknown'),
            "fleet_composition": { "ships": len(self.units), "cargo_groups": len(self.cargo_armies) },
            "is_engaged": self.is_engaged,
            "route_history": [] # Could add if we tracked history
        }
        return package

    def traverse_portal(self, engine=None) -> Dict[str, Any]:
        """
        Handles portal traversal logic when fleet reaches a PortalNode.
        
        Returns:
            Dict containing hand-off package and metadata, or None if traversal fails.
        """
        if not self.current_node or not self.current_node.is_portal():
            return None
            
        print(f"[PORTAL_TRANSIT] Fleet {self.id} preparing for transit: {len(self.units)} units, {len(self.cargo_armies)} armies")

        # Validate State
        if self.is_engaged:
            print(f"[PORTAL_TRANSIT] Failed: Fleet {self.id} is engaged in combat.")
            return None
            
        # Serialize
        package = self.prepare_for_portal_transit()
        if engine and hasattr(engine, 'turn'):
            package["timestamp"] = engine.turn
            
        # Comment 1: Ensure source_universe is set correctly using engine context
        if engine and hasattr(engine, 'universe_name'):
            package["source_universe"] = engine.universe_name
            
        dest_universe = self.current_node.metadata.get("portal_dest_universe")
        
        # Emit Signal via Engine Queue (Phase 23 Refactoring)
        if engine:
            # Use injected progress_queue if available
            prog_q = getattr(engine, '_progress_q_ref', None)
            if not prog_q:
                # Fallback to older attribute names if refactoring is partial
                prog_q = getattr(engine, 'progress_queue', None)
                
            turn = getattr(engine, 'turn_counter', 0)
            
            if prog_q:
                # MUR expects: (run_id, turn, status, data)
                # run_id 0 is placeholder (Runner will fill or MUR will handle)
                prog_q.put((0, turn, "PORTAL_HANDOFF", package))
                print(f"[PORTAL_TRANSIT] Fleet {self.id} hand-off signal sent via progress queue.")
            else:
                # Final fallback: Globals (legacy)
                if 'progress_queue' in globals():
                    globals()['progress_queue'].put((0, turn, "PORTAL_HANDOFF", package))
                else:
                    print(f"Warning: Fleet {self.id} traversed portal but no progress_queue found to signal hand-off!")
        
        # Mark as In-Transit
        self.in_portal_transit = True
        self.portal_destination_universe = dest_universe
        self.portal_entry_turn = engine.turn_counter if engine and hasattr(engine, 'turn_counter') else 0
        
        # [PHASE 6] Portal Transit Trace
        if logging_config.LOGGING_FEATURES.get('portal_wormhole_usage_tracking', False):
            if engine and hasattr(engine.logger, 'movement'):
                # Calculate distance saved? 
                # (Just log the transit event for now as per plan)
                trace_msg = {
                    "event_type": "portal_transit_event",
                    "fleet_id": self.id,
                    "faction": self.faction,
                    "origin": self.current_node.name if self.current_node else "Unknown",
                    "destination_universe": dest_universe,
                    "turn": self.portal_entry_turn
                }
                engine.logger.movement(f"[PORTAL] Fleet {self.id} traversed to {dest_universe}", extra=trace_msg)

        # Clear Local State
        self.route = []
        self.destination = None
        # Comment 2: Do NOT set is_destroyed = True. Rely on in_portal_transit.
        # self.is_destroyed = True 
        
        print(f"[PORTAL_TRANSIT] Fleet {self.id} marked as in-transit (removed from active roster)")
        return package

class TaskForce:
    def __init__(self, tf_id, faction):
        """
        Initializes a TaskForce to group fleets for coordinated operations.
        
        Args:
            tf_id (str): Task Force ID.
            faction (str): Faction owner.
        """
        self.id = tf_id
        self.faction = faction
        self.fleets = [] # List of Fleet Objects
        self.state = "MUSTERING" # MUSTERING, RALLYING, COLLECTING, TRANSIT, ATTACKING, IDLE
        self.rally_point = None # Planet Object
        self.target = None # Planet Object
        self.status_msg = ""
        self.mission_role = "BALANCED" # BALANCED, INVASION, CONSTRUCTION, SCOUT
        
        # Phase 80: Composition & Strategy
        self.composition_type = "BALANCED" # BALANCED, ASSAULT, RAIDER, SCOUT
        self.strategy = "DIRECT" # DIRECT, PINCER, RESERVE, EXPLORATION
        
        # Combat Doctrines
        self.combat_doctrine = None # CHARGE, KITE, DEFEND (Set by determine_combat_doctrine)
        # Phase 110: Faction Combat Doctrines
        self.faction_combat_doctrine = "STANDARD"
        self.doctrine_intensity = 1.0
        
        # Phase 90: Economic Enhancements
        self.is_raid = False
        self.raid_duration = 0
        self.raid_timer = 0
        self.estimated_upkeep = 0
        
        # Phase 105: Strategic Withdrawals
        self.withdrawal_plan = None
        self.rally_point_reached = False
        
        # Performance Caching
        self._composition_dirty = True
        
        # Phase 10: Performance Tracking
        self.battles_won = 0
        self.battles_lost = 0
        self.turns_active = 0
        self.enemies_destroyed = 0
        self.creation_turn = 0

    def calculate_upkeep(self):
        """Calculates total upkeep for all fleets in task force."""
        total = 0
        for f in self.fleets:
            for u in f.units:
                total += getattr(u, 'upkeep', 0)
        self.estimated_upkeep = total
        return total

    def get_composition(self):
        """Analyzes attached fleets to determine composition type."""
        if not self._composition_dirty:
            return self.composition_type
            
        total_ships = 0
        capital_ships = 0
        
        for f in self.fleets:
            for u in f.units:
                if hasattr(u, 'is_alive') and not u.is_alive(): continue
                total_ships += 1
                # Check for capital status (Tier >= 3 or explicit flag)
                is_cap = getattr(u, 'is_capital', False)
                if not is_cap and hasattr(u, 'tier') and u.tier >= 3:
                    is_cap = True
                if is_cap:
                    capital_ships += 1
                    
        if total_ships == 0: 
            self.composition_type = "BALANCED"
        else:
            cap_ratio = capital_ships / total_ships
            if cap_ratio >= 0.3: 
                self.composition_type = "ASSAULT" 
            elif cap_ratio == 0 and total_ships <= 10: 
                self.composition_type = "RAIDER" 
            else:
                self.composition_type = "BALANCED"
                
        self._composition_dirty = False
        return self.composition_type

    def determine_combat_doctrine(self):
        """Maps broad strategy to tactical combat doctrine."""
        # [QUIRK] Strategic Mapping (Decoupled from lore-specific names)
        doctrine_map = {
            "WAAAGH": DOCTRINE_CHARGE,
            "SWARM": DOCTRINE_CHARGE,
            "REPAIR": DOCTRINE_DEFEND,
            "HIT_AND_RUN": DOCTRINE_KITE,
            "FAITH": DOCTRINE_CHARGE,
            "BALANCED": DOCTRINE_CHARGE # Default fallback
        }
        
        if self.faction_combat_doctrine in doctrine_map:
            self.combat_doctrine = doctrine_map[self.faction_combat_doctrine]
        else:
            # Fallback to strategy-based logic
            if self.strategy in ["DIRECT", "PINCER"]:
                self.combat_doctrine = DOCTRINE_CHARGE
            elif self.strategy in ["EXPLORATION", "RAID"]:
                self.combat_doctrine = DOCTRINE_KITE
            elif self.strategy in ["RESERVE", "DEFEND"]:
                self.combat_doctrine = DOCTRINE_DEFEND
            else:
                self.combat_doctrine = DOCTRINE_CHARGE # Default
            
        return self.combat_doctrine
        
    def add_fleet(self, fleet):
        if fleet not in self.fleets:
            self.fleets.append(fleet)
            self._composition_dirty = True
            
    def update(self, engine=None):
        # Update Doctrine if state is ATTACKING
        if self.state == "ATTACKING" and not self.combat_doctrine:
             self.determine_combat_doctrine()

        # 1. MUSTERING / RALLYING PHASE
        if self.state in ["MUSTERING", "RALLYING"]:
            if not self.rally_point: 
                self.state = "TRANSIT"
                return
            
            all_at_rally = True
            for f in self.fleets:
                if f.location != self.rally_point:
                    all_at_rally = False
                    # Order move if idle
                    if f.destination is None:
                        f.move_to(self.rally_point, engine=engine)
            
            if all_at_rally:
                # Phase 9: Active Merging Logic
                if self.state == "RALLYING" and len(self.fleets) > 1:
                     # Sort fleets by size (Largest is flagship)
                     self.fleets.sort(key=lambda x: len(x.units), reverse=True)
                     flagship = self.fleets[0]
                     others = self.fleets[1:]
                     
                     print(f"  > [RALLY] Task Force {self.id} MERGING {len(others)} fleets into Flagship {flagship.id} at {self.rally_point.name}")
                     
                     if Fleet.merge_multiple_fleets(flagship, others):
                         self.fleets = [flagship] # Update TF roster
                         
                print(f"  > [RALLY] Task Force {self.id} ({self.faction}) RALLIED at {self.rally_point.name}. Preparing for ASSAULT.")
                
                # Phase 22: Transition to Loading/Collecting if this is an invasion force
                if self.mission_role == "INVASION":
                     self.state = "COLLECTING"
                else:
                     self.state = "TRANSIT"
                
        # 1.5 COLLECTING PHASE (Pick up troops)
        elif self.state == "COLLECTING":
            if not engine: return
            
            # 1. Check if we are already loaded
            total_cap = sum(f.transport_capacity for f in self.fleets)
            total_cargo = sum(f.used_capacity for f in self.fleets)
            
            # Heuristic: We want at least 80% capacity utilized if we have troops elsewhere
            is_loaded = total_cargo >= (total_cap * 0.8) or total_cargo >= 10 # 10 is a decent baseline for an invasion
            
            if is_loaded:
                self.state = "TRANSIT"
                if engine.logger:
                    engine.logger.campaign(f"  > [STRATEGY] Task Force {self.id} reached sufficient troop load ({total_cargo}/{total_cap}). Moving to TRANSIT.")
                return

            # 2. Find nearest friendly planet with ground troops
            owned_planets = engine.planets_by_faction.get(self.faction, [])
            best_pickup = None
            min_dist = 9999
            
            for p in owned_planets:
                # Check for idle armies
                has_idle_armies = any(a.state == "IDLE" and not a.is_destroyed for a in p.armies if a.faction == self.faction)
                if not has_idle_armies: continue
                
                # Check distance from current location (using flagship location)
                current_loc = self.fleets[0].location
                dist = ((p.system.x - current_loc.system.x)**2 + (p.system.y - current_loc.system.y)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    best_pickup = p
            
            if not best_pickup:
                # No more troops available anywhere? Just go with what we have.
                self.state = "TRANSIT"
                if engine.logger:
                    engine.logger.campaign(f"  > [STRATEGY] Task Force {self.id} found no more available troops for pickup. Proceeding to target.")
                return
            
            # 3. Move to pickup point
            all_at_pickup = True
            for f in self.fleets:
                if f.location != best_pickup:
                    all_at_pickup = False
                    if f.destination is None:
                        f.move_to(best_pickup, engine=engine)
            
            if all_at_pickup:
                # Attempt to embark all reachable idle armies
                for f in self.fleets:
                    for a in list(best_pickup.armies):
                        if a.faction == self.faction and a.state == "IDLE" and not a.is_destroyed:
                            # Use engine's battle manager to embark
                            if hasattr(engine.battle_manager.invasion_manager, 'embark_army'):
                                if engine.battle_manager.invasion_manager.embark_army(f, a):
                                    if f.used_capacity >= f.transport_capacity:
                                        break # This fleet is full
                
                # Re-evaluate next turn (maybe go to another planet or proceed)
                if engine.logger:
                    engine.logger.campaign(f"  > [LOGISTICS] Task Force {self.id} processed pickup at {best_pickup.name}. Current load: {sum(f.used_capacity for f in self.fleets)}")

        # 2. TRANSIT PHASE (Move to Target)
        elif self.state == "TRANSIT":
            if not self.target: return
            
            all_at_target = True
            for f in self.fleets:
                if f.location != self.target:
                    all_at_target = False
                    if f.destination is None:
                        f.move_to(self.target, engine=engine)
            
            if all_at_target:
                self.state = "ATTACKING"
                
        # 3. WITHDRAWING PHASE (Move to Rally Point)
        elif self.state == "WITHDRAWING":
            if not self.target: return # Target is the rally point from initiate_staged_withdrawal
            
            all_at_rally = True
            for f in self.fleets:
                if f.location != self.target:
                    all_at_rally = False
                    if f.destination is None:
                        f.move_to(self.target, engine=engine)
            
            if all_at_rally:
                print(f"  > [TACTICAL] Task Force {self.id} reached RALLY POINT. Disbanding.")
                self.rally_point_reached = True
                self.state = "IDLE"
                # Reset fleets
                for f in self.fleets:
                    f.is_scout = False
                    f.destination = None

                 
        # 3. ATTACKING (Combat Simulator handles battles)
        elif self.state == "ATTACKING":
            # Phase 93: Raid Completion Logic
            if self.is_raid:
                self.raid_timer += 1
                if self.raid_timer >= self.raid_duration:
                    if not self.target:
                        self.state = "IDLE"
                        return

                    print(f"  > [RAID] Task Force {self.id} COMPLETED RAID on {self.target.name}. Retreating with plunder.")
                    # Plunder logic is handled by AI Manager (awarding Requisition)
                    # Here we just disband/retreat
                    self.state = "IDLE" 
                    self.target = None
                    return "RAID_COMPLETE"
            
            # If battle resolved, return to IDLE or Hold
            pass
