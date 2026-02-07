import functools
import time
import random
from typing import Dict, Any, Callable, List, Optional
from src.models.fleet import TaskForce, Fleet
from src.reporting.telemetry import EventCategory
from universes.base.personality_template import FactionPersonality
from src.core.config import get_universe_config
import copy
import math

from src.ai.strategies.economic_strategy import EconomicStrategy
from src.ai.strategies.defensive_strategy import DefensiveStrategy
from src.ai.strategies.offensive_strategy import OffensiveStrategy
from src.ai.strategies.interception_strategy import InterceptionStrategy
from src.ai.strategies.exploration_strategy import ExplorationStrategy

from src.utils.profiler import profile_method
from src.ai.strategies.standard import _ai_rng

# FactionPersonality and PERSONALITY_DB moved to universes abstraction layer

from src.ai.strategic_planner import StrategicPlanner, StrategicPlan
from src.ai.adaptation.learning_engine import AdaptiveLearningEngine
from src.ai.economic_engine import EconomicEngine
from src.services.target_scoring_service import TargetScoringService
from src.managers.task_force_manager import TaskForceManager

# Coordinators
from src.ai.coordinators.personality_manager import PersonalityManager
from src.ai.coordinators.intelligence_coordinator import IntelligenceCoordinator
from src.ai.coordinators.tech_doctrine_manager import TechDoctrineManager

from src.core.interfaces import IEngine

