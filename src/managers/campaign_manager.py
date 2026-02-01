import os
import sys
import csv
import json
import random
import hashlib
from datetime import datetime
import math
import functools
import time
from queue import Queue, Empty
from collections import deque
import traceback
from typing import Dict, Any, Callable, Optional, List, TYPE_CHECKING, Union
import src.core.config as config
from src.core.config import REPORTS_DIR, SAVES_DIR, ACTIVE_UNIVERSE, set_active_universe, get_universe_config
from src.utils.profiler import profile_method
from src.managers.turn_processor import TurnProcessor
from src.core.constants import (
    AGREEMENT_NUMERALS, 
    MAX_COMBAT_ROUNDS, MAX_FLEET_SIZE, MAX_LAND_UNITS, BUILD_TIME_DIVISOR, MAX_BUILD_TIME, VICTORY_PLANET_THRESHOLD,
    COLONIZATION_REQ_COST
)
from src.core.universe_data import UniverseDataManager
from src.models.planet import Planet
from src.models.army import ArmyGroup
from src.models.faction import Faction
from src.models.fleet import Fleet
from src.managers.tech_manager import TechManager
from src.managers.diplomacy_manager import DiplomacyManager
from src.managers.weather_manager import FluxStormManager
from src.managers.ai_manager import StrategicAI
from src.combat.combat_simulator import parse_unit_file
from src.models.unit import Unit
from src.reporting.telemetry import TelemetryCollector, EventCategory, VerbosityLevel
from src.reporting.organizer import ReportOrganizer
from src.reporting.faction_reporter import FactionReporter
from src.core.game_config import GameConfig

# Decomposed Managers
from src.managers.campaign.orchestrator import CampaignOrchestrator
from src.managers.galaxy_generator import GalaxyGenerator, init_galaxy_rng
from src.managers.asset_manager import AssetManager
from src.managers.intelligence_manager import IntelligenceManager
from src.managers.portal_manager import PortalManager
from src.managers.fleet_manager import FleetManager
from src.managers.weather_manager import FluxStormManager
from src.ai.strategies.standard import StandardStrategy
from src.managers.cache_manager import CacheManager
from src.services.construction_service import ConstructionService

from src.managers.banking_manager import BankingManager # [Iron Bank]
from src.managers.battle_manager import BattleManager
from src.utils.audio import AudioManager # [Audio]
from src.utils.spatial_index import SpatialGrid # [Performance]
from src.managers.mission_manager import MissionManager
from src.managers.scenario_manager import ScenarioManager
from src.managers.persistence_manager import PersistenceManager
from src.managers.galaxy_state_manager import GalaxyStateManager # [Item 2.2]
from src.managers.faction_manager import FactionManager # [Item 2.2]
from src.managers.fleet_queue_manager import FleetQueueManager # [Item 1.5]
from src.core.interfaces import IEngine
from queue import Empty

from src.utils.game_logging import GameLogger, LogCategory
from src.services.pathfinding_service import PathfindingService

