import os
import time
import random
import hashlib
from typing import List, Dict, Set, Optional, Any, TYPE_CHECKING, Union
from src.core.constants import MAX_COMBAT_ROUNDS
from src.utils.profiler import profile_method
from src.reporting.telemetry import EventCategory, VerbosityLevel
from src.managers.combat.utils import ensure_tactical_ships
from src.combat.real_time.map_manager import MapGenerator
from src.managers.combat.retreat_handler import RetreatHandler
from src.managers.combat.invasion_manager import InvasionManager
from src.managers.combat.active_battle import ActiveBattle
from src.combat.tactical_engine import resolve_real_time_combat, resolve_fleet_engagement, initialize_battle_state, execute_battle_round

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.models.fleet import Fleet
    from src.models.planet import Planet
    from src.combat.combat_context import CombatContext
    from src.core.interfaces import IEngine

class BattleManager:
    """
    Handles all combat resolution:
    - Space Battles (Fleets)
    - Ground Invasions (Landing Logic)
    - Planet Battles (Ground War)
    """
    def __init__(self, context: Optional[Union['CombatContext', 'IEngine']] = None, log_dir: Optional[str] = None, campaign_engine: Optional['IEngine'] = None) -> None:
        self.context = context or campaign_engine
        self.log_dir: Optional[str] = log_dir
        self.max_combat_rounds: int = MAX_COMBAT_ROUNDS
        
        # Persistence
        self.active_battles: Dict[Any, ActiveBattle] = {} # Map Location -> ActiveBattle
        self.rounds_per_turn = 50 # Default
        if self.context and hasattr(self.context, 'game_config') and self.context.game_config:
            self.rounds_per_turn = self.context.game_config.get("combat", {}).get("rounds_per_turn", 50)
        
        # Managers
        self.invasion_manager = InvasionManager(self.context)
        self.retreat_handler = RetreatHandler(self.context)
            
        # Phase 2.1 Performance Indices
        self._fleets_by_location = {}
        self._armies_by_location = {}
        self._fleet_index = {} # Phase 1 Optimization: O(1) Fleet Lookup
        self._army_index = {} # Phase 1 Optimization: O(1) Army Lookup
        self._presence_index = {} # Phase 2 Optimization: O(1) Faction-at-Location index
        self._location_factions = {} # Map location -> set of faction names
        
        # Seeded RNG for non-battle operations (Invasions)
        self._manager_rng = random.Random()
        # Stats tracking
        self.battles_resolved_this_turn = 0
        self.battles_resolved_this_turn_space = 0
        self.battles_resolved_this_turn_ground = 0
        
        # [PHASE 6] Tech Scavenging
        # Winner scavenges logic from Loser's casualties
        # NOTE: This block is placed here temporarily for context, but it should logically be within a battle resolution method,
        # as 'winner' and 'loser' are not attributes of BattleManager's __init__.
        # Assuming 'self.engine' and 'self.log_event' would be available in the actual method.
        # For the purpose of this edit, it's inserted as requested, but it will cause a NameError if executed in __init__.
        # if winner != "Nobody" and winner != "Unknown": # This line would cause NameError in __init__
        #     winner_faction = self.engine.get_faction(winner)
        #     loser_faction = self.engine.get_faction(loser)
            
        #     if winner_faction and loser_faction and loser_faction.name != "Neutral":
        #         from src.utils.rng_manager import get_stream
        #         rng = get_stream("combat")
                
        #         # Chance to scavenge based on casualties
        #         scavenge_chance = 0.5 # 50% chance per battle? Or per unit?
        #         if rng.random() < scavenge_chance:
        #             # Pick a random tech/weapon from loser's arsenal?
        #             # Or better: check destroyed units for exotic components.
        #             # Simplified: Randomly pick one of loser's unlocked techs that winner doesn't have.
                    
        #             potential_theft = [t for t in loser_faction.unlocked_techs if t not in winner_faction.unlocked_techs]
        #             if potential_theft:
        #                 stolen = rng.choice(potential_theft)
        #                 # Filter out basic structural techs if needed, but "stealing tech" is broad.
        #                 # Only steal weapon/module techs?
        #                 # For now, steal anything.
        #                 self.engine.tech_manager.steal_technology(winner_faction, loser_faction, stolen)
        #                 self.log_event(winner, f"Scavenged technology '{stolen}' from defeated {loser} forces!")

        if self.log_dir and not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except OSError:
                pass

    def sanitize_state(self, all_fleets: List['Fleet'], all_planets: List['Planet']) -> None:
        """
        Phase 41: Critical Fix for AI Paralysis.
        Force-resets 'is_engaged' flags if no active battle exists at the unit's location.
        """
        # 1. Sanitize Fleets
        for fleet in all_fleets:
            if fleet.is_destroyed: continue
            
            if fleet.is_engaged:
                # Check if there is ACTUALLY a battle here
                if fleet.location not in self.active_battles:
                    # GHOST BATTLE DETECTED
                    print(f"  > [DEBUG] Force-releasing Fleet {fleet.id} (Ghost Engagement at {getattr(fleet.location, 'name', 'Void')})")
                    fleet.is_engaged = False
                else:
                    # Battle exists, but are we in it?
                    battle = self.active_battles[fleet.location]
                    if fleet.id not in battle.participating_fleets:
                         # We are at a battle site but not participating? 
                         # This usually logically implies we should join, but if we are flagged engaged but not in list, it's a bug.
                         print(f"  > [DEBUG] Force-releasing Fleet {fleet.id} (Flagged but not in battle roster)")
                         fleet.is_engaged = False
        
        # 2. Sanitize Armies
        for p in all_planets:
            # Check Planet-level armies
            if hasattr(p, 'armies'):
                for ag in p.armies:
                    if ag.is_engaged and p not in self.active_battles:
                        ag.is_engaged = False
            
            # Check Province-level armies
            if hasattr(p, 'provinces'):
                for node in p.provinces:
                    if hasattr(node, 'armies'):
                        for ag in node.armies:
                            if ag.is_engaged and node not in self.active_battles:
                                ag.is_engaged = False

    def resolve_space_battles(self, fast_resolve: bool = False) -> None:
        """Legacy wrapper, likely not used in sequential."""
        pass

    def _update_presence_indices(self):
        """Rebuilds location-based indices for fast lookup."""
        self._fleets_by_location = {}
        for f in self.context.get_all_fleets():
            if not f.is_destroyed:
                loc = f.location
                if loc not in self._fleets_by_location: self._fleets_by_location[loc] = []
                self._fleets_by_location[loc].append(f)
                
                # Phase 1 Optimization: O(1) Fleet Index
                self._fleet_index[f.id] = f
                
        self._armies_by_location = {}
        self._army_index = {}
        for p in self.context.get_all_planets():
            if hasattr(p, 'armies'):
                for ag in p.armies:
                    # [DOMAIN-FIX] Only index units that are actively on the ground 
                    # [DOMAIN-FIX] Exclude EMBARKED (on ships) or DESTROYED units
                    if not ag.is_destroyed and getattr(ag, 'state', '') != "EMBARKED":
                        # Use ag.location (Province) if available, otherwise fallback to Planet p
                        loc = ag.location if ag.location else p
                        if loc not in self._armies_by_location: self._armies_by_location[loc] = []
                        self._armies_by_location[loc].append(ag)
                        
                        # Phase 1 Optimization: O(1) Army Index
                        self._army_index[ag.id] = ag
        
        # Phase 2 Optimization: Rebuild Presence Index
        self._presence_index = {}
        self._location_factions = {}
        
        for loc, fleets in self._fleets_by_location.items():
            if loc not in self._location_factions: self._location_factions[loc] = set()
            for f in fleets:
                self._location_factions[loc].add(f.faction)
                self._presence_index[(f.faction, loc)] = True
                
        for loc, armies in self._armies_by_location.items():
            if loc not in self._location_factions: self._location_factions[loc] = set()
            for ag in armies:
                self._location_factions[loc].add(ag.faction)
                self._presence_index[(ag.faction, loc)] = True

    def get_factions_at(self, location: Any) -> Set[str]:
        """O(1) lookup for all factions at a location."""
        return self._location_factions.get(location, set())

    def is_faction_at(self, faction: str, location: Any) -> bool:
        """O(1) check if a faction is present at a location."""
        return (faction, location) in self._presence_index

    def get_fleet(self, fleet_id: str) -> Optional['Fleet']:
        """Optimization 1.2: O(1) fleet lookup by ID."""
        return self._fleet_index.get(fleet_id)

    def get_army_group(self, army_id: str) -> Optional['ArmyGroup']:
        """Optimization 1.2: O(1) army group lookup by ID."""
        return self._army_index.get(army_id)

    @profile_method
    def resolve_battles_at(self, location: Any, update_indices: bool = True, force_domain: Optional[str] = None, aggressor_faction: Optional[str] = None) -> None:
        """
        Checks for combat at a location (Planet or GraphNode).
        If Battle exists -> Units Join.
        If no Battle -> Create State.
        
        Args:
            aggressor_faction: The faction currently moving/acting. If provided, they are the Attacker.
        """
        # Update indices for current state (Phase 2.1 Optimization)
        if update_indices:
            self._update_presence_indices()

        if TYPE_CHECKING:
             from src.models.planet import Planet
             from src.models.simulation_topology import GraphNode
             assert isinstance(location, (Planet, GraphNode))

        # O(1) Lookup instead of O(N)
        # ... (rest of function unchanged, just need to match up to the end of the view)

    # Note: I need to target the resolve_ground_war separately or include it in the chunk if contiguous. 
    # They are far apart (line 116 vs 522). I should use MULTI_REPLACE.

        fleets_present = [f for f in self._fleets_by_location.get(location, []) if not getattr(f, 'destination', None)]
        armies_present = self._armies_by_location.get(location, [])
        
        # [DOMAIN-FIX] Strict Domain Separation
        # 1. If forced, obey.
        # 2. If auto, detect based on location type.
        if force_domain == "space":
            armies_present = []
        elif force_domain == "ground":
            fleets_present = []
        else:
            # Broaden domain detection based on GraphNode types and metadata
            space_types = ["Planet", "Star", "FluxGate", "System", "FluxPoint", "PortalNode"]
            ground_types = ["Province", "Capital", "LandingZone", "ProvinceCapital", "Wasteland", "Colony"]

            is_space_loc = (hasattr(location, 'is_star_system') or 
                            (hasattr(location, 'type') and location.type in space_types) or
                            # Planet object itself (orbital context)
                            location.__class__.__name__ == "Planet")

            is_ground_loc = (hasattr(location, 'parent_planet') or 
                             getattr(location, 'is_province', False) or 
                             (hasattr(location, 'type') and location.type in ground_types))

            if is_ground_loc:
                fleets_present = []
            if is_space_loc:
                armies_present = [] # Fallback: In space, don't fight ground troops unless forced
            
        if not fleets_present and not armies_present: 
            return

        factions_present = self.get_factions_at(location)

        # [QUIRK] Evasion Check
        # [FEATURE] Strategic Retreat Limit: Units that already retreated this turn are forced to fight.
        for faction in factions_present:
            f_mgr = self.context.get_faction(faction)
            if f_mgr and f_mgr.evasion_rating > 0:
                my_f = [f for f in fleets_present if f.faction == faction]
                
                # Check for prior retreats
                already_retreated = any(getattr(f, 'has_retreated_this_turn', False) for f in my_f)
                if already_retreated:
                    if self.context.logger:
                        self.context.logger.combat(f"[{faction}] Fleets at {getattr(location, 'name', 'node')} already retreated this turn. FORCED TO STAND AND FIGHT!")
                    continue

                en_f = [f for f in fleets_present if f.faction != faction]
                if my_f and en_f:
                    my_p = sum(f.power for f in my_f)
                    en_p = sum(f.power for f in en_f)
                    if en_p > my_p * 1.5:
                        if self._manager_rng.random() < f_mgr.evasion_rating:
                            if self.context.logger:
                                self.context.logger.combat(f"[EVASION] {faction} fleets at {getattr(location, 'name', 'node')} slipped away!")
                            
                            # Mark as retreated
                            for f in my_f:
                                f.has_retreated_this_turn = True
                            return

        # Check for existing battle
        if location in self.active_battles:
            self._join_active_battle(self.active_battles[location], location, fleets_present, armies_present)
            return

        # No battle. Check if we should START one.
        loc_owner = location.owner if hasattr(location, 'owner') else "Neutral"
        
        # [FIX] Ghost Interception: Valid Defender Check
        # A conflict only exists if there are ACTUAL DEFENDERS present.
        # This prevents battles triggering against dead starbases or empty planets.
        
        has_living_defenders = False
        
        # 1. Check Mobile Forces
        defender_fleets = [f for f in fleets_present if f.faction == loc_owner]
        defender_armies = [ag for ag in armies_present if ag.faction == loc_owner]
        if defender_fleets or defender_armies:
             has_living_defenders = True
             
        # 2. Check Static Defenses (Starbases)
        if not has_living_defenders:
             sb = getattr(location, 'starbase', None)
             # Handle Node Wrapper
             if not sb and hasattr(location, 'metadata'):
                  obj = location.metadata.get("object")
                  if obj and hasattr(obj, 'starbase'):
                       sb = obj.starbase
                       
             if sb and sb.faction == loc_owner and sb.is_alive():
                  has_living_defenders = True

        # Conflict Condition:
        # A. Multiple factions present (Fleet vs Fleet)
        # B. Hostile Faction vs Owner (IF Owner has living defenders)
        
        # [FIX] Peaceful Coexistence Logic
        # Combat only triggers between factions at WAR. 
        # Factions at Peace/Neutral/Alliance/Trade will be ignored by the combat engine.
        
        factions_without_owner = [f for f in factions_present if f != loc_owner]
        dm = getattr(self.context, 'diplomacy', None)
        active_combatants = set()
        
        if dm:
            # 1. Check which factions are at war with at least one other faction present
            # Optimization 1.1: Use War Matrix for O(F) set intersection
            factions_present_set = factions_present 
            for f in factions_present:
                # Find all enemies of f 
                enemies = dm.get_enemies(f)
                # If any of those enemies are also at this location, f is an active combatant
                if any(enemy in factions_present_set for enemy in enemies):
                    active_combatants.add(f)
            
            # 2. Check which invaders are at war with the location owner
            if loc_owner != "Neutral":
                for f_invader in factions_without_owner:
                    if dm.get_treaty(f_invader, loc_owner) == "War":
                        active_combatants.add(f_invader)
                        active_combatants.add(loc_owner)
            
            # 3. Filter the lists
            if active_combatants:
                fleets_present = [f for f in fleets_present if f.faction in active_combatants]
                armies_present = [ag for ag in armies_present if ag.faction in active_combatants]
                # Filter indices for this specific call (though index remains global)
                factions_present = set([f.faction for f in fleets_present] + [ag.faction for ag in armies_present])
                factions_without_owner = [f for f in factions_present if f != loc_owner]
            else:
                # No one is at war!
                # If multiple factions are present, return to avoid "Contact War" / accidental sieges.
                # If only ONE faction is present, allow fallthrough for potential colonization.
                if len(factions_present) > 1:
                    return

        # Conflict Condition (Refined):
        has_conflict = False
        if len(factions_present) > 1:
             has_conflict = True
        elif loc_owner != "Neutral" and factions_without_owner:
             # Only a conflict if the invader is at WAR with the owner
             if has_living_defenders:
                  has_conflict = True

        # DEBUG: Trace Conflict
        if len(fleets_present) > 0:
             print(f"[DEBUG] Resolve At {getattr(location, 'name', 'node')}: Fleets={len(fleets_present)}, ActiveCombatants={active_combatants}, Owner={loc_owner}, Conflict={has_conflict}")

        if has_conflict:
             print(f"[DEBUG] STARTING BATTLE at {getattr(location, 'name', 'node')}")
             self._initialize_new_battle(location, fleets_present, armies_present, factions_present, aggressor_faction=aggressor_faction)
        
        # Phase 21: Uncontested Expansion (Peaceful Annexation)
        elif len(factions_present) == 1:
            occupier = list(factions_present)[0]
            self._handle_unopposed_conquest(location, occupier)

    def _handle_unopposed_conquest(self, location, occupier):
        """Delegates to InvasionManager."""
        self.invasion_manager.handle_unopposed_conquest(location, occupier)

    @profile_method
    def process_active_battles(self, faction_filter: Optional[str] = None) -> None:
        """
        Ticks all active battles for N rounds.
        Also handles RETREATING fleets (removing units).
        If faction_filter is provided, only processes battles involving that faction.
        """
        completed = []
        
        # 3. Resolve Battles
        if self.active_battles: 
            pass
            
        for b_id, battle in list(self.active_battles.items()):
            
            # [Refactor] Faction Filter Logic
            # If we are in a faction turn, we only want to resolve battles that involve this faction.
            # This ensures they get the feedback during their turn.
            if faction_filter:
                factions_involved = set(battle.state.armies_dict.keys())
                if faction_filter not in factions_involved:
                    continue
            
            self._handle_retreats(battle, b_id) # Changed planet to b_id
            
            # Re-verify battle validity
            active_factions = [f for f, units in battle.state.armies_dict.items() if units]
            if len(active_factions) < 2:
                    if self.context.logger:
                        self.context.logger.combat(f"Battle at {getattr(b_id, 'name', 'node')} ending due to lack of enemies (Active: {active_factions}).")
                    battle.is_finished = True
                    completed.append(b_id)
                    continue

            use_real_time = self.context.game_config.get("combat", {}).get("real_time_headless", True)
            if self.context.logger:
                sim_mode = "Real-Time" if use_real_time else "Round-based"
                self.context.logger.combat(f"Resolving battle at {b_id.name if hasattr(b_id, 'name') else str(b_id)} ({sim_mode})...")
            
            # [ATOMIC] Resolve until finished
            winner = "Draw"
            survivors = 0
            active = True
            
            # [PHASE 18] Integrated Real-Time Headless Resolution
            # We use real-time for ALL battles if enabled in config or for specific domains.
            # For Phase 18, we default to Real-Time for Space and Ground engagements 
            # that have high unit counts or if specified.
            
            if use_real_time:
                # [Domain Detection]
                cdomain = "Ground"
                if hasattr(b_id, 'type'):
                     # If it's a System node or similar
                     if getattr(b_id, 'type', '') in ["System", "Sector", "Void"]:
                          cdomain = "Space"
                elif hasattr(b_id, 'is_planet') and not b_id.is_planet: # Assuming Node can distinguish
                     cdomain = "Space"
                
                # Check for class name as fallback
                if cdomain == "Ground" and "System" in type(b_id).__name__:
                     cdomain = "Space"

                winner, survivors, sim_time, stats = resolve_real_time_combat(
                    battle.state.armies_dict, 
                    silent=False, 
                    json_log_file=battle.json_file,
                    universe_rules=battle.state.universe_rules,
                    mechanics_engine=getattr(self.context, 'mechanics_engine', None),
                    combat_domain=cdomain
                )
                
                # [FIX] Sync Real-Time results back to battle.state for finalization
                battle.state.round_num = int(sim_time)
                battle.state.battle_stats = stats
                
                battle.is_finished = True
            else:
                # Safety limit from constants (2000 rounds)
                while not battle.is_finished and battle.state.round_num < self.max_combat_rounds:
                    # Track units before round for unit_destroyed detection
                    units_before = {f: len([u for u in units if u.is_alive()]) for f, units in battle.state.armies_dict.items()}
                    
                    winner, survivors, is_finished = execute_battle_round(battle.state, battle.log_file)
                    
                    if self.context.telemetry:
                        if battle.state.round_num % 10 == 0:
                            self.context.telemetry.log_event(
                                EventCategory.COMBAT, "combat_round",
                                {
                                    "location": b_id.name if hasattr(b_id, 'name') else str(b_id), 
                                    "round": battle.state.round_num, 
                                    "battle_id": getattr(battle, 'battle_id', ''),
                                    "damage_dealt": {f: stats.get("total_damage_dealt", 0) for f, stats in battle.state.battle_stats.items()}
                                },
                                turn=self.context.turn_counter
                            )
                        
                        units_after = {f: len([u for u in units if u.is_alive()]) for f, units in battle.state.armies_dict.items()}
                        for f in units_before:
                            deaths = units_before[f] - units_after.get(f, 0)
                            if deaths > 0:
                                for _ in range(deaths):
                                    self.context.telemetry.log_event(
                                        EventCategory.COMBAT, "unit_destroyed",
                                        {
                                            "battle_id": getattr(battle, 'battle_id', ''),
                                            "faction": f,
                                            "location": b_id.name if hasattr(b_id, 'name') else str(b_id),
                                            "turn": self.context.turn_counter
                                        },
                                        turn=self.context.turn_counter,
                                        faction=f
                                    )
                    
                    if is_finished:
                        battle.is_finished = True
                        break
            
            # Force finish if max rounds reached
            if not battle.is_finished:
                 if self.context.logger:
                     self.context.logger.combat(f"Battle at {getattr(b_id, 'name', 'node')} TIMED OUT at {self.max_combat_rounds} rounds. Forcing End.")
                 battle.is_finished = True
                 # If timed out, check victory conditions one last time or force Draw
                 # check_victory_conditions usually handles "Draw" if rounds > X.
                 # calling it manually might be needed if execute_battle_round didn't catch it
                 pass 

            self._finalize_battle(battle, b_id, winner, survivors, is_real_time=use_real_time)
            completed.append(b_id)

        # Cleanup completed battles
        for planet in completed:
            if planet in self.active_battles:
                del self.active_battles[planet]

    def _join_active_battle(self, battle: ActiveBattle, location: Any, fleets: List['Fleet'], armies: List['ArmyGroup']) -> None:
        if hasattr(location, 'is_sieged'): location.is_sieged = True
        
        # Add Fleets
        for f in fleets:
            if f.id not in battle.participating_fleets:
                if not getattr(f, 'is_engaged', False):
                    if hasattr(self.context, 'logger'):
                         self.context.logger.combat(f"[REINFORCE] Fleet {f.id} JOINING battle at {getattr(location, 'name', 'node')}")
                    
                    # [PHASE 6] Propagate Directive to fresh units
                    if hasattr(f, 'units') and hasattr(f, 'tactical_directive'):
                         for u in f.units:
                              u.tactical_directive = f.tactical_directive

                    battle.add_fleet(f)
                    f.is_engaged = True
            else:
                f.is_engaged = True
        
        # Add Armies
        for ag in armies:
            if ag.id not in battle.participating_armies:
                if not ag.is_engaged:
                    if hasattr(self.context, 'logger'):
                         self.context.logger.combat(f"[REINFORCE] Army {ag.id} JOINING battle at {getattr(location, 'name', 'node')}")
                    battle.add_army(ag)
            else:
                ag.is_engaged = True

    @profile_method
    def _initialize_new_battle(self, location: Any, fleets: List['Fleet'], armies: List['ArmyGroup'], factions: Set[str], aggressor_faction: Optional[str] = None) -> None:
        if hasattr(location, 'is_sieged'): 
            location.is_sieged = True
        
        armies_dict = {}
        start_fleet_ids = set()
        
        # Add Ships
        for f in fleets:
            ships = [u for u in f.units if u.is_ship() and u.is_alive()]
            if ships:
                if f.faction not in armies_dict: armies_dict[f.faction] = []
                tactical_ships = ensure_tactical_ships(ships)
                # Double check liveness after tactical conversion
                tactical_ships = [u for u in tactical_ships if u.is_alive()]
                
                for u in tactical_ships: 
                    u._fleet_id = f.id
                    # [PHASE 6] Propagate Tactical Directive
                    if hasattr(f, 'tactical_directive'):
                         u.tactical_directive = f.tactical_directive
                if tactical_ships:
                    armies_dict[f.faction].extend(tactical_ships)
                    f.is_engaged = True
                    start_fleet_ids.add(f.id)
        
        # Add Ground Units
        start_army_ids = set()
        for ag in armies:
            # Filter dead units
            valid_units = [u for u in ag.units if u.is_alive()]
            if valid_units:
                if ag.faction not in armies_dict: armies_dict[ag.faction] = []
                for u in valid_units: u._fleet_id = ag.id 
                armies_dict[ag.faction].extend(valid_units)
                ag.is_engaged = True
                start_army_ids.add(ag.id)
        
                ag.is_engaged = True
                start_army_ids.add(ag.id)
        
        # [FIX] Add Starbase (Static Defense)
        sb = getattr(location, 'starbase', None)
        # Handle Node Wrapper
        if not sb and hasattr(location, 'metadata'):
             obj = location.metadata.get("object")
             if obj and hasattr(obj, 'starbase'):
                  sb = obj.starbase
                  
        if sb and sb.is_alive():
             if sb.faction not in armies_dict: armies_dict[sb.faction] = []
             
             # Starbase is a Unit, add directly
             # Assign a dummy fleet_id for tracking
             sb._fleet_id = f"SB_{sb.faction}_{getattr(location, 'formatted_name', 'System')}"
             armies_dict[sb.faction].append(sb)
             # Starbases don't have 'is_engaged' flag usually managed by BattleManager logic, 
             # but we treat them as engaged units.
             if hasattr(self.context, 'logger'):
                  self.context.logger.combat(f"[DEFENSE] Starbase {sb.name} JOINING battle at {getattr(location, 'name', 'node')}")
        
        # DEBUG
        print(f"[DEBUG] _initialize_new_battle: Fleets={len(fleets)}, Armies={len(armies)}, ArmiesDict Keys={list(armies_dict.keys())}")
        if len(fleets) > 0:
             for i, f in enumerate(fleets):
                 print(f"[DEBUG] Fleet {f.id} (Faction: {f.faction}): {len(f.units)} units")
                 for j, u in enumerate(f.units[:3]):
                      print(f"  - Unit {j}: {u.name} (Class: {u.__class__.__name__}), is_ship={u.is_ship()}, is_alive={u.is_alive()}, HP={getattr(u, 'current_hp', 'N/A')}/{getattr(u, 'base_hp', 'N/A')}")
        
        if armies_dict:
            # Initialize State
            log_file = None
            json_log = None
            if self.log_dir:
                ts = int(time.time()*1000)
                # Standardized Naming: battle_{turn}_{location}_{ts}
                turn_str = f"{self.context.turn_counter:03d}"
                loc_clean = getattr(location, 'name', 'node').replace(" ", "_")
                
                fname = f"battle_{turn_str}_{loc_clean}_{ts}.txt"
                log_file = os.path.join(str(self.log_dir), fname)
                
                jname = f"battle_{turn_str}_{loc_clean}_{ts}.json"
                json_log = os.path.join(str(self.log_dir), jname)

            # Extract Doctrines
            faction_doctrines = {}
            faction_metadata = {} 
            
            for f in fleets:
                tf = self.context.strategic_ai.get_task_force_for_fleet(f)
                if tf:
                    doctrine = tf.combat_doctrine or tf.determine_combat_doctrine()
                    if f.faction not in faction_doctrines:
                        faction_doctrines[f.faction] = doctrine
                        
                    if f.faction not in faction_metadata:
                        faction_metadata[f.faction] = {
                            "faction_doctrine": getattr(tf, 'faction_combat_doctrine', 'STANDARD'),
                            "intensity": getattr(tf, 'doctrine_intensity', 1.0),
                            "turn_counter": self.context.turn_counter,
                            "evasion_rating": getattr(self.context.get_faction(f.faction), 'evasion_rating', 0),
                            "game_config": getattr(self.context, 'game_config', {})
                        }
            
            mechanics_engine = getattr(self.context, 'mechanics_engine', None)
            
            # Phase 16.5: Identify Defenders (Attacker-Lose Logic v3: Total War Style)
            defender_factions = set()
            
            if aggressor_faction:
                 # Explicit Aggressor (Sequential Turn Logic)
                 # ANYONE who is not the aggressor is a defender.
                 # "I moved here, so I am attacking everyone present."
                 
                 # Note: what if multiple enemies are present? They are all defenders relative to me.
                 # But are they defenders relative to each other?
                 # In a simple "King of the Hill" check:
                 # If Aggressor fails to win -> Defenders win.
                 # Who are the winners? Everyone not the aggressor.
                 
                 for f_name in factions:
                      if f_name != aggressor_faction:
                           defender_factions.add(f_name)
                           
            else:
                 # Fallback: Use Arrival Logic (simultaneous/neutral/unknown)
                 # 1. Fleets that did NOT arrive this turn are Defenders
                 for f in fleets:
                      if not getattr(f, 'arrived_this_turn', False):
                           defender_factions.add(f.faction)
                      
                 # 2. Armies are always Defenders (Resident)
                 for ag in armies:
                      if ag.faction not in defender_factions:
                           defender_factions.add(ag.faction)
            
            state = initialize_battle_state(
                armies_dict, 
                json_log_file=json_log, 
                faction_doctrines=faction_doctrines, 
                faction_metadata=faction_metadata, 
                location_name=getattr(location, 'name', str(location)), 
                mechanics_engine=mechanics_engine, 
                telemetry_collector=getattr(self.context, 'telemetry', None),
                defender_factions=defender_factions
            )

            # [DEBUG] Inspect Unit HP
            print(f"DEBUG: Battle at {location}")
            for f_name, dbg_units in armies_dict.items():
                alive_count = sum(1 for u in dbg_units if u.is_alive())
                total_count = len(dbg_units)
                hp_vals = [u.current_hp for u in dbg_units[:5]]
                print(f"  Faction {f_name}: {alive_count}/{total_count} alive. HP samples: {hp_vals}")
            
            # [PHASE 18.5] Apply Biome-based Map Features
            MapGenerator.generate_map(state.grid, location)
            
            battle = ActiveBattle(location, state, self.context.turn_counter, context=self.context)
            
            # [FIX] Populate pre_battle_counts for casualty calculation
            for f_name, units in state.armies_dict.items():
                battle.pre_battle_counts[f_name] = len(units)
                
            battle.log_file = log_file
            battle.json_file = json_log
            battle.participating_fleets = start_fleet_ids
            battle.participating_armies = start_army_ids
            
            self.active_battles[location] = battle
            
            self.context.telemetry.log_event(
                EventCategory.COMBAT, "battle_start",
                {"location": getattr(location, 'name', 'node'), "factions": list(factions), "battle_id": getattr(battle, 'battle_id', '')},
                turn=self.context.turn_counter
            )
            if self.context.logger:
                 self.context.logger.combat(f"BATTLE STARTED at {getattr(location, 'name', 'node')} between {list(factions)}")

            # Generate unique battle_id
            battle.battle_id = f"battle_{self.context.turn_counter}_{getattr(location, 'name', 'node')}_{hash(frozenset(factions)) & 0xFFFF}"

    @profile_method
    def _handle_retreats(self, battle: ActiveBattle, planet: Any) -> None:
        """Delegates to RetreatHandler."""
        self.retreat_handler.handle_retreats(battle, planet)

    def _log_battle_composition(self, battle: ActiveBattle, planet: Any):
        """Log battle composition telemetry."""
        if self.context.telemetry:
            for f_name in battle.state.armies_dict:
                units = battle.state.armies_dict.get(f_name, [])
                composition = self._get_force_composition(units)
                veterancy_levels = self._get_veterancy_levels(units)
                
                self.context.telemetry.log_event(
                    EventCategory.COMBAT,
                    "battle_composition",
                    {
                        "battle_id": getattr(battle, 'battle_id', ''),
                        "faction": f_name,
                        "turn": self.context.turn_counter,
                        "composition": composition,
                        "veterancy_levels": veterancy_levels
                    },
                    turn=self.context.turn_counter,
                    faction=f_name
                )
    
    def _get_force_composition(self, units: List[Any]) -> Dict[str, Any]:
        """Categorize units into composition types."""
        comp = {
            "capital_ships": {"count": 0, "lost": 0, "tier_avg": 0.0},
            "escorts": {"count": 0, "lost": 0, "tier_avg": 0.0},
            "ground_infantry": {"count": 0, "lost": 0},
            "ground_armor": {"count": 0, "lost": 0},
            "ground_artillery": {"count": 0, "lost": 0},
            "special_units": {"count": 0, "lost": 0}
        }
        tier_sum = {"capital": 0, "escort": 0}
        
        for u in units:
            if not u.is_alive():
                # Track lost units
                domain = getattr(u, 'domain', '')
                if domain == 'ground' or u.__class__.__name__ == 'Regiment':
                    if hasattr(u, 'ship_class'):
                        s_class = getattr(u, 'ship_class', 'Escort')
                        if s_class == "Battleship" or getattr(u, 'tier', 1) >= 3:
                            comp["capital_ships"]["lost"] += 1
                            tier_sum["capital"] += getattr(u, 'tier', 1)
                        else:
                            comp["escorts"]["lost"] += 1
                            tier_sum["escort"] += getattr(u, 'tier', 1)
                    else:
                        # Ground unit categorization
                        if hasattr(u, 'unit_type'):
                            u_type = getattr(u, 'unit_type', '')
                            if u_type == 'infantry':
                                comp["ground_infantry"]["lost"] += 1
                            elif u_type == 'armor':
                                comp["ground_armor"]["lost"] += 1
                            elif u_type == 'artillery':
                                comp["ground_artillery"]["lost"] += 1
                            else:
                                comp["special_units"]["lost"] += 1
                else:
                    # Track alive units
                    domain = getattr(u, 'domain', '')
                    if domain == 'ground' or u.__class__.__name__ == 'Regiment':
                        if hasattr(u, 'ship_class'):
                            s_class = getattr(u, 'ship_class', 'Escort')
                            if s_class == "Battleship" or getattr(u, 'tier', 1) >= 3:
                                comp["capital_ships"]["count"] += 1
                                tier_sum["capital"] += getattr(u, 'tier', 1)
                            else:
                                comp["escorts"]["count"] += 1
                                tier_sum["escort"] += getattr(u, 'tier', 1)
                        else:
                            # Ground unit categorization
                            if hasattr(u, 'unit_type'):
                                u_type = getattr(u, 'unit_type', '')
                                if u_type == 'infantry':
                                    comp["ground_infantry"]["count"] += 1
                                elif u_type == 'armor':
                                    comp["ground_armor"]["count"] += 1
                                elif u_type == 'artillery':
                                    comp["ground_artillery"]["count"] += 1
                                else:
                                    comp["special_units"]["count"] += 1
        
        # Calculate average tiers
        if comp["capital_ships"]["count"] > 0:
            comp["capital_ships"]["tier_avg"] = tier_sum["capital"] / comp["capital_ships"]["count"]
        if comp["escorts"]["count"] > 0:
            comp["escorts"]["tier_avg"] = tier_sum["escort"] / comp["escorts"]["count"]
        
        return comp
    
    def _get_veterancy_levels(self, units: List[Any]) -> Dict[str, int]:
        """Count veterancy levels of units."""
        levels = {"rookie": 0, "veteran": 0, "elite": 0}
        for u in units:
            if u.is_alive():
                xp = getattr(u, 'xp', 0)
                if xp < 100:
                    levels["rookie"] += 1
                elif xp < 300:
                    levels["veteran"] += 1
                else:
                    levels["elite"] += 1
        return levels
    
    @profile_method
    def _finalize_battle(self, battle: ActiveBattle, planet: Any, winner: str, survivors: int, is_real_time: bool = False) -> None:
        # Update Counters
        self.battles_resolved_this_turn += 1
        if battle.participating_fleets:
            self.battles_resolved_this_turn_space += 1
        else:
            self.battles_resolved_this_turn_ground += 1

        # Log battle composition telemetry
        self._log_battle_composition(battle, planet)
        
        # Calculate final intel points for all participants
        for f_name in battle.state.armies_dict:
            if f_name in battle.state.battle_stats:
                stats = battle.state.battle_stats[f_name]
                tech_count = len(stats.get("enemy_tech_encountered", set()))
                unit_count = len(stats.get("enemy_units_analyzed", []))
                intel_earned = (tech_count * 100) + (unit_count * 10)
                stats["intel_points_earned"] = intel_earned
                
                # Persist to faction model
                f_obj = self.context.get_faction(f_name)
                if f_obj and hasattr(f_obj, 'earn_intel') and intel_earned > 0:
                    f_obj.earn_intel(intel_earned, source="combat")

        self.context.telemetry.log_event(
            EventCategory.COMBAT, "battle_end",
            {
                "location": planet.name if hasattr(planet, 'name') else str(planet), 
                "winner": winner, 
                "rounds": battle.state.round_num, 
                "duration_seconds": round(time.time() - getattr(battle, 'start_time', time.time()), 2),
                "battle_id": getattr(battle, 'battle_id', ''),
                "casualties": {f: battle.pre_battle_counts.get(f, 0) - len([u for u in units if u.is_alive()]) 
                               for f, units in battle.state.armies_dict.items()}
            },
            turn=self.context.turn_counter
        )
        
        battle.state.tracker.finalize(winner, battle.state.round_num, battle.state.armies_dict, 
                                     pre_battle_counts=battle.pre_battle_counts,
                                     battle_id=getattr(battle, 'battle_id', None),
                                     battle_stats=battle.state.battle_stats,
                                     skip_save=is_real_time)
        
        loser_factions = [f for f in battle.state.armies_dict if f != winner]
        self.context.log_battle_result(getattr(planet, 'name', 'node'), winner, loser_factions, battle.state.round_num, survivors, battle_stats=battle.state.battle_stats)
        
        # [PHASE 6] Tech Scavenging (Post-Battle)
        if winner != "Draw" and winner != "Unknown" and loser_factions:
            winner_faction = self.context.get_faction(winner)
            # Pick primary loser (one with most casualties?) or just first
            loser_name = loser_factions[0]
            loser_faction = self.context.get_faction(loser_name)

            if winner_faction and loser_faction and loser_faction.name != "Neutral" and hasattr(self.context, 'tech_manager'):
                from src.utils.rng_manager import get_stream
                rng = get_stream("combat")
                
                # Chance to scavenge
                if rng.random() < 0.5:
                     # Identify potential thefts
                     potential = [t for t in loser_faction.unlocked_techs if t not in winner_faction.unlocked_techs]
                     # Filter out trivial ones?
                     potential = [t for t in potential if "Standard" not in t] # Heuristic
                     
                     if potential:
                         stolen = rng.choice(potential)
                         self.context.tech_manager.steal_technology(winner_faction, loser_faction, stolen)
                         # Log
                         if hasattr(self.context, 'logger'):
                             self.context.logger.info(f"[SCAVENGE] {winner} forces recovered {stolen} from {loser_name} wreckage!")
        
        # [QUIRK] Assimilation / On-Kill Effects
        winner_faction_mgr = self.context.get_faction(winner)
        if winner_faction_mgr:
             # Check quirk
             w_p = None
             if hasattr(winner_faction_mgr, 'learned_personality') and winner_faction_mgr.learned_personality:
                 w_p = winner_faction_mgr.learned_personality
             elif hasattr(self.context, 'strategic_ai'):
                 w_p = self.context.strategic_ai.get_faction_personality(winner)
             
             quirks = getattr(w_p, 'quirks', {}) if w_p else {}

        # MECHANICS HOOK: Battle End
        if hasattr(self.context, 'mechanics_engine'):
             # Trigger for ALL participants, win or lose
             participants = set(battle.state.armies_dict.keys())
             for f_name in participants:
                  f_obj = self.context.get_faction(f_name)
                  if f_obj:
                       context = {
                           "faction": f_obj, 
                           "planet": planet, 
                           "winner": winner, 
                           "is_winner": (f_name == winner),
                           "stats": battle.state.battle_stats.get(f_name, {})
                       }
                       self.context.mechanics_engine.apply_mechanics(f_name, "on_battle_end", context)

        self._sync_army_status(planet)
        self._sync_fleet_status(planet, winner)
        
        # Update Turn Counter
        self.battles_resolved_this_turn += 1
        if battle.participating_fleets:
            self.battles_resolved_this_turn_space += 1
        else:
            self.battles_resolved_this_turn_ground += 1
        
        faction_costs = {}
        total_casualties_cost = 0
        for f_name, units in battle.state.armies_dict.items():
            faction_costs[f_name] = {"initial": 0, "lost": 0}
            run_casualties = 0
            navy_lost = 0
            army_lost = 0
            
            for u in units:
                u_cost = getattr(u, 'cost', 100)
                faction_costs[f_name]["initial"] += u_cost
                
                if not u.is_alive():
                    faction_costs[f_name]["lost"] += u_cost
                    
                    # Track Casualties for Dashboard
                    f_mgr = self.context.get_faction(f_name)
                    if f_mgr and hasattr(f_mgr, 'stats'):
                        f_mgr.stats["turn_units_lost"] = f_mgr.stats.get("turn_units_lost", 0) + 1
                        f_mgr.stats["units_lost"] = f_mgr.stats.get("units_lost", 0) + 1
                        
                        if hasattr(u, 'is_ship') and u.is_ship():
                             f_mgr.stats["turn_ships_lost"] = f_mgr.stats.get("turn_ships_lost", 0) + 1
                             f_mgr.stats["ships_lost"] = f_mgr.stats.get("ships_lost", 0) + 1
                        else:
                             f_mgr.stats["turn_ground_lost"] = f_mgr.stats.get("turn_ground_lost", 0) + 1
                             f_mgr.stats["ground_lost"] = f_mgr.stats.get("ground_lost", 0) + 1
                        
                    run_casualties += 1
                    total_casualties_cost += u_cost
                    if hasattr(u, 'is_ship') and u.is_ship():
                        navy_lost += 1
                    else:
                        army_lost += 1
                else:
                    # [PHASE 11] Veterancy / Service Record
                    xp_gain = 50 # Base survival amount
                    if winner == f_name:
                         xp_gain += 100 # Victory Bonus
                    
                    rounds_survived = battle.state.round_num
                    xp_gain += (rounds_survived * 5)
                    
                    if hasattr(u, 'gain_xp'):
                        # [FIX] Ensure ability_manager is passed for level-up discovery
                        xp_context = {
                            "turn": self.context.turn_counter,
                            "ability_manager": getattr(battle.state, 'ability_manager', None),
                            "battle_state": battle.state
                        }
                        u.gain_xp(xp_gain, context=xp_context)
                    
                    if hasattr(u, 'log_service_event'):
                         outcome = "VICTORY" if winner == f_name else "DEFEAT"
                         loc_name = getattr(planet, 'name', str(planet))
                         u.log_service_event("BATTLE_SURVIVED", f"Survived Battle of {loc_name} ({outcome})", self.context.turn_counter)
            
            if run_casualties > 0:
                f_mgr = self.context.get_faction(f_name)
                # Note: f_mgr stats for ships_lost and ground_lost are already updated inside the unit loop.
                # We just ensure the total units_lost is synced if not already.
                if f_mgr and "units_lost" in f_mgr.stats:
                     pass # Already handled partially in u loop. 
                     # However, f_mgr.stats["units_lost"] += run_casualties was here.
                     # Let's clean it up to avoid double counting.

                if hasattr(self.context, 'telemetry') and self.context.telemetry:
                    self.context.telemetry.log_event(
                        EventCategory.CONSTRUCTION,
                        "unit_losses_report",
                        {
                            "count": run_casualties, 
                            "navy": navy_lost,
                            "army": army_lost,
                            "location": getattr(planet, 'name', str(planet))
                        },
                        turn=self.context.turn_counter, # Ensure turn context available
                        faction=f_name
                    )

            # Phase 22: War Exhaustion from Casualties
            if (navy_lost > 0 or army_lost > 0) and hasattr(self.context, 'diplomacy_manager'):
                 # Calculate Exhaustion Hit
                 # Ship: 0.5%, Army: 0.2%
                 exhaustion_hit = (navy_lost * 0.005) + (army_lost * 0.002)
                 
                 # Apply to all enemies in this battle
                 participants = list(battle.state.armies_dict.keys())
                 for enemy in participants:
                     if enemy == f_name: continue
                     # Check if actually at war? update_war_exhaustion doesn't check, 
                     # but logic implies we only care if we are hostile.
                     # However, safe to just push it. The DiploManager can decide if it sticks 
                     # (or we just accept that fighting causes exhaustion regardless of formal war).
                     # Current DiploManager logic expects 'War' state for passive gain, but for losses
                     # we likely want it to count even in skirmishes? 
                     # For now, let's call it.
                     self.context.diplomacy_manager.update_war_exhaustion(f_name, enemy, exhaustion_hit)
        
        if self.context.logger:
            # import time
            duration = time.time() - battle.start_time
            self.context.logger.combat(f"BATTLE ENDED at {getattr(planet, 'name', 'node')}. Winner: {winner} (Rounds: {battle.state.round_num}, Duration: {duration:.2f}s)")
        
        if winner != "Draw" and hasattr(planet, 'owner'):
            if planet.owner != winner:
                # [PHASE 20] Segregation of Space vs Ground Victories
                # 1. Did we win on the Ground? (Conquest)
                ground_victory = False
                
                # Check for surviving armies of the winner
                has_ground_presence = any(u.is_alive() and not u.is_ship() for u in battle.state.armies_dict.get(winner, []))
                
                # Check if defenders are purely wiped out on ground
                # Note: "Winner" implies enemy is wiped out or retreated.
                # If we have ground troops and won, it's a conquest.
                # But if we ONLY have ships, we can't capture.
                
                if has_ground_presence:
                     ground_victory = True
                
                if ground_victory:
                    # Trigger full conquest
                    if hasattr(self, 'invasion_manager'):
                        self.invasion_manager.handle_conquest(planet, winner, method="ground_invasion")
                    else:
                        # Fallback
                        self.context.update_planet_ownership(planet, winner)
                else:
                    # Space Victory Only -> Siege / Blockade
                    if hasattr(planet, 'is_sieged'):
                        planet.is_sieged = True
                        if self.context.logger:
                            self.context.logger.campaign(f"[SIEGE] {winner} has established orbital supremacy over {planet.name} (Production Blocked).")
        
        # Phase 14: Alliance Effectiveness (Joint Victories)
        if winner != "Draw" and getattr(self.context, 'diplomacy', None):
            participants = set(battle.state.armies_dict.keys())
            winner_allies = [p for p in participants if p != winner and self.context.diplomacy.get_treaty(winner, p) == "Alliance"]
            for ally in winner_allies:
                self.context.diplomacy.treaty_coordinator.log_alliance_interaction(winner, ally, "joint_victory")
        
        # [QUIRK] Casualty Plunder
        if total_casualties_cost > 0:
             participants = set(battle.state.armies_dict.keys())
             for f_name in participants:
                 f_mgr = self.context.get_faction(f_name)
                 if f_mgr and getattr(f_mgr, 'casualty_plunder_ratio', 0) > 0:
                      raid_income = int(total_casualties_cost * f_mgr.casualty_plunder_ratio)
                      if raid_income > 0:
                           f_mgr.requisition += raid_income
                           print(f"[DIAGNOSTIC] {f_name.upper()} PLUNDER: Gained {raid_income} Req from {total_casualties_cost} total casualty value.")
                           if self.context.logger:
                                self.context.logger.campaign(f"[{f_name.upper()}] Plunder! Gained {raid_income} Req from battle suffering (Value: {total_casualties_cost}).")

        # [PHASE 10] Task Force Performance Tracking
        if hasattr(self.context, 'strategic_ai') and self.context.strategic_ai:
            tf_mgr = getattr(self.context.strategic_ai, 'tf_manager', None)
            if tf_mgr:
                for f_name, units in battle.state.armies_dict.items():
                    # For each fleet in the battle, find its TaskForce and update stats
                    # For each fleet in the battle, find its TaskForce and update stats
                    involved_fleets = {u.fleet_id for u in units if hasattr(u, 'fleet_id')}
                    for fleet_id in involved_fleets:
                        # Optimized O(1) Lookup
                        fleet = self._fleet_index.get(fleet_id)
                        if fleet:
                            tf = tf_mgr.get_task_force_for_fleet(fleet)
                            if tf:
                                if f_name == winner:
                                    tf.battles_won += 1
                                elif winner != "Draw":
                                    tf.battles_lost += 1
                                # Track enemies destroyed if we can calculate it
                                if f_name == winner:
                                    loser_initial = sum(v["initial"] for k, v in faction_costs.items() if k != winner)
                                    tf.enemies_destroyed += (loser_initial / 100) # Proxy value

        # [TELEMETRY] Phase 2: Combat Metrics
        if self.context.telemetry:
            self._log_battle_decisiveness(battle, winner, faction_costs, total_casualties_cost, planet)
            self._log_doctrine_performance(battle)

    def _log_battle_decisiveness(self, battle, winner, faction_costs, total_lost_value, planet):
        """Calculates and logs battle decisiveness (Metric #3)."""
        winner_stats = faction_costs.get(winner, {"initial": 1, "lost": 0})
        winner_loss_pct = (winner_stats["lost"] / winner_stats["initial"]) if winner_stats["initial"] > 0 else 0.0
        
        # Aggregate loser stats
        loser_initial = 0
        loser_lost = 0
        for f, stats in faction_costs.items():
            if f != winner:
                loser_initial += stats["initial"]
                loser_lost += stats["lost"]
        
        loser_loss_pct = (loser_lost / loser_initial) if loser_initial > 0 else 0.0
        
        # Determine Label
        label = "marginal"
        if winner_loss_pct < 0.10 and loser_loss_pct > 0.50:
            label = "overwhelming"
        elif winner_loss_pct < 0.30 and loser_loss_pct > 0.50:
            label = "decisive"
        elif winner_loss_pct > 0.40:
            label = "pyrrhic"
            
        self.context.telemetry.log_event(
            EventCategory.COMBAT,
            "battle_decisiveness",
            {
                "battle_id": getattr(battle, 'battle_id', ''),
                "winner": winner,
                "decisiveness": label,
                "winner_loss_pct": winner_loss_pct,
                "loser_loss_pct": loser_loss_pct,
                "total_value_destroyed": total_lost_value,
                "location": getattr(planet, 'name', str(planet))
            },
            turn=self.context.turn_counter
        )

    def _log_doctrine_performance(self, battle):
        """Logs doctrine performance for each faction (Metric #4)."""
        # Determine intensity/rounds
        rounds = battle.state.round_num
        
        # Access doctrines if available in state
        doctrines = getattr(battle.state, 'faction_doctrines', {})
        
        for f_name, doctrine in doctrines.items():
            # Calculate simple performance metrics
            # We can use battle_stats if populated, or simplistic win/loss if we know who won
            # For now, let's log participation and basic attrition
            stats = getattr(battle.state, 'battle_stats', {}).get(f_name, {})
            # Note: battle_stats might not be fully populated with attrition yet in all versions
            
            self.context.telemetry.log_event(
                EventCategory.COMBAT,
                "doctrine_combat_performance",
                {
                    "faction": f_name,
                    "doctrine": doctrine,
                    "rounds_lasted": rounds,
                    # We could add more deep stats here if CombatSimulator exposes them
                },
                turn=self.context.turn_counter,
                faction=f_name
            )

    def _enforce_tech_lock(self, planet: 'Planet', new_owner: str) -> None:
        """Delegates to InvasionManager."""
        self.invasion_manager.enforce_tech_lock(planet, new_owner)

    def _sync_fleet_status(self, planet, winner="Draw"):
        """Checks fleets at planet, marks destroyed if empty."""
        fleets = [f for f in self.context.fleets if f.location == planet]
        for f in fleets:
            # Remove dead units
            f.units = [u for u in f.units if u.is_alive()]
            if not f.units:
                f.is_destroyed = True
                f.is_engaged = False # Release
                f.cargo_armies.clear() # Clear cargo on destruction
                f.invalidate_caches()
                if self.context.logger:
                    self.context.logger.combat(f"[DESTROYED] Fleet {f.id} destroyed.")
                
                # [PHASE 4] Grudge Trigger: Destruction
                if winner != "Draw" and f.faction != winner and getattr(self.context, 'diplomacy', None):
                     self.context.diplomacy.add_grudge(f.faction, winner, 15, f"Destroyed Fleet {f.id}")
            else:
                f.is_engaged = False
                f.invalidate_caches()

    def _sync_army_status(self, location):
        """Phase 18: Checks armies at location, marks destroyed if empty and releases engagement lock."""
        armies = []
        if hasattr(location, 'armies'):
            armies = [ag for ag in location.armies]
        
        for ag in armies:
            # Remove dead units
            ag.units = [u for u in ag.units if u.is_alive()]
            if not ag.units:
                ag.is_destroyed = True
                ag.is_engaged = False
                if self.context.logger:
                    self.context.logger.combat(f"[DESTROYED] Army {ag.id} wiped out at {getattr(location, 'name', 'node')}.")
            else:
                ag.is_engaged = False # Release lock if battle over

    def _resolve_battles_detailed(self) -> None:
        """Deprecated."""
        pass

    @profile_method
    def resolve_ground_war(self, faction_filter: Optional[str] = None) -> int:
        """Resolves ground combat between armies on specific province nodes."""
        battles_started = 0
        
        # Optimization: Update indices ONCE per phase instead of per node
        self._update_presence_indices()
        
        for p in self.context.all_planets:
            # Filter Logic: Skip planet if faction not present
            if faction_filter:
                has_presence = False
                for ag in p.armies:
                     if ag.faction == faction_filter:
                         has_presence = True
                         break
                
                # Check provinces too if main list empty
                if not has_presence and hasattr(p, 'provinces'):
                    for prov in p.provinces:
                         for ag in prov.armies:
                             if ag.faction == faction_filter:
                                 has_presence = True
                                 break
                         if has_presence: break
                
                if not has_presence: continue

            if hasattr(p, 'provinces') and p.provinces:
                for node in p.provinces:
                    self.resolve_battles_at(node, update_indices=False, force_domain="ground")
                    if node in self.active_battles:
                        battles_started += 1
            else:
                # Abstract planet fallback (legacy)
                self.resolve_battles_at(p, update_indices=False, force_domain="ground")
                if p in self.active_battles:
                    battles_started += 1
        return battles_started

    @profile_method
    def process_invasions(self, faction_filter: Optional[str] = None) -> None:
        """Delegates to InvasionManager."""
        self.invasion_manager.process_invasions(faction_filter=faction_filter)

    def embark_army(self, fleet: 'Fleet', army_group: 'ArmyGroup') -> bool:
        """Army boards a Fleet (Transport)."""
        return self.invasion_manager.embark_army(fleet, army_group)

    def disembark_army(self, fleet: 'Fleet', target_node: Any) -> None:
        """Army unloads from Fleet to Planet Node."""
        self.invasion_manager.disembark_army(fleet, target_node)

    def land_armies(self, fleet: 'Fleet', planet: Any) -> None:
        """Wrapper for AI invasion logic."""
        self.invasion_manager.land_armies(fleet, planet)

    def _seed_manager_rng(self, location: Any):
        """Deprecated: Logic moved to InvasionManager."""
        pass
        
    def _calculate_faction_losses(self, faction: str, units: List[Any]) -> float:
        """Calculates total resource value of lost units for a faction."""
        total_lost = 0.0
        for u in units:
            if not u.is_alive():
                total_lost += getattr(u, 'cost', 150.0)
        return total_lost

    def _get_force_composition(self, units: List[Any]) -> Dict[str, int]:
        """Categorizes units into capital ships, escorts, and ground units."""
        comp = {"capital_ships": 0, "escorts": 0, "ground_units": 0}
        for u in units:
            if getattr(u, 'domain', '') == 'ground' or u.__class__.__name__ == 'Regiment':
                comp["ground_units"] += 1
            elif u.__class__.__name__ == 'Ship' or getattr(u, 'domain', '') == 'space':
                s_class = getattr(u, 'ship_class', 'Escort')
                tier = getattr(u, 'tier', 1)
                if s_class == "Battleship" or tier >= 3:
                    comp["capital_ships"] += 1
                elif s_class in ["Escort", "Cruiser"]:
                    comp["escorts"] += 1
                else:
                    comp["escorts"] += 1
        return comp

    def _calculate_attrition_rate(self, initial_count: int, current_count: int) -> float:
        """Calculates percentage of units lost."""
        if initial_count <= 0:
            return 0.0
        return ((initial_count - current_count) / initial_count) * 100.0