class StrategicAI:
    def __init__(self, engine: IEngine):
        self.engine = engine
        self.tf_manager = TaskForceManager(self)
        self.planner = StrategicPlanner(self)
        self.learning_engine = AdaptiveLearningEngine(self)
        self.turn_cache = {} # Cache for current turn data
        
        # Specialists (Phase 121)
        from src.ai.management import StrategyOrchestrator, ProductionPlanner, ExpansionLogic
        self.orchestrator = StrategyOrchestrator(self)
        self.production_planner = ProductionPlanner(self)
        self.expansion_logic = ExpansionLogic(self)

        # Coordinators
        self.personality_manager = PersonalityManager(self.engine)
        self.persistence_loader = None # Deprecated/Wrapped by PersonalityManager
        self.intelligence_coordinator = IntelligenceCoordinator(self.engine, self)
        self.tech_doctrine_manager = TechDoctrineManager(self.engine, self)
        
        # Strategies
        self.economic_strategy = EconomicStrategy(self)
        self.defensive_strategy = DefensiveStrategy(self)
        self.offensive_strategy = OffensiveStrategy(self)
        self.interception_strategy = InterceptionStrategy(self)
        self.exploration_strategy = ExplorationStrategy(self)
        self.hybrid_tech_manager = self.engine.tech_manager
        
        # New Engine (Item 2.1)
        self.economic_engine = EconomicEngine(self)
        self.target_scoring = TargetScoringService(self)
        
        # New Feature: Dynamic Weights
        from src.ai.dynamic_weights import DynamicWeightSystem
        self.dynamic_weights = DynamicWeightSystem()
        
        # New Feature: Opponent Modeling (Phase 3)
        from src.ai.opponent_profiler import OpponentProfiler
        self.opponent_profiler = OpponentProfiler()
        
        # New Feature: Advanced Diplomacy (Phase 7)
        from src.ai.coalition_builder import CoalitionBuilder
        from src.ai.proactive_diplomacy import ProactiveDiplomacy
        self.coalition_builder = CoalitionBuilder(self)
        self.proactive_diplomacy = ProactiveDiplomacy(self)
        
        # New Feature: Deep Strategic AI (Phase 8)
        from src.ai.tactical_ai import TacticalAI
        from src.ai.strategic_memory import StrategicMemory
        from src.ai.composition_optimizer import CompositionOptimizer
        
        self.tactical_ai = TacticalAI(self)
        self.strategic_memory = StrategicMemory()
        self.composition_optimizer = CompositionOptimizer(self)
        
        # New Feature: Posture System V3
        from src.ai.posture_system import PostureManager
        self.posture_manager = PostureManager(self)
        
        # Telemetry: Alliance Stats
        self.alliance_stats = {} # {alliance_id: {shared_intel: 0, coordinated_attacks: 0}}
        
    def _log_strategic_decision(self, faction: str, decision_type: str, decision: str, reason: str, context: dict, expected_outcome: str):
        """Logs strategic decision telemetry."""
        if not self.engine.telemetry: return
        
        self.engine.telemetry.log_event(
            EventCategory.STRATEGY,
            "strategic_decision",
            {
                "faction": faction,
                "turn": self.engine.turn_counter,
                "decision_type": decision_type,
                "decision": decision,
                "reason": reason,
                "context": context,
                "expected_outcome": expected_outcome,
                "confidence": 0.8 # Placeholder or derived
            },
            turn=self.engine.turn_counter,
            faction=faction
        )

    def _log_plan_execution(self, faction: str, plan_id: str, plan_type: str, status: str, objectives: list, outcome: dict = None):
        """Logs strategic plan execution telemetry (Metric #10/11)."""
        if not self.engine.telemetry: return
        
        self.engine.telemetry.log_event(
            EventCategory.STRATEGY,
            "strategic_plan_execution",
            {
                "faction": faction,
                "plan_id": plan_id,
                "plan_type": plan_type,
                "turn": self.engine.turn_counter,
                "status": status,
                "objectives": objectives, # Simple list or summary
                "outcome": outcome
            },
            turn=self.engine.turn_counter,
            faction=faction
        )
        
    @property
    def task_forces(self):
        return self.tf_manager.task_forces

    @property
    def tf_counter(self):
        return self.tf_manager.tf_counter

    @tf_counter.setter
    def tf_counter(self, value):
        self.tf_manager.tf_counter = value
        
    def load_personalities(self, universe_name: Optional[str] = "void_reckoning"):
        """Loads personality module for the specified universe."""
        self.personality_manager.load_personalities(universe_name)

    def process_turn(self):
        """Delegated to StrategyOrchestrator."""
        self.orchestrator.process_turn()


                
    def evaluate_espionage_targets(self, faction_name: str):
        """Delegated to IntelligenceCoordinator."""
        self.intelligence_coordinator.evaluate_espionage_targets(faction_name)
                  
    def process_innovation_cycle(self, faction_name: str):
        """Delegated to ProductionPlanner."""
        self.production_planner.process_innovation_cycle(faction_name)

    def update_ship_designs(self, faction_name: str):
        """Delegated to AdaptiveLearningEngine."""
        self.learning_engine.update_performance_metrics(faction_name)

    def adapt_personality(self, faction: str, personality: FactionPersonality) -> FactionPersonality:
        """Delegated to AdaptiveLearningEngine."""
        return self.learning_engine.adapt_personality(faction, personality)

    def export_learning_report(self, faction: str, output_dir: str):
        """Delegated to AdaptiveLearningEngine."""
        self.learning_engine.export_learning_report(faction, output_dir)

    def build_turn_cache(self, force: bool = False):
        """Pre-calculates expensive lookups for the turn. (Optimized R5)"""
        current_turn = self.engine.turn_counter
        # Avoid redundant rebuilds in same turn
        if not force and getattr(self, '_last_cache_turn', -1) == current_turn:
            return

        self.turn_cache = {
            "fleets_by_loc": {},
            "threats_by_faction": {},
            "visibility_by_faction": {},
            "threat_levels": {},
            "defense_zones": {}, # Populated lazily
            "exploration_frontiers": {}, # Populated lazily
            "mandates": {},
            "theater_power_cache": {} # R6: Power Index
        }
        
        # Cache Fleets by Location
        for f in self.engine.fleets:
            if getattr(f, 'is_destroyed', False): continue
            loc = getattr(f, 'location', None)
            if loc:
                loc_id = id(loc)
                if loc_id not in self.turn_cache["fleets_by_loc"]:
                    self.turn_cache["fleets_by_loc"][loc_id] = []
                self.turn_cache["fleets_by_loc"][loc_id].append(f)
                
            # Cache Incoming Threats
            dest = getattr(f, 'destination', None)
            if dest and hasattr(dest, 'owner'):
                target_owner = dest.owner
                if target_owner not in self.turn_cache["threats_by_faction"]:
                     self.turn_cache["threats_by_faction"][target_owner] = []
                self.turn_cache["threats_by_faction"][target_owner].append(f)
        
        self._last_cache_turn = current_turn

    def invalidate_turn_cache(self):
        """Explicitly invalidates current turn cache."""
        self._last_cache_turn = -1
        self.turn_cache.clear()

    def invalidate_faction_cache(self, faction: str):
        """Invalidates faction-specific lazy entries."""
        if faction in self.turn_cache.get("defense_zones", {}):
            del self.turn_cache["defense_zones"][faction]
        if faction in self.turn_cache.get("exploration_frontiers", {}):
            del self.turn_cache["exploration_frontiers"][faction]

    def clear_turn_cache(self):
        """Clear turn cache and LRU caches."""
        self.turn_cache.clear()
        self.target_scoring.clear_caches()

    @profile_method
    def process_adaptation_requests(self, faction_obj, turn_num):
        """Delegated to TechDoctrineManager."""
        self.tech_doctrine_manager.process_adaptation_requests(faction_obj, turn_num)

    def process_standard_research(self, faction: str, f_mgr: Any):
        """
        [Standard Research] Delegated to EconomicEngine for RP-based queuing.
        Legacy instant-buy logic removed (Batch 13).
        """
        # Redirect to new engine logic
        if hasattr(self, 'economic_engine'):
             self.economic_engine.evaluate_research_priorities(faction)

    def process_intel_driven_research(self, faction_obj, turn_num):
        """Delegated to TechDoctrineManager."""
        self.tech_doctrine_manager.process_intel_driven_research(faction_obj, turn_num)

    def evaluate_hybrid_tech_value(self, faction_obj, tech_id):
        """Delegated to TechDoctrineManager."""
        return self.tech_doctrine_manager.evaluate_hybrid_tech_value(faction_obj, tech_id)

    def filter_tech_by_doctrine(self, faction_obj, tech_id, acquisition_type="research"):
        """Delegated to TechDoctrineManager."""
        return self.tech_doctrine_manager.filter_tech_by_doctrine(faction_obj, tech_id, acquisition_type)

    def apply_doctrine_effects(self, faction_obj, effect_type, tech_id):
        """Delegated to TechDoctrineManager."""
        self.tech_doctrine_manager.apply_doctrine_effects(faction_obj, effect_type, tech_id)

    def request_adaptation(self, faction_obj, tech_id):
        """Delegated to TechDoctrineManager."""
        return self.tech_doctrine_manager.request_adaptation(faction_obj, tech_id)

    def process_espionage_decisions(self, faction_obj):
        """Delegated to IntelligenceCoordinator."""
        self.intelligence_coordinator.process_espionage_decisions(faction_obj)

    def calculate_expansion_target_score(self, planet_name: str, faction: str, 
                                        home_x: float, home_y: float, 
                                        personality_name: str, econ_state: str, turn: int,
                                        weights: Dict[str, float] = None) -> float:
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.calculate_expansion_target_score(
            planet_name, faction, home_x, home_y, personality_name, econ_state, turn, weights=weights
        )

    def is_valid_target(self, faction: str, target_faction: str) -> bool:
        """Delegated to IntelligenceCoordinator."""
        return self.intelligence_coordinator.is_valid_target(faction, target_faction)

    def should_betray(self, faction: str, target_faction: str, personality: FactionPersonality) -> bool:
        """Delegated to IntelligenceCoordinator."""
        return self.intelligence_coordinator.should_betray(faction, target_faction, personality)

    def get_diplomatic_stance(self, faction: str, target_faction: str) -> str:
        """Delegated to IntelligenceCoordinator."""
        return self.intelligence_coordinator.get_diplomatic_stance(faction, target_faction)
        
    def get_faction_personality(self, faction: str) -> FactionPersonality:
        """Helper to get current personality (learned or DB)."""
        return self.personality_manager.get_faction_personality(faction)

    def get_cached_defense_zone(self, faction: str, planet_name: str):
        if faction not in self.turn_cache["defense_zones"]:
            self.turn_cache["defense_zones"][faction] = self.classify_defense_zones(faction)
        return self.turn_cache["defense_zones"][faction].get(planet_name, "CORE")
                
    def get_cached_theater_power(self, location, requesting_faction):
        """Optimized version of get_theater_power using cache. Respects Fog of War. (R6)"""
        # 0. Visibility Check (Fog of War)
        f_mgr = self.engine.factions.get(requesting_faction)
        if f_mgr and hasattr(location, 'name') and location.name not in getattr(f_mgr, 'visible_planets', set()):
             return {}

        loc_id = id(location)
        
        # 1. R6: Use Theater Power Cache (Index)
        if loc_id not in self.turn_cache["theater_power_cache"]:
            powers = {}
            # Fleets from Location Cache
            fleets_here = self.turn_cache["fleets_by_loc"].get(loc_id, [])
            for f in fleets_here:
                powers[f.faction] = powers.get(f.faction, 0) + f.power
                
            # Armies
            if hasattr(location, 'armies'):
                for ag in location.armies:
                    if not ag.is_destroyed:
                        powers[ag.faction] = powers.get(ag.faction, 0) + ag.power
                        
            # Base Defense
            if hasattr(location, 'defense_level') and location.owner != "Neutral":
                 powers[location.owner] = powers.get(location.owner, 0) + (location.defense_level * 500)
            
            self.turn_cache["theater_power_cache"][loc_id] = powers
             
        return self.turn_cache["theater_power_cache"][loc_id]

    def get_task_force_for_fleet(self, fleet):
        """Finds the TaskForce containing the given fleet."""
        return self.tf_manager.get_task_force_for_fleet(fleet)

    def assess_economic_health(self, faction: str):
        """Delegates to EconomicEngine (Item 2.1)."""
        return self.economic_engine.assess_economic_health(faction)
    
    def calculate_fleet_upkeep(self, fleet):
        """Delegates to EconomicEngine (Item 2.2)."""
        return self.economic_engine.calculate_fleet_upkeep(fleet)

    def classify_defense_zones(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.classify_defense_zones(faction)

    def get_cached_exploration_frontier(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.get_cached_exploration_frontier(faction)

    def calculate_exploration_frontier(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.calculate_exploration_frontier(faction)

    def _process_sieges(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic._process_sieges(faction)

    def evaluate_offensive_targets(self, faction: str, candidates: List[Any]) -> List[Any]:
        """Delegated to StrategyOrchestrator."""
        return self.orchestrator.evaluate_offensive_targets(faction, candidates)

    def select_scout_target(self, faction: str, f_mgr):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.select_scout_target(faction, f_mgr)

    def predict_enemy_threats(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.predict_enemy_threats(faction)

    # --- Phase 105: Strategic & Tactical Methods ---
    def calculate_dynamic_retreat_threshold(self, fleet, location, personality: FactionPersonality, strategic_plan: StrategicPlan) -> float:
        """Calculates retreat threshold based on strategic importance."""
        return self.target_scoring.calculate_dynamic_retreat_threshold(fleet, location, personality, strategic_plan)

    def initiate_staged_withdrawal(self, task_force: TaskForce, current_location, personality: FactionPersonality):
        """Sets up a withdrawal plan for a task force."""
        return self.tf_manager.initiate_staged_withdrawal(task_force, current_location, personality)
             
    def evaluate_strategic_posture(self, faction_name: str, personality: FactionPersonality, plan: StrategicPlan):
        """Check if we need to switch strategies using the new PostureManager."""
        return self.posture_manager.update_faction_posture(faction_name)

    def switch_strategy(self, faction_name: str, new_posture: str, personality: FactionPersonality):
        """Legacy wrapper for backward compatibility."""
        return self.target_scoring.switch_strategy(faction_name, new_posture, personality)

    def execute_fighting_retreat(self, task_force: TaskForce):
        """Manages the rearguard action while the rest of the task force withdraws."""
        return self.tf_manager.execute_fighting_retreat(task_force)

    def process_faction_strategy(self, faction: str):
        """Delegated to StrategyOrchestrator."""
        return self.orchestrator.process_faction_strategy(faction)

    def _initialize_strategy_context(self, faction: str, f_mgr: Any) -> Any:
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._initialize_strategy_context(faction, f_mgr)

    def _determine_strategic_context(self, faction: str, f_mgr: Any, econ_state: str) -> str:
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._determine_strategic_context(faction, f_mgr, econ_state)

    def _update_operational_plan(self, faction: str, f_mgr: Any, personality: FactionPersonality):
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._update_operational_plan(faction, f_mgr, personality)

    def _execute_strategy_pipeline(self, faction: str, f_mgr: Any, personality: Any, strategic_plan: Any, owned_planets: list, weights: dict):
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._execute_strategy_pipeline(faction, f_mgr, personality, strategic_plan, owned_planets, weights)

    def _handle_expansion_logic(self, faction: str, f_mgr: Any, available_fleets: list, personality: Any, econ_state: str, owned_planets: list, expansion_bias: float, weights: dict):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.handle_expansion_logic(faction, f_mgr, available_fleets, personality, econ_state, owned_planets, expansion_bias, weights)

    def _manage_task_forces(self, faction: str):
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._manage_task_forces(faction)

    def _get_idle_fleets(self, faction: str) -> List[Fleet]:
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._get_idle_fleets(faction)

    def _get_available_fleets(self, faction: str, idle_fleets: List[Fleet]) -> List[Fleet]:
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._get_available_fleets(faction, idle_fleets)

    def _handle_post_strategy_ops(self, faction: str, available_fleets: List[Fleet], f_mgr: Any, personality: FactionPersonality, econ_health: dict, strategic_plan: Any):
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._handle_post_strategy_ops(faction, available_fleets, f_mgr, personality, econ_health, strategic_plan)

    def concentrate_forces(self, faction: str):
        """Delegates to TaskForceManager."""
        return self.tf_manager.concentrate_forces(faction)

    def check_target_failures(self, faction: str):
        """Delegates to StrategicPlanner."""
        return self.planner.check_target_failures(faction)

    def share_intelligence_with_allies(self, faction: str):
        """Delegated to StrategyOrchestrator."""
        return self.orchestrator.share_intelligence_with_allies(faction)

    def log_alliance_stats(self):
        """Delegated to StrategyOrchestrator."""
        return self.orchestrator.log_alliance_stats()

    def _log_strategic_deployment(self, faction: str):
        """Internal delegation to StrategyOrchestrator."""
        return self.orchestrator._log_strategic_deployment(faction)

    def check_for_treaty_and_coalition_obligations(self, faction: str):
        """Delegated to StrategyOrchestrator."""
        return self.orchestrator.check_for_treaty_and_coalition_obligations(faction)

    def _process_sieges(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic._process_sieges(faction)

    def get_cached_exploration_frontier(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.get_cached_exploration_frontier(faction)

    def classify_defense_zones(self, faction: str):
        """Delegated to ExpansionLogic."""
        return self.expansion_logic.classify_defense_zones(faction)

