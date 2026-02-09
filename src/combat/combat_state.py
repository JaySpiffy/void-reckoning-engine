import hashlib
import math
from typing import Dict, List, Any, Optional
from src.combat.tactical_grid import TacticalGrid
from src.combat.combat_tracker import CombatTracker
from src.utils.rng_manager import RNGManager

class CombatState:
    """
    Encapsulates battle state operations, management, and initialization.
    """
    def __init__(self, armies_dict: Dict[str, List[Any]], faction_doctrines: Dict[str, str], faction_metadata: Dict[str, Any], universe_rules: Optional[Any] = None, defender_factions: Optional[set] = None, decision_logger: Optional[Any] = None):
        self.armies_dict = armies_dict
        self.faction_doctrines = faction_doctrines
        self.faction_metadata = faction_metadata
        self.universe_rules = universe_rules
        self.defender_factions = defender_factions or set()
        self.decision_logger = decision_logger
        self.universe_state = {}
        self.active_factions = [f for f in armies_dict if len(armies_dict[f]) > 0]
        self.battle_stats = {
            f: {
                "routed_sum": 0, 
                "rounds_routed": 0,
                "intel_points_earned": 0,
                "enemy_tech_encountered": set(),
                "enemy_units_analyzed": [],
                "wreckage": [],
                "total_damage_dealt": 0.0
            } 
            for f in armies_dict
        }
        self.grid = None
        self.tracker = None
        self.round_num = 0
        self.mechanics_engine = None
        # Phase 250: Stalemate Detection
        self.rounds_since_last_damage = 0
        self.rounds_since_last_kill = 0
        self.total_damage_this_round = 0.0
        self.formations = [] # [PHASE 17.5] Real-Time Ground Formations
        # [PHASE 17.10] Victory Points & Objectives
        self.victory_points: Dict[str, float] = {f: 0.0 for f in armies_dict}
        self.vp_victory_threshold = 1000.0
        
        # [PHASE 18] Replay / History Buffers
        self.snapshots = []
        self.event_log = []
        self.total_sim_time = 0.0
        self.last_snapshot_time = -99.0 # Force immediate first snapshot
    def update_active_factions(self):
        """Updates the list of factions that still have living units."""
        self.active_factions = [f for f, units in self.armies_dict.items() if any(u.is_alive() for u in units)]

    def add_faction_units(self, faction: str, units: List[Any]):
        """
        Dynamically adds units to an existing battle state.
        Used by ActiveBattle when new fleets join.
        """
        if faction not in self.armies_dict:
            self.armies_dict[faction] = []
            if faction not in self.battle_stats:
                self.battle_stats[faction] = {
                    "routed_sum": 0,
                    "rounds_routed": 0,
                    "intel_points_earned": 0,
                    "enemy_tech_encountered": set(),
                    "enemy_units_analyzed": [],
                    "wreckage": [],
                    "total_damage_dealt": 0.0
                }
        
        self.armies_dict[faction].extend(units)
        
        # Log initial snapshot for new units
        if self.tracker:
            for u in units:
                if u.is_alive():
                    self.tracker.log_snapshot(u)
        
        self.update_active_factions()

    def initialize_battle(self, json_log_file=None, location_name=None, telemetry_collector=None, mechanics_engine=None, combat_domain=None):
        """Initializes the tactical grid and tracker."""
        self.mechanics_engine = mechanics_engine
        
        # Calculate Grid Size based on unit count (Scaling logic)
        total_units = sum(len(units) for units in self.armies_dict.values())
        
        if total_units < 20:
            grid_size = 30
        elif total_units < 60:
            grid_size = 50
        elif total_units >= 150:
            grid_size = 100
        else:
            grid_size = 80 # Default for transition range
            
        # [Total War / EaW] Infer Battle Type (Space or Ground)
        map_type = "Ground" # Default
        
        # Priority: Explicit Domain > Inference
        if combat_domain:
             # Normalize
             if combat_domain.lower() in ["space", "system", "void"]:
                  map_type = "Space"
             else:
                  map_type = "Ground"
        else:
            space_keywords = ["Ship", "Station", "Capital", "Frigate", "Destroyer", "Cruiser", "Battleship"]
            
            # Check if we have any space assets
            found_space = False
            for units in self.armies_dict.values():
                for u in units:
                    # Robust Space Check
                    is_space = False
                    if hasattr(u, 'domain') and getattr(u, 'domain') and getattr(u, 'domain').lower() == "space":
                         is_space = True
                    elif hasattr(u, 'is_ship') and u.is_ship():
                         is_space = True
                    else:
                         utype = getattr(u, 'type', '') or getattr(u, 'unit_class', '') or 'Unknown'
                         if any(x in utype for x in space_keywords):
                              is_space = True
                    
                    if is_space:
                         found_space = True
                         break
                if found_space: break
                
            if found_space:
                 map_type = "Space"
             
        # Initialize Managers
        from src.combat.grid.grid_manager import GridManager
        from src.combat.realtime.realtime_manager import RealTimeManager
        
        self.grid_manager = GridManager(grid_size, grid_size, map_type=map_type)
        self.grid = self.grid_manager.grid # Compatibility
        self.realtime_manager = RealTimeManager()
        
        # Initialize Tracker
        self.tracker = CombatTracker(json_path=json_log_file, universe_name=location_name, telemetry_collector=telemetry_collector)
        
        # [PHASE 30] Initialize Ability Manager
        from src.combat.ability_manager import AbilityManager
        registry = {}
        if self.mechanics_engine:
             registry = self.mechanics_engine.get_ability_registry() 
        else:
             from src.core.universe_data import UniverseDataManager
             registry = UniverseDataManager.get_instance().get_ability_database().copy()

        self.ability_manager = AbilityManager(registry)
        
        # Register units
        for f, units in self.armies_dict.items():
            for u in units:
                if u.is_alive():
                    # Initialize transient combat flags
                    if hasattr(u, 'init_combat_state'):
                        u.init_combat_state()
                        
                    # Placement Logic (Delegate to GridManager or keep here for scaling setup?)
                    # Keeping here as it's setup logic
                    curr_x = getattr(u, 'grid_x', None)
                    curr_y = getattr(u, 'grid_y', None)
                    
                    if curr_x is None or curr_y is None or (curr_x == 0 and curr_y == 0):
                         f_id = str(f).lower()
                         is_faction_a = ("factiona" in f_id) or (f_id.startswith("a")) or (f_id == "factiona")
                         
                         x_min = int(grid_size * 0.35)
                         x_max = int(grid_size * 0.45)
                         if not is_faction_a:
                             x_min = int(grid_size * 0.55)
                             x_max = int(grid_size * 0.65)
                         
                         name_hash = hash(u.name)
                         u.grid_x = x_min + (abs(name_hash) % (x_max - x_min + 1))
                         u.grid_y = (grid_size // 2) + (hash(u.name + "y") % 10 - 5)
                    
                    self.grid_manager.place_unit(u, u.grid_x, u.grid_y)
                    
        # Initial Snapshot
        for f, units in self.armies_dict.items():
            for u in units:
                if u.is_alive():
                    self.tracker.log_snapshot(u)

    def check_victory_conditions(self, force_result=False) -> tuple:
        self.update_active_factions()
        winner = "Draw"
        is_finished = force_result
        
        # Phase 250: Stalemate Breaker
        # If no damage has been dealt for a long time, force a draw
        # [FIX] Increased threshold (100 -> 1000) to allow for maneuver on massive maps
        if self.rounds_since_last_damage >= 500:
            is_finished = True
            winner = "Draw"
        elif self.rounds_since_last_kill >= 300:
            # New Breaker: If damage is happening but nobody is dying (Regen Loops), force decision
            is_finished = True
        elif len(self.active_factions) <= 1:
            winner = self.active_factions[0] if self.active_factions else "Draw"
            is_finished = True
            
        if is_finished and winner == "Draw":
            # [PHASE 16.5] Attacker-Lose Logic (Siege Failure)
            # If a stalemate occurs, the Defenders (Stationary Fleets) automatically Win.
            # The Attacker (Arriving Fleets) failed to dislodge them in time.
            
            forced_winner = None
            reason = ""
            
            # 1. Check if any Defender is present and alive
            # Priority: If ANY defender survives, they hold the ground.
            active_defenders = [f for f in self.defender_factions if f in self.active_factions]
            
            if active_defenders:
                 # Pick the strongest defender as the "Winner" for record keeping
                 # Or just the first one. Let's pick alphabetical for determinism or random?
                 # Tie-breaker logic isn't needed for "Who Wins", just "Defenders Win".
                 # But we need to return A winner string.
                 forced_winner = sorted(active_defenders)[0]
                 reason = "Siege Failed (Time Limit - Defenders Win)"
            else:
                 # 2. No Defenders present (Mutual Arrival or Detectors Dead) -> Fallback to Integrity Check
                 # Calculate Integrity % for all factions
                 best_faction = None
                 best_score = -1.0
                 best_max_hp = -1
                 
                 for f, units in self.armies_dict.items():
                    total_current = 0
                    total_max = 0
                    for u in units:
                        if u.is_alive():
                            total_current += u.current_hp
                            total_max += u.max_hp
                    
                    integrity = (total_current / total_max) if total_max > 0 else 0.0
                    
                    # Tie-Breaker Priority:
                    # 1. Higher Integrity %
                    # 2. Higher Total Max HP (Larger Fleet holds the field)
                    # 3. Alphabetical (Deterministic Fallback)
                    
                    if best_faction is None:
                        best_faction = f
                        best_score = integrity
                        best_max_hp = total_max
                    else:
                        # Compare
                        if integrity > best_score:
                            best_faction = f
                            best_score = integrity
                            best_max_hp = total_max
                        elif abs(integrity - best_score) < 0.001:
                            # Integrity Tie -> Check Size
                            if total_max > best_max_hp:
                                best_faction = f
                                best_score = integrity
                                best_max_hp = total_max
                 
                 if best_faction:
                      forced_winner = best_faction
                      reason = "Integrity/Size Check"
            
            if forced_winner:
                winner = forced_winner
                print(f"[DEBUG] Stalemate Resolved: {winner} wins via {reason} (Forced Retreats).")
                
                # Force Retreat on Losers
                for f, units in self.armies_dict.items():
                    if f != winner:
                        for u in units:
                            if u.is_alive():
                                u.is_routing = True
            else:
                # Should be impossible unless no factions exist
                winner = "Draw"
        
        survivors = 0
        if winner != "Draw":
            survivors = sum(1 for u in self.armies_dict[winner] if u.is_alive())
            
        return winner, survivors, is_finished

    def real_time_update(self, dt: float):
        """
        [PHASE 17] Real-Time Simulation Hook.
        Delegates to RealTimeManager.
        """
        self.realtime_manager.update(self, dt)

    def _take_snapshot(self):
        """Records unit positions and health for replay."""
        snap = {
            "timestamp": self.total_sim_time,
            "units": []
        }
        for f_name, units in self.armies_dict.items():
            for u in units:
                snap["units"].append({
                    "id": id(u),
                    "name": u.name,
                    "faction": f_name,
                    "x": round(u.grid_x, 2),
                    "y": round(u.grid_y, 2),
                    "hp": round(u.current_hp, 1),
                    "facing": round(getattr(u, 'facing', 0), 1),
                    "is_alive": u.is_alive()
                })
        self.snapshots.append(snap)

    def log_event(self, event_type: str, attacker: str, target: str, description: str = ""):
        """Logs a tactical event."""
        self.event_log.append({
            "timestamp": self.total_sim_time,
            "type": event_type,
            "attacker": attacker,
            "target": target,
            "description": description
        })

    def remove_retreating_units(self):
        """
        Removes units that have successfully retreated from the battlefield.
        (Atomic Engine Hook)
        """
        for f, units in self.armies_dict.items():
            # Identify units that have escaped (e.g. left grid bounds)
            # For now, we assume units marked 'is_escaped' are removed
            # This requires MovementCalculator to set this flag.
            
            # Simple cleanup of dead/escaped units from active lists if needed
            # self.armies_dict[f] = [u for u in units if not getattr(u, 'is_escaped', False)]
            pass

    def track_unit_destruction(self, faction, unit, killer_faction):
        """
        Records unit death for stats and telemetry (Atomic Engine Hook).
        """
        # Update Stats
        if faction not in self.battle_stats:
             self.battle_stats[faction] = {"units_lost": 0, "total_damage_dealt": 0, "kills": 0}
        
        self.battle_stats[faction]["units_lost"] = self.battle_stats[faction].get("units_lost", 0) + 1
        
        # Credit Killer
        if killer_faction:
            if killer_faction not in self.battle_stats:
                 self.battle_stats[killer_faction] = {"units_lost": 0, "total_damage_dealt": 0, "kills": 0}
            self.battle_stats[killer_faction]["kills"] = self.battle_stats[killer_faction].get("kills", 0) + 1

        # Log to Tracker
        if self.tracker:
            # log_event expects object with .name attribute
            class FactionWrapper:
                def __init__(self, name): self.name = name
            
            self.tracker.log_event("unit_death", FactionWrapper(killer_faction or "Unknown"), unit)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grid": self.grid,
            "tracker": self.tracker,
            "round_num": self.round_num,
            "active_factions": self.active_factions,
            "battle_stats": self.battle_stats,
            "armies_dict": self.armies_dict,
            "faction_doctrines": self.faction_doctrines,
            "faction_metadata": self.faction_metadata,
            "universe_rules": self.universe_rules,
            "universe_state": self.universe_state
        }

# Compatibility alias
CombatStateManager = CombatState
