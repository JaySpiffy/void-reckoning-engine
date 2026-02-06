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
from src.combat.management.state_manager import BattleStateManager
from src.combat.management.battle_logger import BattleLogger
from src.combat.management.resolution_factory import BattleResolutionFactory

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
            
        # Refactored Components
        self.state_mgr = BattleStateManager(self.context)
        self.battle_logger = BattleLogger(self.context)
        self.resolution_factory = BattleResolutionFactory(self.context, self.state_mgr, self.battle_logger)

        # Legacy Aliases (For Backward Compatibility)
        self.active_battles = self.state_mgr.active_battles
        self._fleet_index = self.state_mgr._fleet_index
        self._army_index = self.state_mgr._army_index
        self._presence_index = self.state_mgr._presence_index
        self._location_factions = self.state_mgr._location_factions
        
        # Seeded RNG for non-battle operations (Invasions)
        self._manager_rng = random.Random()
        # Stats tracking
        self.battles_resolved_this_turn = 0
        self.battles_resolved_this_turn_space = 0
        self.battles_resolved_this_turn_ground = 0

    # --- DELEGATION HELPERS ---
    def get_factions_at(self, location: Any) -> Set[str]:
        return self.state_mgr.get_factions_at(location)

    def get_fleets_at(self, location: Any) -> List['Fleet']:
        return self.state_mgr.get_fleets_at(location)

    def get_armies_at(self, location: Any) -> List['ArmyGroup']:
        return self.state_mgr.get_armies_at(location)

    def get_fleet(self, fleet_id: str) -> Optional['Fleet']:
        return self.state_mgr.get_fleet(fleet_id)

    def get_army_group(self, army_id: str) -> Optional['ArmyGroup']:
        return self.state_mgr.get_army_group(army_id)
        
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
        self.state_mgr.update_indices()

    def get_factions_at(self, location: Any) -> Set[str]:
        """O(1) lookup for all factions at a location."""
        return self.state_mgr.get_factions_at(location)

    def is_faction_at(self, faction: str, location: Any) -> bool:
        """O(1) check if a faction is present at a location."""
        return self.state_mgr.is_faction_at(faction, location)

    def get_fleet(self, fleet_id: str) -> Optional['Fleet']:
        """Optimization 1.2: O(1) fleet lookup by ID."""
        return self.state_mgr.get_fleet(fleet_id)

    def get_army_group(self, army_id: str) -> Optional['ArmyGroup']:
        """Optimization 1.2: O(1) army group lookup by ID."""
        return self.state_mgr.get_army_group(army_id)

    @profile_method
    def resolve_battles_at(self, location: Any, update_indices: bool = True, force_domain: Optional[str] = None, aggressor_faction: Optional[str] = None) -> None:
        """Facade method for checking and starting combat."""
        if update_indices:
            self._update_presence_indices()

        # Check for existing battle
        active_battle = self.state_mgr.get_active_battle(location)

        # Get forces at location
        fleets_present = [f for f in self.state_mgr.get_fleets_at(location) if not getattr(f, 'destination', None)]
        armies_present = self.state_mgr.get_armies_at(location)

        # Apply Domain Constraints
        domain_hint = force_domain or self.resolution_factory.determine_domain(location)
        if domain_hint == "space": armies_present = []
        elif domain_hint == "ground": fleets_present = []

        if not fleets_present and not armies_present:
            return

        factions_present = self.get_factions_at(location)

        # Evasion Check
        for faction in factions_present:
            if self.resolution_factory.handle_evasion(faction, location, fleets_present):
                if self.context.logger:
                    self.context.logger.combat(f"[EVASION] {faction} fleets at {getattr(location, 'name', 'node')} slipped away!")
                return

        # Join existing or start new
        if active_battle:
            self._join_active_battle(active_battle, location, fleets_present, armies_present)
        else:
            if self.resolution_factory.check_conflict(location, fleets_present, armies_present, factions_present):
                new_battle = self.resolution_factory.initialize_battle(location, fleets_present, armies_present, factions_present, aggressor_faction)
                if new_battle:
                    self.state_mgr.register_battle(location, new_battle)
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
    def _handle_retreats(self, battle: ActiveBattle, planet: Any) -> None:
        """Delegates to RetreatHandler."""
        self.retreat_handler.handle_retreats(battle, planet)
    
    @profile_method
    def _finalize_battle(self, battle: ActiveBattle, planet: Any, winner: str, survivors: int, is_real_time: bool = False) -> None:
        # Update Counters
        self.battles_resolved_this_turn += 1
        if battle.participating_fleets:
            self.battles_resolved_this_turn_space += 1
        else:
            self.battles_resolved_this_turn_ground += 1

        # Log battle composition telemetry
        self.battle_logger.log_battle_composition(battle, planet)
        
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
                        fleet = self.get_fleet(fleet_id)
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
            self.battle_logger.log_battle_decisiveness(battle, winner, faction_costs, total_casualties_cost, planet)
            self.battle_logger.log_doctrine_performance(battle)

        # Remove from active battles
        self.state_mgr.remove_battle(planet)

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
                
                # [FIX] Ensure transported troops are destroyed with the fleet
                if hasattr(f, 'cargo_armies') and f.cargo_armies:
                    for ag in f.cargo_armies:
                        if not ag.is_destroyed:
                            ag.is_destroyed = True
                            num_troops = len(ag.units)
                            ag.units.clear() # Wipe units
                            
                            if self.context.telemetry:
                                self.context.telemetry.log_event(
                                    EventCategory.COMBAT, "troops_lost_in_space",
                                    {
                                        "fleet_id": f.id,
                                        "army_id": ag.id,
                                        "faction": ag.faction,
                                        "location": getattr(planet, 'name', 'Void'),
                                        "troops_count": num_troops
                                    },
                                    turn=self.context.turn_counter,
                                    faction=ag.faction
                                )
                            if self.context.logger:
                                self.context.logger.combat(f"  > [CASUALTY] {ag.id} ({num_troops} troops) lost in space with Fleet {f.id}")

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