class CampaignEngine:
    def __init__(self, battle_log_dir: Optional[str] = None, game_config: Optional[Union[Dict[str, Any], GameConfig]] = None, report_organizer: Optional[object] = None, universe_name: Optional[str] = None, telemetry_collector: Optional[object] = None, manager_overrides: Optional[Dict[str, Any]] = None):
        """
        Initializes the Campaign Engine, the central controller for the simulation.
        
        Manages the galaxy state, factions, fleets, armies, and turn processing.
        """
        from src.managers.campaign_initializer import CampaignInitializer
        
        initializer = CampaignInitializer(
            self, 
            battle_log_dir=battle_log_dir, 
            game_config=game_config, 
            report_organizer=report_organizer, 
            universe_name=universe_name, 
            telemetry_collector=telemetry_collector, 
            manager_overrides=manager_overrides
        )
        initializer.initialize()
        
        # [PHASE 5] Orchestrator Initialization
        overrides = manager_overrides or {}
        self.orchestrator = overrides.get("orchestrator") or CampaignOrchestrator(self)
        
        # Turn Processor remains here as it's tightly coupled to the engine instance logic
        self.turn_processor = TurnProcessor(self)
        
        # Init remaining managers (Phase 32 Analytics)
        self.mission_manager = MissionManager(self.logger)
        self.banking_manager = BankingManager(self) # [Iron Bank]
        self.scenario_manager = ScenarioManager(self)
        self.persistence_manager = PersistenceManager(self)
        self.stats_history: List[Dict[str, Any]] = []
        
        # Campaign Milestone Tracking
        self._campaign_milestones: List[Dict[str, Any]] = []
        self._victory_progress_history: Dict[str, List[Dict[str, Any]]] = {}
        self._milestone_turns = {
            'first_battle': None,
            'first_conquest': None,
            'first_alliance': None,
            'major_expansion': None,
            'tech_breakthrough': None
        }
        
        # Log Campaign Start
        if self.telemetry:
            # Generate a stable campaign ID if not present
            self.campaign_id = hashlib.md5(f"{universe_name or 'unknown'}_{getattr(self, 'turn_counter', 0)}_{id(self)}".encode()).hexdigest()[:12]
            
            self.telemetry.log_event(
                EventCategory.CAMPAIGN,
                "campaign_started",
                {
                    "campaign_id": self.campaign_id,
                    "universe": universe_name or "unknown",
                    "factions": list(self.factions.keys()),
                    "settings": {
                        "universe": ACTIVE_UNIVERSE,
                        "max_fleet_size": self.max_fleet_size,
                        "max_rounds": self.max_combat_rounds
                    }
                },
                turn=0
            )
        
        # Register Caches (Post-Init)
        # Note: Some cache registration logic is split between initializer and here depending on object availability
        # Ideally, move all to initializer, but keeping here for safety during refactor
        
        self._progress_q_ref = None

    # [Item 2.2] Proxy Properties for Backward Compatibility
    @property
    def systems(self) -> List[Any]:
        return self.galaxy_manager.get_all_systems()
        
    @systems.setter
    def systems(self, value):
        self.galaxy_manager.set_systems(value)

    @property
    def all_planets(self) -> List[Planet]:
        return self.galaxy_manager.get_all_planets()

    @property
    def factions(self) -> Dict[str, Faction]:
        return self.faction_manager.factions

    @property
    def fleets(self) -> List[Any]:
        return self.fleet_manager.fleets

    @property
    def fleets_by_faction(self) -> Dict[str, List[Any]]:
        return self.fleet_manager.fleets_by_faction

    @property
    def planets_by_faction(self) -> Dict[str, List[Planet]]:
        return self.galaxy_manager.planets_by_faction
        
    @planets_by_faction.setter
    def planets_by_faction(self, value):
        self.galaxy_manager.planets_by_faction = value

    def log_performance_metrics(self):
        """Log aggregated performance metrics."""
        summary = {}
        if self.logger:
            self.logger.system("=== PERFORMANCE METRICS ===")
            for metric, times in self.performance_metrics.items():
                if times:
                    avg = sum(times) / len(times)
                    max_time = max(times)
                    self.logger.system(f"{metric}: avg={avg:.2f}ms, max={max_time:.2f}ms, calls={len(times)}")
                    summary[metric] = {
                        "avg_ms": round(avg, 2),
                        "max_ms": round(max_time, 2),
                        "calls": len(times)
                    }
            
            # Cache Statistics
            cache_stats = self.cache_manager.get_statistics()
            self.logger.system(f"Cache Statistics: {cache_stats['registered_caches']} caches, {cache_stats['clear_count']} clears")
            summary["cache"] = cache_stats
            
            # Economy Metrics
            if hasattr(self, 'economy_manager') and hasattr(self.economy_manager, 'perf_metrics'):
                em = self.economy_manager
                self.logger.system("=== ECONOMY PERFORMANCE ===")
                self.logger.system(f"  Avg Upkeep Calc: {em.perf_metrics['upkeep_calc_time']:.2f}ms")
                self.logger.system(f"  Avg Insolvency: {em.perf_metrics['insolvency_time']:.2f}ms")
                self.logger.system(f"  Units Disbanded: {em.perf_metrics['disbanded_count']}")
                summary["economy"] = em.perf_metrics
                
            self.logger.system("===========================\n")
            
        # Log to Telemetry
        if self.telemetry:
            self.telemetry.log_performance_summary(summary, self.turn_counter)
            
        # Reset metrics for next turn/interval to ensure per-turn aggregation (Comment 4)
        self.performance_metrics = {k: [] for k in self.performance_metrics.keys()}
        if hasattr(self, 'economy_manager') and hasattr(self.economy_manager, 'perf_metrics'):
             # Reset economy metrics too if they are accumulators? 
             # Assuming economy_manager handles its own reset or we should trigger it.
             # For now, just resetting the engine-level aggregator behavior.
             pass
        
    def clear_turn_caches(self):
        """Central turn-boundary hook: Clears and then warms all registered caches."""
        if self.logger:
            self.logger.debug("Executing turn-boundary cache refresh (Clear + Warm)...")
        self.cache_manager.refresh_all(self)

    def _warm_threat_assessments(self, engine):
        """Pre-calculates threat levels for all owned planets to speed up strategic AI."""
        if not hasattr(self, 'all_planets'): return
        
        for planet in self.all_planets:
            if planet.owner != "Neutral":
                 # Trigger calculation to fill LRU cache
                 self.intel_manager.calculate_threat_level(planet.name, planet.owner, self.turn_counter)
        
    def attach_dashboard(self):
        """Attempts to attach telemetry to the live dashboard if active."""
        if hasattr(self, 'orchestrator'):
            return self.orchestrator.attach_dashboard()
        return False
        
        # [REFACTORED] Logic moved to DashboardManager



    # --- Accessors (Item 5.4) ---
    def get_faction(self, faction_name: str) -> Optional[Any]:
        return self.factions.get(faction_name)

    def add_faction(self, faction: Any) -> None:
        """Central method to register a new faction in the engine state."""
        if faction.name not in self.factions:
            self.factions[faction.name] = Faction(faction.name) # Ensure Faction object is created
            if self.logger: self.logger.info(f"[ENGINE] Added faction: {faction.name}")

    def get_planet(self, planet_name: str) -> Optional[Any]:
        return next((p for p in self.all_planets if p.name == planet_name), None)

    def get_all_factions(self) -> List[Any]:
        return list(self.factions.values())

    def get_all_planets(self) -> List[Any]:
        return self.all_planets

    def get_all_fleets(self) -> List[Any]:
        """Delegates to FleetManager (Item 3.1)."""
        return self.fleet_manager.get_all_fleets()

    def get_fleets_by_faction(self, faction_name: str) -> List[Any]:
        """Delegates to FleetManager (Item 3.1)."""
        return self.fleet_manager.get_fleets_by_faction(faction_name)

    def add_fleet(self, fleet: 'Fleet') -> None:
        """Delegates to FleetManager (Item 3.1)."""
        self.fleet_manager.add_fleet(fleet)

    def remove_fleet(self, fleet: 'Fleet') -> None:
        """Delegates to FleetManager (Item 3.1)."""
        self.fleet_manager.remove_fleet(fleet)

    def update_faction_territory(self, faction_name: str, planet: 'Planet', removal: bool = False) -> None:
        """
        Deprecated. Use GalaxyStateManager.update_planet_ownership instead.
        Kept for compatibility if external modules call it directly.
        """
        # We can't easily map this to update_ownership without knowing context.
        # But if the repo manages the state, we don't need this method to update a local dict.
        pass

    def register_fleet(self, fleet: 'Fleet') -> None:
        """Delegates to FleetManager (Item 3.1)."""
        self.fleet_manager.register_fleet(fleet)

    def unregister_fleet(self, fleet: 'Fleet') -> None:
        """Delegates to FleetManager (Item 3.1)."""
        self.fleet_manager.unregister_fleet(fleet)

    def update_planet_ownership(self, planet: 'Planet', new_owner: str) -> None:
        """Updates planet owner and maintains faction indices."""
        old_owner = planet.owner
        self.asset_manager.update_planet_ownership(planet, new_owner)
        
        # Log to Master Timeline if ownership actually changed
        if old_owner != new_owner:
            # Log first conquest milestone
            if old_owner != "Neutral" and self._milestone_turns['first_conquest'] is None:
                self._log_campaign_milestone(
                    'first_conquest',
                    new_owner,
                    {
                        'planet': planet.name,
                        'previous_owner': old_owner
                    }
                )
            
            if self.report_organizer:
                description = f"{new_owner} conquered {planet.name} from {old_owner}"
                self.report_organizer.log_to_master_timeline(self.turn_counter, "CONQUEST", description)
            
                # Phase 42: Real-time Map Updates
                if self.telemetry:
                    p_data = {
                        "name": planet.name,
                        "system": planet.system.name if planet.system else "Unknown",
                        "owner": new_owner,
                        "status": "Stable" if not getattr(planet, 'is_sieged', False) else "Siege",
                        "is_sieged": getattr(planet, 'is_sieged', False)
                    }
                    # Emit as a LIST for dashboard compatibility
                    self.telemetry.log_event(EventCategory.SYSTEM, "planet_update", {"planets": [p_data]}, turn=self.turn_counter)

            # Check for Major Expansion Milestone ( > 20% Control )
            if new_owner != "Neutral":
                total_planets = len(self.all_planets)
                owned_count = len([p for p in self.all_planets if getattr(p, 'owner', 'Neutral') == new_owner])
                if total_planets > 0 and (owned_count / total_planets) >= 0.20:
                     if self._milestone_turns['major_expansion'] is None: # Only log first time globally? Or first time for faction?
                         # The list tracks global milestones?
                         # The implementation of _log_campaign_milestone tracks milestones in self._milestone_turns which is global.
                         # But let's check if we want it per faction.
                         # For now, "First Major Expansion" is fine as a global 'major_expansion' event.
                         # Or we can pass 'major_expansion' + faction to make unique keys if we modified the dict.
                         # Given current dict, it's global.
                         self._log_campaign_milestone('major_expansion', new_owner, {'planets': owned_count, 'percentage': (owned_count / total_planets)})

    def _is_hostile_target(self, faction: str, target_owner: str) -> bool:
        return self.intel_manager._is_hostile_target(faction, target_owner)

    @functools.lru_cache(maxsize=1024)
    def calculate_threat_level(self, faction: str, planet: 'Planet') -> float:
        """Wrapper for IntelligenceManager."""
        return self.intel_manager.calculate_threat_level(faction, planet)
        
    def _register_lru_caches(self):
         # Helper called after methods are bound? 
         # Python methods are bound at init? No, they are descriptors.
         # We can register them in __init__
         pass

    def get_cached_intel(self, faction: str, planet_name: str, turn: int) -> tuple:
        return self.intel_manager.get_cached_intel(faction, planet_name, turn)

    def find_cached_path(self, start_node, end_node, turn):
        """Cached wrapper for pathfinding to avoid redundant graph traversals."""
        # Delegating to service which handles caching now
        # Phase 23: Include universe_name as context for cache key scoping
        return self.pathfinder.find_cached_path(start_node, end_node, turn, context=self.universe_config.name)

    def calculate_target_score(self, planet_name: str, faction: str, 
                               home_x: float, home_y: float,
                               strat_priority: tuple, strat_targets: tuple, 
                               strat_target_faction: str, strat_phase: str,
                               turn: int) -> float:
        return self.intel_manager.calculate_target_score(planet_name, faction, home_x, home_y, strat_priority, strat_targets, strat_target_faction, strat_phase, turn)

    def load_points_db(self) -> None:
        self.galaxy_generator.load_points_db()
        self.points_db = self.galaxy_generator.points_db

    def load_blueprints(self) -> None:
        self.galaxy_generator.load_blueprints()
        self.unit_blueprints = self.galaxy_generator.unit_blueprints
        self.navy_blueprints = self.galaxy_generator.navy_blueprints
        self.army_blueprints = self.galaxy_generator.army_blueprints
        
        if self.logger:
            for f in self.navy_blueprints:
                self.logger.debug(f"[BLUEPRINTS] {f}: {len(self.navy_blueprints[f])} Ships, {len(self.army_blueprints[f])} Armies loaded.")

    def generate_galaxy(self, num_systems: int = 20, min_planets: int = 1, max_planets: int = 5, base_req: int = 2500) -> None:
        systems, all_planets = self.galaxy_generator.generate_galaxy(
            num_systems=num_systems,
            min_planets=min_planets,
            max_planets=max_planets,
            base_req=base_req
        )
        self.galaxy_manager.set_systems(systems)
        
        # Post-Generation Hooks
        if self.logger:
            self.logger.campaign(f"Galaxy Generation Complete: {len(self.systems)} Systems, {len(self.all_planets)} Planets.")
        
        # Populate Planet Index
        # Delegated to Repository via GalaxyStateManager.set_systems -> PlanetRepository.save
        # self.galaxy_manager.set_systems(systems) calls save(), which updates the index.
        # No action needed here.
            
        if hasattr(self, 'storm_manager') and self.storm_manager:
            self.storm_manager.collect_edges()

        # Telemetry: Emit Universe Generated Event for Dashboard
        if self.telemetry:
            simple_systems = []
            for s in self.systems:
                conns = [n.name for n in s.connections] if hasattr(s, 'connections') else []
                # Use planet count for visualization
                p_count = len(s.planets) if hasattr(s, 'planets') else 0
                
                simple_systems.append({
                    "name": s.name,
                    "x": s.x,
                    "y": s.y,
                    "owner": getattr(s, 'owner', 'Neutral'),
                    "connections": conns,
                    "total_planets": p_count,
                    "total_planets": p_count,
                    "planets": [{"name": p.name, "owner": getattr(p, 'owner', 'Neutral')} for p in s.planets]
                })

            from src.reporting.telemetry import EventCategory
            self.telemetry.log_event(
                EventCategory.SYSTEM, 
                "galaxy_generated", 
                {"systems": simple_systems, "num_systems": len(self.systems)}
            )

    def rebuild_planet_indices(self):
        """Rebuilds the planets_by_faction index. Delegated to Repo."""
        # Forcing a full save/re-index if needed, or just warn.
        # Usually valid unless repo is corrupted.
        pass

    def validate_asset_cache(self) -> None:
        """
        Debug Utility: Verifies that planets_by_faction is in sync with actual planet owners.
        """
        print("[CACHE] Validating Planet Ownership Cache...")
        errors = 0
        
        # 1. Reverse Map: Planet -> Owner
        cache_map = {}
        for f, planets in self.planets_by_faction.items():
            for p in planets:
                if p.name in cache_map:
                    print(f"Error: Planet {p.name} listed under multiple factions: {cache_map[p.name]} and {f}")
                    errors += 1
                cache_map[p.name] = f
                
        # 2. Check Real State
        for p in self.all_planets:
            real_owner = p.owner if hasattr(p, 'owner') else "Neutral"
            cached_owner = cache_map.get(p.name)
            
            if real_owner != cached_owner:
                 # It's possible for Neutral planets to be missing from cache if we lazily init
                 if real_owner == "Neutral" and not cached_owner:
                     continue
                     
                 print(f"Sync Error: {p.name} Real({real_owner}) vs Cache({cached_owner})")
                 errors += 1
                 
        if errors == 0:
            print("[CACHE] Cache Integrity Verified.")
        else:
            print(f"[CACHE] Found {errors} sync errors.")

    def calculate_build_time(self, bp: Any) -> int:
        return self.asset_manager.calculate_build_time(bp)

    def create_fleet(self, faction: str, location: Planet, units: Optional[List[Unit]] = None, fid: Optional[str] = None) -> Fleet:
        fleet = self.asset_manager.create_fleet(faction, location, units, fid)
        if hasattr(fleet, 'register_with_cache_manager'):
            fleet.register_with_cache_manager(self.cache_manager)
        return fleet

    def create_army(self, faction: str, location: Planet, units: Optional[List[Unit]] = None, aid: Optional[str] = None) -> ArmyGroup:
        return self.asset_manager.create_army(faction, location, units, aid)

    def set_fleet_queues(self, incoming_q: Optional[Queue], outgoing_q: Optional[Queue], progress_q: Optional[Queue] = None) -> None:
        """
        Passes queues to FleetQueueManager.
        """
        FleetQueueManager.initialize(incoming_q, outgoing_q, progress_q)

    def process_fleet_queues(self, run_id: int, turn: int) -> None:
        """
        Delegates queue polling to PortalManager.
        """
        self.portal_manager.process_queue_commands(run_id, turn)

    def _handle_fleet_injection(self, cmd: Dict[str, Any]) -> None:
        """
        Delegates fleet injection to PortalManager.
        """
        self.portal_manager.handle_fleet_injection(cmd)

    def spawn_start_fleets(self, num_fleets_per_faction: int = 1) -> None:
        self.galaxy_generator.spawn_start_fleets(self, num_fleets_per_faction)
        
        # Phase 5 Fix: Re-emit Galaxy Snapshot with Ownership
        # The initial galaxy_generated event (pre-spawn) shows everyone as Neutral.
        # We need a new snapshot now that factions have claimed systems.
        if self.telemetry:
            simple_systems = []
            for s in self.systems:
                conns = [n.name for n in s.connections] if hasattr(s, 'connections') else []
                # Use planet count for visualization
                p_count = len(s.planets) if hasattr(s, 'planets') else 0
                
                simple_systems.append({
                    "name": s.name,
                    "x": s.x,
                    "y": s.y,
                    "owner": getattr(s, 'owner', 'Neutral'),
                    "connections": conns,
                    "total_planets": p_count,
                    "total_planets": p_count,
                    "planets": [{"name": p.name, "owner": getattr(p, 'owner', 'Neutral')} for p in s.planets]
                })

            from src.reporting.telemetry import EventCategory
            self.telemetry.log_event(
                EventCategory.SYSTEM, 
                "galaxy_generated", 
                {"systems": simple_systems, "num_systems": len(self.systems), "phase": "post_spawn"}
            )


    def prune_empty_armies(self) -> int:
        count = self.asset_manager.prune_empty_armies()
        if count > 0:
            print(f"  > [CLEANUP] Pruned {count} Ghost Armies (0 units).")
        return count

    def process_turn(self, fast_resolve: bool = False) -> None:
        """Delegates to the new CampaignOrchestrator."""
        if not hasattr(self, 'orchestrator'):
            from src.managers.campaign.orchestrator import CampaignOrchestrator
            self.orchestrator = CampaignOrchestrator(self)
            
        self.orchestrator.process_turn(fast_resolve)

    def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Compatibility bridge for orchestrator events."""
        if hasattr(self, 'telemetry') and self.telemetry:
             from src.reporting.telemetry import EventCategory
             # Map some events to legacy telemetry for dashboard support
             cat = EventCategory.CAMPAIGN
             if "error" in event_type: cat = EventCategory.SYSTEM
             self.telemetry.log_event(cat, event_type, data, turn=self.turn_counter)
        
        # Also publish to the new EventBus
        from src.events.event_bus import EventBus
        EventBus.get_instance().publish(event_type, data, source="CampaignEngine")



    def get_intelligence_report(self, faction_name: str, planet_name: str):
        return self.intel_manager.get_intelligence_report(faction_name, planet_name)

    @profile_method
    def update_faction_visibility(self, f_name: str) -> None:
        self.intel_manager.update_faction_visibility(f_name)

    def choose_ai_target(self, fleet):        # Delegated to Strategy
        strategy = self.strategies.get(fleet.faction, self.default_strategy)
        return strategy.choose_target(fleet, self)

        pass # Redundant, handled by strategy









    def log_battle_result(self, planet_name, winner, losers, rounds, survivor_count, battle_stats=None):
        # Log first battle milestone
        if self._milestone_turns['first_battle'] is None:
            self._log_campaign_milestone(
                'first_battle',
                winner,
                {
                    'planet': planet_name,
                    'losers': losers,
                    'rounds': rounds
                }
            )
        
        if self.report_organizer:
            cat_path = self.report_organizer.get_turn_path(self.turn_counter, "battles")
            log_path = os.path.join(cat_path, "battle_results.csv")
        elif self.battle_log_dir:
            log_path = os.path.join(self.battle_log_dir, "battle_telemetry.csv")
        else:
            log_path = os.path.join(REPORTS_DIR, "battle_telemetry.csv")
        
        if not os.path.exists(log_path):
             with open(log_path, "w", encoding='utf-8') as f:
                 f.write("Turn,Planet,Winner,Losers,Rounds,Survivors\n")
                 
        with open(log_path, "a", encoding='utf-8') as f:
            l_str = ";".join(losers)
            f.write(f"{self.turn_counter},{planet_name},{winner},{l_str},{rounds},{survivor_count}\n")
            
        if winner and winner in self.factions:
            self.factions[winner].stats["turn_battles_fought"] += 1
            self.factions[winner].stats["turn_battles_won"] += 1
            self.factions[winner].stats["battles_fought"] += 1 # Global
            self.factions[winner].stats["battles_won"] += 1 # Global
            
            # [LEARNING] Record Win
            if hasattr(self.factions[winner], 'learning_history'):
                 outcome = {
                     'turn': self.turn_counter,
                     'location': planet_name,
                     'won': True,
                     'opponent': losers[0] if losers else "Unknown",
                     'rounds': rounds
                 }
                 self.factions[winner].learning_history['battle_outcomes'].append(outcome)

        for loser in losers:
            if loser in self.factions:
                self.factions[loser].stats["turn_battles_fought"] += 1
                self.factions[loser].stats["battles_fought"] += 1 # Global
                
                # [LEARNING] Record Loss
                if hasattr(self.factions[loser], 'learning_history'):
                     outcome = {
                         'turn': self.turn_counter,
                         'location': planet_name,
                         'won': False,
                         'opponent': winner,
                         'rounds': rounds
                     }
                     self.factions[loser].learning_history['battle_outcomes'].append(outcome)
                
                # [FIX] Draw Tracking
                if winner == "Draw":
                     if "battles_drawn" not in self.factions[loser].stats:
                         self.factions[loser].stats["battles_drawn"] = 0
                     self.factions[loser].stats["battles_drawn"] += 1

        # Log to Faction Reporter
        if winner == "Draw":
             for loser in losers:
                 draw_msg = f"Inconclusive engagement on {planet_name} (Draw)"
                 self.faction_reporter.log_event(loser, "military", draw_msg, {"planet": planet_name, "rounds": rounds, "result": "Draw"})
        else:
            result_msg = f"Victory on {planet_name} against {', '.join(losers)}"
            self.faction_reporter.log_event(winner, "military", result_msg, {"planet": planet_name, "losers": losers, "rounds": rounds})
            for loser in losers:
                defeat_msg = f"Defeat on {planet_name} by {winner}"
                self.faction_reporter.log_event(loser, "military", defeat_msg, {"planet": planet_name, "winner": winner, "rounds": rounds})

    def export_analytics(self, output_dir, run_id):
        if not self.stats_history: return
        
        # Determine CSV Columns dynamically
        keys = list(self.stats_history[0].keys())
        
        if self.report_organizer:
            # New structured path
            filename = f"economy_run_{run_id}.csv"
            filepath = os.path.join(self.report_organizer.run_path, filename)
            
            # Legacy path for compatibility
            try:
                legacy_filename = f"economy_run_{int(run_id):03d}.csv"
            except:
                legacy_filename = f"economy_run_{run_id}.csv"
            legacy_path = os.path.join(output_dir, legacy_filename)
            
            # Ensure legacy directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.stats_history)
                
            # Copy or write to legacy path
            try:
                import shutil
                shutil.copy2(filepath, legacy_path)
            except:
                with open(legacy_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(self.stats_history)
                    
            print(f"Exported economy stats to structured path: {filepath}")
            print(f"Exported economy stats to legacy path: {legacy_path}")
        else:
            filename = f"economy_run_{run_id:03d}.csv"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.stats_history)
            print(f"Exported economy stats to {filepath}")
        
    def _log_campaign_milestone(self, milestone_type: str, faction: str, context: Dict[str, Any] = None):
        """
        Logs campaign milestone telemetry events. Delegates to Orchestrator.
        """
        if hasattr(self, 'orchestrator'):
            self.orchestrator.log_milestone(milestone_type, self.turn_counter, {'faction': faction, 'context': context})

    
    def _log_victory_condition_progress(self):
        """
        Logs victory condition progress. Delegates to Orchestrator.
        """
        if hasattr(self, 'orchestrator'):
            self.orchestrator.log_victory_progress()
        return None

    def _log_faction_elimination(self, faction_name: str):
        """Logs detailed analysis when a faction is eliminated (Phase 6)."""
        if not self.telemetry:
            return

        f_obj = self.get_faction(faction_name)
        if not f_obj:
            return

        # Collect Decline Timeline (Briefly from stats history if available)
        # For now, we'll just log the final status and contributing factors.
        
        analysis = {
            "faction": faction_name,
            "elimination_turn": self.turn_counter,
            "survival_metrics": {
                "turns_in_game": self.turn_counter,
                "peak_planets": f_obj.stats.get("max_planets", 0),
                "peak_military_power": f_obj.stats.get("max_military_power", 0)
            },
            "contributing_factors": {
                "economic_status": "collapsed" if f_obj.requisition < 0 else "stable",
                "final_military_power": f_obj.military_power,
                "final_planet_count": len(self.planets_by_faction.get(faction_name, []))
            }
        }

        self.telemetry.log_event(
            EventCategory.CAMPAIGN,
            "faction_elimination_analysis",
            analysis,
            turn=self.turn_counter,
            faction=faction_name
        )

    def _log_faction_survival_stats(self):
        """Logs faction survival rates and economic resilience (Metric #14)."""
        if not self.telemetry or self.turn_counter % 10 != 0: return

        factions_data = {}
        active_count = 0
        eliminated_count = 0
        bankrupt_count = 0
        survival_turns_sum = 0
        
        econ = getattr(self, 'economy_manager', None)
        
        for f_name, f in self.factions.items():
            if f_name == "Neutral": continue
            
            is_eliminated = not f.is_alive
            status = "eliminated" if is_eliminated else "active"
            
            # Check bankruptcy
            if status == "active" and f.requisition < -5000:
                 status = "bankrupt"
                 bankrupt_count += 1
            
            if status == "active" or status == "bankrupt": active_count += 1
            elif status == "eliminated": eliminated_count += 1
            
            survival_turns = f.stats.get("turns_survived", self.turn_counter)
            survival_turns_sum += survival_turns
            
            # Recovery stats
            rec_events = 0
            max_debt = 0
            if econ:
                if f_name in getattr(econ, 'cumulative_recovery_impact', {}):
                    rec_events = econ.cumulative_recovery_impact[f_name].get("events", 0)
                if f_name in getattr(econ, 'faction_recovery_state', {}):
                     max_debt = econ.faction_recovery_state[f_name].get("accumulated_debt_max", 0)
                     
            # Volatility
            volatility = 0.0
            if self.telemetry:
                 vol = self.telemetry.calculate_economic_volatility(f_name)
                 volatility = vol.get("combined_volatility", 0.0)
            
            factions_data[f_name] = {
                "status": status,
                "survival_turns": survival_turns,
                "recovery_events_count": rec_events,
                "max_debt_encountered": max_debt,
                "economic_volatility": volatility,
                "elimination_turn": f.stats.get("elimination_turn"),
                "elimination_cause": f.stats.get("elimination_cause")
            }
            
        self.telemetry.log_event(
            EventCategory.CAMPAIGN,
            "faction_survival_rate",
            {
                "factions": factions_data,
                "statistics": {
                    "total_factions": len(self.factions) - 1,
                    "active_factions": active_count,
                    "eliminated_factions": eliminated_count,
                    "bankrupt_factions": bankrupt_count,
                    "average_survival_turns": survival_turns_sum / max(1, (active_count + eliminated_count))
                }
            },
            turn=self.turn_counter
        )
    
    def _log_narrative_event(self, title: str, description: str, participants: list, impact_score: float = 0.5, tags: list = None):
        """Logs a descriptive narrative event (Metric #16/17)."""
        if not self.telemetry: return
        
        self.telemetry.log_event(
            EventCategory.CAMPAIGN,
            "narrative_event",
            {
                "turn": self.turn_counter,
                "event_type": "turning_point",
                "title": title,
                "description": description,
                "participants": participants,
                "impact_score": impact_score,
                "tags": tags or ["turning_point"]
            },
            turn=self.turn_counter
        )

    def detect_narrative_turning_points(self):
        """Analyzes campaign state for dramatic shifts (Metric #17)."""
        if not self.telemetry: return
        
        # 1. Territory Collapse
        for faction in self.get_all_factions():
            if faction.name == "Neutral": continue
            
            history = self._victory_progress_history.get(faction.name, [])
            if len(history) >= 10:
                old_val = history[-10]['planets_controlled']
                new_val = history[-1]['planets_controlled']
                
                if old_val >= 4 and new_val <= old_val / 2:
                    self._log_narrative_event(
                        "Territory Collapse",
                        f"{faction.name} has lost over 50% of its controlled systems in a short span!",
                        [faction.name],
                        impact_score=0.9,
                        tags=["collapse", "war"]
                    )
                    
        # 2. Economic Renaissance (Deep Debt to Surplus)
        # Could be added by checking EconomyManager state history
    
    def check_victory_conditions(self) -> Optional[str]:
        """Delegates to MissionManager for victory checking and logs progress."""
        # Log progress for all factions first
        self._log_victory_condition_progress()
        
        winner = self.mission_manager.check_victory_conditions(self)
        if winner and self.telemetry:
             self.telemetry.log_event(
                 EventCategory.CAMPAIGN,
                 "campaign_ended",
                 {
                     "campaign_id": getattr(self, 'campaign_id', 'unknown'),
                     "winner": winner, 
                     "total_turns": self.turn_counter
                 },
                 turn=self.turn_counter
             )
        return winner

    @profile_method
    def _refresh_spatial_indices(self):
        """Rebuilds spatial lookups for O(1) targeting."""
        # 1. Index Planets (Static - Run once)
        if not self._planets_indexed and self.universe_data:
            self.spatial_index_planets.clear()
            for system in self.universe_data.systems:
                # System coords
                sx, sy = getattr(system, 'x', 0), getattr(system, 'y', 0)
                for p in system.planets:
                    # Planets share system coords roughly
                    self.spatial_index_planets.add(sx, sy, p)
            self._planets_indexed = True

        # 2. Index Fleets (Dynamic - Run every turn)
        self.spatial_index_fleets.clear()
        for f in self.fleets:
            if f.is_destroyed: continue
            
            # Resolve Coords
            node = f.current_node
            if not node:
                 # Try location
                 if hasattr(f.location, 'x'): node = f.location
                 elif hasattr(f.location, 'system'): node = f.location.system
            
            if node and hasattr(node, 'x') and hasattr(node, 'y'):
                self.spatial_index_fleets.add(node.x, node.y, f)

    def run_campaign(self):
        pass # Placeholder for the actual implementation of run_campaign

    def save_campaign(self, filename: str = "autosave") -> bool:
        """Delegates to PersistenceManager."""
        return self.persistence_manager.save_campaign(filename)

    def load_campaign(self, filename: str = "autosave") -> bool:
        """Delegates to PersistenceManager."""
        return self.persistence_manager.load_campaign(filename)

    def load_campaign_from_config(self, config_path: str) -> bool:
        """Delegates to ScenarioManager."""
        return self.scenario_manager.load_campaign_from_config(config_path)

    def apply_starting_conditions(self, conditions: Dict[str, Any]):
        """Delegates to ScenarioManager."""
        self.scenario_manager.apply_starting_conditions(conditions)
        
    def _link_seeded_systems(self, systems):
        """No longer used directly, ScenarioManager handles it."""
        pass

    def register_victory_conditions(self, conditions: List[Dict]):
        """Delegates to MissionManager."""
        self.mission_manager.register_victory_conditions(conditions)

    def load_mission_sequence(self, missions: List[Dict]):
        """Delegates to MissionManager."""
        self.mission_manager.load_mission_sequence(missions)

    def check_mission_objectives(self, turn: int):
        """Delegates to MissionManager."""
        self.mission_manager.check_mission_objectives(turn, self)
        



    def generate_run_summary(self) -> None:
        """
        [REPORTING] Generates a final run-level summary.json.
        """
        if not self.report_organizer: return
        
        # 1. Determine Winner
        winner = "None"
        max_score = -1
        
        # Simple scoring: Planets + Economy
        scores = {}
        for f in self.factions:
            if f == "Neutral": continue
            f_obj = self.factions[f]
            planets = len(self.planets_by_faction.get(f, []))
            score = (planets * 1000) + (f_obj.requisition // 100)
            scores[f] = score
            
            if score > max_score:
                max_score = score
                winner = f
                
        # 2. Compile Stats
        stats = {
            "winner": winner,
            "total_turns": self.turn_counter,
            "final_scores": scores,
            "factions": {}
        }
        
        for f in self.factions:
            if f == "Neutral": continue
            f_obj = self.factions[f]
            stats["factions"][f] = {
                "planets": len(self.planets_by_faction.get(f, [])),
                "requisition": f_obj.requisition,
                "tech_level": len(f_obj.unlocked_techs)
            }
            
        # 3. Write Summary
        summary_path = os.path.join(self.report_organizer.run_path, "summary.json")
        try:
            with open(summary_path, "w") as f:
                json.dump(stats, f, indent=2)
            print(f"[REPORT] Run Summary generated: {summary_path}")
        except Exception as e:
            print(f"[REPORT] Failed to generate summary: {e}")

        # 4. Generate CSV Reports (Economy/Diplomacy)
        if hasattr(self, 'telemetry') and self.telemetry and hasattr(self.telemetry, 'log_file'):
            self.report_organizer.generate_csv_reports(self.telemetry.log_file)

if __name__ == "__main__":
    engine = CampaignEngine()
    engine.generate_galaxy(30)
    engine.spawn_start_fleets()
    for _ in range(10):
        engine.process_turn()
