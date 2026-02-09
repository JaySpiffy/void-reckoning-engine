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
from src.reporting.decision_logger import DecisionLogger

class StrategicAI:
    def __init__(self, engine: IEngine):
        self.engine = engine
        self.tf_manager = TaskForceManager(self)
        self.planner = StrategicPlanner(self)
        self.learning_engine = AdaptiveLearningEngine(self)
        self.turn_cache = {} # Cache for current turn data
        
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
        # New Engine (Item 2.1)
        self.economic_engine = EconomicEngine(self)
        self.target_scoring = TargetScoringService(self)
        self.decision_logger = DecisionLogger(engine=self.engine)
        
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
        
    def __getstate__(self):
        """Prepares StrategicAI for pickling."""
        state = self.__dict__.copy()
        if 'engine' in state: del state['engine']
        if 'decision_logger' in state: del state['decision_logger']
        
        # Stateless Coordinators/Strategies that contain unpicklable refs (modules/locks)
        # We exclude them and re-init them on load
        if 'intelligence_coordinator' in state: del state['intelligence_coordinator']
        if 'tech_doctrine_manager' in state: del state['tech_doctrine_manager']
        if 'economic_strategy' in state: del state['economic_strategy']
        if 'defensive_strategy' in state: del state['defensive_strategy']
        if 'offensive_strategy' in state: del state['offensive_strategy']
        if 'interception_strategy' in state: del state['interception_strategy']
        if 'exploration_strategy' in state: del state['exploration_strategy']
        
        # Phase 7/8 components
        if 'coalition_builder' in state: del state['coalition_builder']
        if 'proactive_diplomacy' in state: del state['proactive_diplomacy']
        if 'tactical_ai' in state: del state['tactical_ai']
        
        # Prune deep caches that hold engine/fleet refs
        if 'turn_cache' in state: del state['turn_cache']
        if '_last_cache_turn' in state: del state['_last_cache_turn']
        
        return state

    def __setstate__(self, state):
        """Restores StrategicAI from pickle."""
        self.__dict__.update(state)
        # Engine will be re-injected by SnapshotManager
        self.decision_logger = None 
        # Stateless components will be re-inited by reinit_stateless_components called by SnapshotManager
        self.intelligence_coordinator = None
        self.tech_doctrine_manager = None
        
        self.economic_strategy = None
        self.defensive_strategy = None
        self.offensive_strategy = None
        self.interception_strategy = None
        self.exploration_strategy = None
        
        self.coalition_builder = None
        self.proactive_diplomacy = None
        self.tactical_ai = None
        
        # Re-init caches
        self.turn_cache = {}
        self._last_cache_turn = -1

    def reinit_stateless_components(self):
        """Re-initializes stateless components after snapshot restore."""
        # Restore engine refs in stateful managers
        if self.tf_manager:
            self.tf_manager.engine = self.engine
            self.tf_manager.ai_manager = self
            
        if self.planner:
            self.planner.ai = self
            if self.planner.theater_manager:
                self.planner.theater_manager.context = self.engine

        if self.personality_manager:
            self.personality_manager.engine = self.engine
            # Reload personalities if loader is missing (it was excluded)
            from src.core.config import ACTIVE_UNIVERSE
            self.personality_manager.load_personalities(ACTIVE_UNIVERSE or "void_reckoning")

        if self.target_scoring:
            self.target_scoring.engine = self.engine
            self.target_scoring.ai_manager = self
            
        if self.economic_engine:
            self.economic_engine.engine = self.engine
            self.economic_engine.ai = self
            
        if self.composition_optimizer:
            self.composition_optimizer.engine = self.engine
            self.composition_optimizer.ai = self

        # Coordinators
        self.intelligence_coordinator = IntelligenceCoordinator(self.engine, self)
        self.tech_doctrine_manager = TechDoctrineManager(self.engine, self)
        
        # Strategies
        self.economic_strategy = EconomicStrategy(self)
        self.defensive_strategy = DefensiveStrategy(self)
        self.offensive_strategy = OffensiveStrategy(self)
        self.interception_strategy = InterceptionStrategy(self)
        self.exploration_strategy = ExplorationStrategy(self)
        
        # Advanced Features
        from src.ai.coalition_builder import CoalitionBuilder
        from src.ai.proactive_diplomacy import ProactiveDiplomacy
        from src.ai.tactical_ai import TacticalAI
        
        self.coalition_builder = CoalitionBuilder(self)
        self.proactive_diplomacy = ProactiveDiplomacy(self)
        self.tactical_ai = TacticalAI(self)
        
    def _log_strategic_decision(self, faction: str, decision_type: str, decision: str, reason: str, context: dict, expected_outcome: str):
        """Logs strategic decision telemetry."""
        if not self.engine or not self.engine.telemetry: return
        
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
        # Ensure personalities are loaded (Comment 2)
        if not self.personality_manager.personality_loader:
            from src.core.config import ACTIVE_UNIVERSE
            self.personality_manager.load_personalities(ACTIVE_UNIVERSE or "void_reckoning")

        # 1. Performance Optimization: Build Turn Cache
        self.build_turn_cache()
        
        for faction in sorted(list(self.engine.factions.keys())):
            if faction == "Neutral": continue
            
            # NEW: Learning Integration
            self.learning_engine.update_performance_metrics(faction)
            
            # Phase 108: Process Hybrid Tech Adaptations
            f_obj = self.engine.factions[faction]
            self.tech_doctrine_manager.process_adaptation_requests(f_obj, self.engine.turn_counter)
            
            self.process_faction_strategy(faction)
            
            # INTEGRATION: Check obligations
            # self.check_for_treaty_and_coalition_obligations(faction) # Moved to inside process_faction_strategy or distinct step?
            # It's better as a distinct step that might OVERRIDE strategy or ADD to it.
            # Let's keep it here.
            
            
            # Phase 7: Intelligence Espionage Theft
            self.engine.intelligence_manager.update_spy_networks(faction) # NEW: Passive Growth
            self.intelligence_coordinator.process_espionage_decisions(f_obj)
            
            # Phase 7: Proactive Diplomacy & Coalitions
            self.proactive_diplomacy.process_turn(faction)
            self.coalition_builder.process_turn(faction)
            
            # INTEGRATION: Check obligations
            self.check_for_treaty_and_coalition_obligations(faction)
            
            # Phase: Innovation (Ship/Weapon Evolution)
            # Cycle runs every 25 turns or if faction is wealthy/advanced
            if self.engine.turn_counter % 25 == 0 or (f_obj.requisition > 100000 and len(f_obj.unlocked_techs) > 20):
                self.process_innovation_cycle(faction)
                
            # Phase 8: Composition Optimization (Adaptive Counters)
            # Run every 10 turns to adjust production
            if self.engine.turn_counter % 10 == 0:
                 # Find primary enemy (threat)
                 threats = self.predict_enemy_threats(faction)
                 if threats:
                      primary_threat_faction = threats[0]["fleet"].faction
                      profile = self.composition_optimizer.analyze_enemy_composition(primary_threat_faction)
                      doctrine = self.composition_optimizer.recommend_counter_doctrine(profile)
                      self.composition_optimizer.adjust_production_priorities(faction, doctrine)
            
        # NEW: Intelligence sharing phase
        for faction in list(self.engine.factions.keys()):
            if faction == "Neutral": continue
            self.share_intelligence_with_allies(faction)
            
            # Feature: Research & Espionage Logic
            self.economic_engine.evaluate_research_priorities(faction)
            self.intelligence_coordinator.evaluate_espionage_targets(faction)
            
            # Filter hybrid tech by doctrine
            # Filter hybrid tech by doctrine
            self.tech_doctrine_manager.process_intel_driven_research(self.engine.factions[faction], self.engine.turn_counter)


                
    def evaluate_espionage_targets(self, faction_name: str):
        """Delegated to IntelligenceCoordinator."""
        self.intelligence_coordinator.evaluate_espionage_targets(faction_name)
                  
    def process_innovation_cycle(self, faction_name: str):
        """
        Periodically triggers technological innovation for a faction.
        Can result in a Hull Mutation or a Weapon Paradigm Shift.
        """
        import os
        import json
        from src.core.config import UNIVERSE_ROOT
        f_obj = self.engine.factions.get(faction_name)
        if not f_obj: return
        
        # 1. Determine Innovation Type
        # 70% Hull Mutation, 30% Weapon Invention
        import random
        innovation_roll = random.random()
        
        dna = self.personality_manager.get_faction_dna(faction_name)
        
        if innovation_roll < 0.70:
            # --- HULL MUTATION ---
            from src.factories.hull_mutation_factory import HullMutationFactory
            mutator = HullMutationFactory()
            
            # Select a random base hull that this faction is using
            hulls_path = os.path.join(UNIVERSE_ROOT, "base", "units", "base_ship_hulls.json")
            if os.path.exists(hulls_path):
                with open(hulls_path, 'r', encoding='utf-8') as f:
                    hulls = json.load(f)
                
                base_id = random.choice(list(hulls.keys()))
                base_hull = hulls[base_id]
                
                mutated = mutator.mutate_hull(faction_name, base_id, base_hull, dna)
                
                # Register the new hull locally in base hulls (so design factory can find it)
                # But we should really just inject it into the ship designer call.
                # For now, we'll store it in the faction's custom hulls list if we add one.
                if not hasattr(f_obj, 'custom_hulls'): f_obj.custom_hulls = {}
                f_obj.custom_hulls[mutated["id"]] = mutated
                
                if self.engine.logger:
                    self.engine.logger.campaign(f"[INNOVATION] {faction_name} evolved a new ship hull: {mutated['name']}!")
        
        else:
            # --- WEAPON INVENTION ---
            # Create a "Paradigm Shift" base blueprint
            paradigms = [
                {"id": "singularity_projector", "name": "Singularity Projector", "dna": "atom_mass", "prefixes": ["Gravitic", "Collapse", "Event-Horizon"]},
                {"id": "chrono_beam", "name": "Chrono-Beam", "dna": "atom_information", "prefixes": ["Timeless", "Recursive", "Delayed"]},
                {"id": "aether_lance", "name": "Aether Lance", "dna": "atom_aether", "prefixes": ["Spirit", "Ghost", "Hallowed"]},
                {"id": "bio_electric_ray", "name": "Bio-Electric Ray", "dna": "atom_volatility", "prefixes": ["Synaptic", "Viral", "Neural"]}
            ]
            
            paradigm = random.choice(paradigms)
            
            from src.factories.weapon_factory import ProceduralWeaponFactory
            # Get existing factory or create a new one for this event
            base_bp_path = os.path.join(UNIVERSE_ROOT, "base", "weapons", "base_weapon_blueprints.json")
            if os.path.exists(base_bp_path):
                with open(base_bp_path, 'r', encoding='utf-8') as f:
                    blueprints = json.load(f)
                
                factory = ProceduralWeaponFactory(blueprints)
                
                # Define the base data for the new paradigm
                new_base = {
                    "name": paradigm["name"],
                    "category": "Experimental",
                    "elemental_signature": {paradigm["dna"]: 50.0},
                    "power_multiplier": 1.5,
                    "cost": 500
                }
                
                factory.inject_paradigm(paradigm["id"], new_base)
                
                # Generate a set of unique weapons using this paradigm
                new_arsenal = factory.generate_arsenal(faction_name, dna, count=3, custom_prefixes=paradigm["prefixes"])
                
                # Merge into faction's weapon registry
                f_obj.weapon_registry.update(new_arsenal)
                
                if self.engine.logger:
                    self.engine.logger.campaign(f"[INNOVATION] {faction_name} invented a new weapon paradigm: {paradigm['name']}!")

        # Always trigger a design refresh after innovation
        self.update_ship_designs(faction_name)

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

    @profile_method
    def calculate_expansion_target_score(self, planet_name: str, faction: str, 
                                        home_x: float, home_y: float, 
                                        personality_name: str, econ_state: str, turn: int,
                                        weights: Dict[str, float] = None,
                                        include_rationale: bool = False) -> Any:
        """Cached expansion target scoring with intelligence integration."""
        mandates = self.turn_cache.get('mandates', {}).get(faction, {})
        
        return self.target_scoring.calculate_expansion_target_score(
            planet_name, faction, home_x, home_y, personality_name, econ_state, turn, 
            mandates=mandates, weights=weights, include_rationale=include_rationale
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

    @profile_method
    def classify_defense_zones(self, faction: str):
        """
        Classifies owned planets into Capital Zone, Border Zone, and Core Zone.
        Returns a dict: {planet_name: zone_type}
        """
        zones = {}
        owned = self.engine.planets_by_faction.get(faction, [])
        if not owned: return zones
        
        # 1. Identify Capital
        capital = next((p for p in owned if "Capital" in [n.type for n in p.provinces]), owned[0])
        
        # 2. Identify Borders (Planets with connections to non-owned systems)
        for p in owned:
            is_border = False
            if hasattr(p, 'system') and p.system.connections:
                for neighbor_sys in p.system.connections:
                    # If any planet in neighbor system is NOT owned by us, it's a border
                    # Simplified: Just check if we own all planets there? 
                    # Or simpler: Is neighbor system fully owned?
                    # Let's assume if we don't own the system, it's external.
                    # Actually, borders are planets connected to systems where we don't have total control?
                    # Let's define Border: Connected to a system containing Enemy or Neutral worlds.
                    external_threat = False
                    for np in neighbor_sys.planets:
                        if np.owner != faction:
                            external_threat = True
                            break
                    if external_threat:
                        is_border = True
                        break
            
            if p == capital:
                zones[p.name] = "CAPITAL"
            elif is_border:
                zones[p.name] = "BORDER"
            else:
                zones[p.name] = "CORE"
                
        # Upgrade neighbors of Capital to Capital Zone for buffer
        if hasattr(capital, 'system') and capital.system.connections:
            for neighbor_sys in capital.system.connections:
                for np in neighbor_sys.planets:
                    if np.owner == faction and zones.get(np.name) != "CAPITAL":
                        zones[np.name] = "CAPITAL_ZONE"
                        
        return zones

    def get_cached_exploration_frontier(self, faction: str):
        if faction not in self.turn_cache["exploration_frontiers"]:
            self.turn_cache["exploration_frontiers"][faction] = self.calculate_exploration_frontier(faction)
        return self.turn_cache["exploration_frontiers"][faction]

    @profile_method
    def calculate_exploration_frontier(self, faction: str):
        """
        Identifies and prioritizes systems for exploration.
        Updates faction.exploration_frontier priority queue.
        """
        f_mgr = self.engine.factions[faction]
        owned_planets = self.engine.planets_by_faction.get(faction, [])
        if not owned_planets: return
        
        # Only update periodically (every 5 turns) or if frontier is empty
        if f_mgr.exploration_frontier and (self.engine.turn_counter - f_mgr.last_exploration_update < 5):
            return

        f_mgr.exploration_frontier = []
        
        # Candidate generation: Neighbors of owned/connected systems
        candidates = set()
        
        for p in owned_planets:
            if hasattr(p.system, 'connections'):
                for neighbor in p.system.connections:
                    if neighbor.name not in f_mgr.explored_systems:
                        candidates.add(neighbor)
                        
        personality = self.get_faction_personality(faction)
        
        for sys in candidates:
            # Diplomatic Filter
            if self.engine.diplomacy:
                has_invalid_ally = False
                coordinating = False
                if f_mgr.active_strategic_plan and f_mgr.active_strategic_plan.diplomatic_goal == "COORDINATE_WITH_ALLY":
                    coordinating = True
                    
                for p in sys.planets:
                     if p.owner != "Neutral" and p.owner != faction:
                         # It's an inhabited system
                         if not self.is_valid_target(faction, p.owner):
                             # It's an ally/friend
                             # If coordinating, we might scout it? Or skip?
                             # Usually we don't scout allies unless we are looking for them?
                             # Prompt says: "exclude allied systems if not coordinating"
                             if not coordinating:
                                 has_invalid_ally = True
                                 break
                                 
                if has_invalid_ally: continue

            # Score Calculation
            score = 0
            
            # 1. Distance from nearest owned planet
            min_dist = 9999
            for p in owned_planets:
                d = ((p.system.x - sys.x)**2 + (p.system.y - sys.y)**2)**0.5
                if d < min_dist: min_dist = d
            
            # Closer is better (higher score)
            score += max(0, 100 - min_dist)
            
            # 2. Strategic Chokepoint Potential
            connections = len(sys.connections)
            if connections <= 2: score += 20 # Chokepoint
            if connections >= 5: score += 10 # Hub
            
            # 3. Personality Bias
            if personality.aggression > 1.2:
                # Aggressive factions prioritize potential conflict (if any info known or just spread out)
                score += 5
            
            # Store in frontier: (Score, System)
            f_mgr.exploration_frontier.append((score, sys))
            
        # Sort by score (descending)
        f_mgr.exploration_frontier.sort(key=lambda x: x[0], reverse=True)
        # Sort by score (descending)
        f_mgr.exploration_frontier.sort(key=lambda x: x[0], reverse=True)
        f_mgr.last_exploration_update = self.engine.turn_counter

    def check_for_treaty_and_coalition_obligations(self, faction: str):
        """
        [INTEGRATION] Checks active treaties (Defensive Pacts) and Coalition memberships.
        If an ally is under attack, generates a DEFEND strategy override or support fleet.
        """
        if not self.engine.diplomacy: return
        
        diplomacy = self.engine.diplomacy
        treaty_mgr = diplomacy.treaty_coordinator
        
        # 1. Check Defensive Pacts
        # Who are we protecting?
        allies = []
        for other, treaty in treaty_mgr.active_treaties.get(faction, {}).items():
            if treaty == "Defensive Pact":
                allies.append(other)
                
        # Are any allies at war?
        for ally in allies:
             # Find wars involving ally where they are DEFENDER
             # We check diplomacy.active_wars
             for (attacker, defender), start_turn in diplomacy.active_wars.items():
                 if defender == ally:
                     # Our ally is being attacked!
                     # 1. Are we already at war with attacker? (If not, we should trigger war or at least defensive mobilization)
                     # For now, simplistic: Create a Defense plan centered on Ally's high value worlds?
                     # Or just log it.
                     pass

    def evaluate_offensive_targets(self, faction: str, candidates: List[Any]) -> List[Any]:
        """
        [INTEGRATION] Filters offensive targets based on diplomatic status.
        Rejects NAPs and Allies unless personality allows betrayal.
        """
        filtered = []
        diplomacy = getattr(self.engine, 'diplomacy', None)
        
        personality = self.get_faction_personality(faction)
        betrayal_threshold = 0.8 # Only treacherous factions betray NAPs
        
        for target in candidates:
             # Target owner?
             owner = target.owner
             if owner == "Neutral" or owner == faction: 
                 filtered.append(target)
                 continue
                 
             if diplomacy:
                 treaty = diplomacy.treaty_coordinator.get_treaty(faction, owner)
                 if treaty in ["Non-Aggression Pact", "Defensive Pact", "Alliance"]:
                     if personality.honor > betrayal_threshold: 
                         continue # Honor prevents attack
                     if personality.aggression < 0.9:
                         continue # Not aggressive enough to break treaty
                         
             filtered.append(target)
             
        return filtered

        # Return only the planet names for the exploration strategy (flatten systems into planets)
        frontier_planet_names = set()
        for _, sys in f_mgr.exploration_frontier:
            for p in sys.planets:
                # Use simple set for visible planets comparison
                if p.name not in getattr(f_mgr, 'visible_planets', set()):
                    frontier_planet_names.add(p.name)
                    
        return frontier_planet_names

    def select_scout_target(self, faction: str, f_mgr):
        """
        Selects the next best target for a scout fleet from the frontier.
        """
        self.get_cached_exploration_frontier(faction)
        
        if not f_mgr.exploration_frontier:
            return None
            
        # Pop highest priority system
        score, target_system = f_mgr.exploration_frontier.pop(0)
        
        # Select a random planet in that system
        if target_system.planets:
            return random.choice(target_system.planets)
            
        return None

    @profile_method
    def predict_enemy_threats(self, faction: str):
        """
        Scans visible enemy fleets to detect incoming attacks.
        Returns list of dicts: [{target, fleet, eta, strength}]
        """
        threats = []
        f_mgr = self.engine.factions[faction]
        
        # Optimized: Use Cached Candidates
        candidates = self.turn_cache.get("threats_by_faction", {}).get(faction, [])
        
        # Iterate candidates
        for f in candidates:
            if f.faction == faction or f.is_destroyed: continue
            if f.faction == "Neutral": continue
            
            # Visibility Check (Fog of War)
            # We can see fleet if it's at a location we know about (in visible_planets)
            # OR if we have a fleet in the same system (handled by update_visibility usually adding to visible_planets)
            is_visible = False
            
            # Check if current location is visible
            current_loc_name = f.location.name if hasattr(f.location, 'name') else None
            if current_loc_name and current_loc_name in f_mgr.visible_planets:
                is_visible = True
            
            if not is_visible: continue
            
            # Check Destination (Already filtered by owner)
            if not f.destination: continue
            # INCOMING ATTACK!
            # Calculate ETA (Length of remaining path)
            # Path is list of nodes. fleet.route is the remaining path?
            # Fleet logic: route is list of nodes to visit.
            eta = len(f.route) if f.route else 1 
            
            threats.append({
                "target": f.destination,
                "fleet": f,
                "eta": eta,
                "strength": f.power
            })
            print(f"  > [INTELLIGENCE] {faction} detects {f.faction} fleet incoming to {f.destination.name} (ETA: {eta})")
                
        return threats

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
        """Legacy wrapper for backward compatibility, now deferred to posture_manager's internal logic if possible."""
        return self.target_scoring.switch_strategy(faction_name, new_posture, personality)

    def execute_fighting_retreat(self, task_force: TaskForce):
        """
        Manages the rearguard action while the rest of the task force withdraws.
        """
        return self.tf_manager.execute_fighting_retreat(task_force)
    @profile_method('ai_strategy_time')
    def process_faction_strategy(self, faction: str):
        """
        Main entry point for per-faction strategy logic.
        """
        if self.engine.turn_counter % 10 == 0:
             self._log_strategic_deployment(faction)
        # Phase 8: Alliance Stats Telemetry
        if self.engine.turn_counter % 10 == 0 and self.engine.diplomacy:
            self.log_alliance_stats()
        f_mgr = self.engine.get_faction(faction)
        if not f_mgr: return
        
        owned_planets = self.engine.planets_by_faction.get(faction, [])
        if not owned_planets: return # No presence
        
        # 1. Context & Personality
        personality = self._initialize_strategy_context(faction, f_mgr)
        
        # [LEARNING] Generate Counter-Mandates
        if not hasattr(self, 'turn_cache'): self.turn_cache = {}
        if 'mandates' not in self.turn_cache: self.turn_cache['mandates'] = {}
        
        mandates = self.learning_engine.generate_counter_mandates(faction)
        self.turn_cache['mandates'][faction] = mandates
        
        # 2. Strategic Planning
        self._update_operational_plan(faction, f_mgr, personality)
        strategic_plan = f_mgr.active_strategic_plan
        
        # Calculate Context & Weights for Execution Phase
        # We derived these in _update_operational_plan too, ideally we reuse or recalculate.
        # Recalculating is cheap.
        econ_health = self.assess_economic_health(faction)
        context = self._determine_strategic_context(faction, f_mgr, econ_health['state'])
        weights = self.dynamic_weights.get_weights(context, personality)
        
        # 3. Execution Pipeline
        self._execute_strategy_pipeline(faction, f_mgr, personality, strategic_plan, owned_planets, weights)

        # 4. [Phase 22] Process Sieges & Invasions
        self._process_sieges(faction)

    def _process_sieges(self, faction: str):
        """
        [Phase 22] Checks for sieged planets where we have armies and triggers invasions.
        """
        f_mgr = self.engine.factions.get(faction)
        if not f_mgr: return

        # Get all fleets of this faction
        fleets = [f for f in self.engine.fleets if f.faction == faction and not f.is_destroyed]
        
        for fleet in fleets:
            if not fleet.location: continue
            
            # Check if location is a valid target (Planet)
            if not hasattr(fleet.location, 'owner'): continue
            
            planet = fleet.location
            
            # Skip invalid targets
            if planet.owner == faction: continue
            
            # Phase 22: Proactive Invasion Trigger
            # We don't always need a formal "siege" flag to invade if we have troops ready.
            # If the planet is Neutral, it's just colonization.
            # If the planet is Enemy, we should check if we can land. (War Check)
            is_at_war = False
            if planet.owner != "Neutral" and hasattr(self.engine, 'diplomacy') and self.engine.diplomacy:
                 dm = self.engine.diplomacy
                 state = dm.treaty_coordinator.get_treaty(faction, planet.owner)
                 is_at_war = state == "War"
            
            can_invade = False
            if planet.owner == "Neutral":
                can_invade = True
            elif is_at_war:
                can_invade = True
            elif getattr(planet, 'is_sieged', False):
                can_invade = True
            
            if not can_invade:
                continue

            # [FIX] Proactive War Check for Invasion
            # "War must be declared BEFORE attacking" - User
            if planet.owner != "Neutral" and hasattr(self.engine, 'diplomacy') and self.engine.diplomacy:
                 dm = self.engine.diplomacy
                 state = dm.treaty_coordinator.get_treaty(faction, planet.owner)
                 rel = dm.get_relation(faction, planet.owner)
                 if state != "War" and rel < -25:
                     dm._declare_war(faction, planet.owner, rel, self.engine.turn_counter, reason="Invasion of " + planet.name)
                
            # Check for Cargo Armies
            if not fleet.cargo_armies: continue
            
            # Trigger Invasion
            if self.engine.logger:
                 self.engine.logger.campaign(f"[STRATEGY] {faction} launching invasion of {planet.name} from {fleet.id}!")
            
            if hasattr(self.engine.battle_manager, 'land_armies'):
                 self.engine.battle_manager.land_armies(fleet, planet)

    def _initialize_strategy_context(self, faction: str, f_mgr: Any) -> Any:
        """Loads and adapts faction personality and strategic posture."""
        personality = self.get_faction_personality(faction)

        # Adaptive Check (Every 3 turns)
        if self.engine.turn_counter % 3 == 0:
            decision = self.evaluate_strategic_posture(faction, personality, f_mgr.active_strategic_plan)
            # Log significant posture changes (handled in evaluate_strategic_posture or we can log here if it returns a change?)
            # evaluate_strategic_posture returns None or "CHANGED" maybe? 
            # Looking at source, it likely modifies internal state.
            pass
        
        # Apply adaptive learning
        personality = self.adapt_personality(faction, personality)
        
        # [QUIRK] Chaos Randomness (Phase 5)
        if faction == "Chaos":
             if _ai_rng.random() < 0.2:
                  personality.aggression += 0.5
             elif _ai_rng.random() < 0.1:
                  personality.aggression *= 0.5

        # Persist updated personality
        f_mgr.learned_personality = personality
        return personality

    def _determine_strategic_context(self, faction: str, f_mgr: Any, econ_state: str) -> str:
        """Determines the current strategic context for dynamic weighting."""
        # 1. Recovery Mode (Step 2.1)
        if econ_state in ["CRISIS", "BANKRUPT"] or getattr(f_mgr, 'recovery_mode', False):
            return "RECOVERY"

        # 2. Early Expansion (Turn < 25)
        if self.engine.turn_counter < 25:
            return "EARLY_EXPANSION"
            
        # 3. Total War (At war with multiple major powers)
        active_wars = 0
        if self.engine.diplomacy:
            for other_f in self.engine.factions:
                if other_f == "Neutral": continue
                if self.engine.diplomacy.get_relation(faction, other_f) == "War":
                    active_wars += 1
        
        if active_wars >= 2 or f_mgr.strategic_posture == "TOTAL_WAR":
            return "TOTAL_WAR"
            
        # 4. Consolidation (Overextended)
        if f_mgr.strategic_posture == "CONSOLIDATION":
            return "CONSOLIDATION"
            
        # 5. Threatened (Incoming fleets or aggressive neighbors)
        threats = self.turn_cache.get("threats_by_faction", {}).get(faction, [])
        if threats:
            return "THREATENED"
        
        # 6. Expansion
        if f_mgr.strategic_posture == "EXPANSION":
            return "EXPANSION"
            
        return "DEFAULT"

    def _update_operational_plan(self, faction: str, f_mgr: Any, personality: FactionPersonality):
        """Updates the high-level strategic plan and checks for failures."""
        # [LEARNING] Check for Target Failures before planning new ones
        self.check_target_failures(faction)
        
        # [PHASE 7] VASSAL ALIGNMENT
        # If this faction is a Vassal, copy Overlord's plan if available
        if self.engine.diplomacy:
            treaties = self.engine.diplomacy.get_treaties(faction)
            overlord = None
            for other_f, state in treaties.items():
                if state == "Overlord":
                    overlord = other_f
                    break
            
            if overlord:
                overlord_mgr = self.engine.get_faction(overlord)
                if overlord_mgr and overlord_mgr.active_strategic_plan:
                    if not f_mgr.active_strategic_plan or f_mgr.active_strategic_plan.plan_id != overlord_mgr.active_strategic_plan.plan_id:
                        f_mgr.active_strategic_plan = copy.deepcopy(overlord_mgr.active_strategic_plan)
                        if self.engine.logger:
                            self.engine.logger.strategy(f"[VASSAL ALIGNMENT] {faction} adopting Overlord {overlord}'s strategic plan.")
                    return # Skip normal planning
        
        econ_health = self.assess_economic_health(faction)
        current_state = {
            'econ_health': {'state': econ_health['state']}
        }
        
        # New: Determine Context and Weights
        context = self._determine_strategic_context(faction, f_mgr, econ_health['state'])
        weights = self.dynamic_weights.get_weights(context, personality)
        
        # Inject weights into current state for planner to use
        current_state['weights'] = weights
        
        if not f_mgr.active_strategic_plan or \
           self.planner.evaluate_plan_progress(faction, f_mgr.active_strategic_plan) == "COMPLETED":
             f_mgr.active_strategic_plan = self.planner.create_plan(faction, personality, current_state)

    def _execute_strategy_pipeline(self, faction: str, f_mgr: Any, personality: Any, strategic_plan: Any, owned_planets: list, weights: dict):
        """Executes sequential strategy phases: Economic, Defensive, Offensive, and Research."""
        
        # --- PHASE 0: PRE-ANALYSIS ---
        threatened_planets = [p for p in owned_planets if any(ag.faction != faction for ag in p.armies if not ag.is_destroyed)]
        econ_health = self.assess_economic_health(faction)
        econ_state = econ_health["state"]
        
        # Aggression Scaling
        aggression = personality.aggression
        expansion_bias = personality.expansion_bias
        
        if econ_state == "STRESSED":
            aggression *= 0.7
            expansion_bias *= 0.6
        elif econ_state == "CRISIS":
            aggression *= 0.4
            expansion_bias = 0.2
        elif econ_state == "BANKRUPT":
            aggression = 0.2
            expansion_bias = 0.0

        # --- PHASE: ECONOMIC & TASK FORCE ---
        self.economic_strategy.handle_economic_restraint(faction, econ_state)
        self._manage_task_forces(faction)
        
        # --- PHASE: FLEET ASSIGNMENT ---
        idle_fleets = self._get_idle_fleets(faction)
        # Split overlarge fleets if we have too few operational groups
        idle_fleets = self.tf_manager.split_overlarge_fleets(faction, idle_fleets)
        
        available_fleets = self._get_available_fleets(faction, idle_fleets)
        
        # [NEW] Construction Task Forces (Deep Space Stations)
        # Attempt to build stations at choke points if we have resources
        if self.engine.turn_counter > 10: # Give some time for initial expansion
             self.tf_manager.form_construction_task_force(faction, available_fleets)
        
        # --- PHASE: DEFENSIVE & RESERVES ---
        is_bankrupt = econ_state == "BANKRUPT"
        available_fleets = self.defensive_strategy.manage_strategic_reserves(faction, available_fleets, threatened_planets, is_bankrupt)
        self.concentrate_forces(faction)
        
        zones = self.classify_defense_zones(faction) if self.engine.diplomacy else {} 
        available_fleets = self.defensive_strategy.handle_defensive_priority(faction, available_fleets, threatened_planets, personality, econ_health, zones)

        # --- PHASE: INTERCEPTION ---
        available_fleets = self.interception_strategy.handle_predictive_interception(faction, available_fleets, personality, econ_state, econ_health['upkeep'], econ_health['income'], zones)

        # --- PHASE: OFFENSIVE EXPANSION ---
        self._handle_expansion_logic(faction, f_mgr, available_fleets, personality, econ_state, owned_planets, expansion_bias, weights)
        
        # --- PHASE: RESEARCH ---
        self.process_standard_research(faction, f_mgr)
        self.process_intel_driven_research(f_mgr, self.engine.turn_counter)
        
        # --- POST-STRATEGY OPS ---
        self._handle_post_strategy_ops(faction, available_fleets, f_mgr, personality, econ_health, strategic_plan)

    def _handle_expansion_logic(self, faction: str, f_mgr: Any, available_fleets: list, personality: Any, econ_state: str, owned_planets: list, expansion_bias: float, weights: dict):
        """Specific logic for exploration vs expansion (Honey Pot Logic)."""
        owned_systems_count = len(set([p.system.name for p in owned_planets if hasattr(p, 'system')]))
        
        if owned_systems_count < 2:
             # ISOLATED: Prioritize finding/seizing first colony
             has_col_target = False
             if f_mgr.requisition >= 200:
                 for pname in f_mgr.known_planets:
                     p = next((x for x in self.engine.all_planets if x.name == pname), None)
                     if p and p.owner == "Neutral" and p.name not in [op.name for op in owned_planets]:
                         has_col_target = True
                         break
             
             if has_col_target:
                 # Colonize first!
                 self.offensive_strategy.handle_offensive_expansion(faction, available_fleets, f_mgr, personality, econ_state, owned_planets, expansion_bias, weights)
                 self.exploration_strategy.handle_exploration(faction, available_fleets, f_mgr, personality)
             else:
                 # Explore first!
                 self.exploration_strategy.handle_exploration(faction, available_fleets, f_mgr, personality)
                 self.offensive_strategy.handle_offensive_expansion(faction, available_fleets, f_mgr, personality, econ_state, owned_planets, expansion_bias, weights)
        else:
             # ESTABLISHED: Prioritize Expansion/War
             self.offensive_strategy.handle_offensive_expansion(faction, available_fleets, f_mgr, personality, econ_state, owned_planets, expansion_bias, weights)
             self.exploration_strategy.handle_exploration(faction, available_fleets, f_mgr, personality)

    def _manage_task_forces(self, faction: str):
        self.tf_manager.ensure_faction_list(faction)
        
        # Log Strategic Deployment (Metric #4)
        if self.engine.turn_counter % 5 == 0:
            self._log_strategic_deployment(faction)
            
        return

    def _get_idle_fleets(self, faction: str) -> List[Fleet]:
        # Phase 17: Filter out ENGAGED fleets (they are busy fighting)
        return [f for f in self.engine.fleets if f.faction == faction and f.destination is None and not getattr(f, 'is_engaged', False)]

    def _get_available_fleets(self, faction: str, idle_fleets: List[Fleet]) -> List[Fleet]:
        active_fleets = []
        for tf in self.task_forces[faction]:
            active_fleets.extend(tf.fleets)
        return [f for f in idle_fleets if f not in active_fleets]

    def _handle_post_strategy_ops(self, faction: str, available_fleets: List[Fleet], f_mgr: Any, personality: FactionPersonality, econ_health: dict, strategic_plan: Any):
        """
        Handles post-strategy operations: Task Force cleaning, patrols, and retreats.
        Extracted from legacy _handle_offensive_expansion.
        """
        self.tf_manager.manage_task_forces_lifecycle(faction, available_fleets, f_mgr, personality, econ_health, strategic_plan)

        # 1.5 Empire-wide Fleet Consolidation (Idle Fleets)
        self.consolidate_available_fleets(faction, available_fleets)

        # 2. Legacy Random Move for Leftovers (Patrols)
        for f in available_fleets:
            if random.random() < 0.1:
                if hasattr(f.location, 'system') and f.location.system.connections:
                        dest_sys = random.choice(f.location.system.connections)
                        if dest_sys.planets:
                            f.move_to(dest_sys.planets[0], engine=self.engine)
                elif hasattr(f.location, 'metadata') and 'target_system' in f.location.metadata:
                    if hasattr(f.location.metadata['target_system'], 'planets'):
                         f.move_to(f.location.metadata['target_system'].planets[0], engine=self.engine)

    @profile_method
    def form_raiding_task_force(self, faction: str, available_fleets: list):
        """
        Forms a small, fast task force to raid enemy economy when bankrupt.
        """
        return self.tf_manager.form_raiding_task_force(faction, available_fleets)

    def consolidate_available_fleets(self, faction: str, available_fleets: List[Fleet]) -> None:
        """Merges unassigned fleets at the same location if they have capacity."""
        if len(available_fleets) < 2: return
        
        max_size = getattr(self.engine, 'max_fleet_size', 100)
        
        # Group by location
        by_loc = {}
        for f in available_fleets:
            if f.is_destroyed: continue
            loc_id = id(f.location)
            if loc_id not in by_loc: by_loc[loc_id] = []
            by_loc[loc_id].append(f)
            
        for loc_id, fleets in by_loc.items():
            if len(fleets) < 2: continue
            
            # Sort by size
            fleets.sort(key=lambda x: len(x.units), reverse=True)
            
            primary = fleets[0]
            for i in range(1, len(fleets)):
                secondary = fleets[i]
                if (len(primary.units) + len(secondary.units)) <= max_size:
                    print(f"  > [EMPIRE] {faction} consolidating loose fleet {secondary.id} into {primary.id}")
                    primary.merge_with(secondary)
                else:
                    primary = secondary

    @profile_method
    def concentrate_forces(self, faction: str):
        """
        Scans active Task Forces and merges them if they are redundant or can combine for a major objective.
        """
        return self.tf_manager.concentrate_forces(faction)

    def check_target_failures(self, faction: str):
        """
        [LEARNING] Checks if any pending target outcomes have failed.
        Called at end of turn (or start of strategy process).
        """
        f_mgr = self.engine.factions.get(faction)
        if not f_mgr or not f_mgr.learning_history.get('target_outcomes'):
            return

        # Get active targets from Task Forces
        active_targets = set()
        if faction in self.task_forces:
            for tf in self.task_forces[faction]:
                if tf.target:
                    active_targets.add(tf.target.name)
        
        # Check pending outcomes
        for entry in f_mgr.learning_history['target_outcomes']:
            if not entry['success'] and entry.get('captured_turn') is None and not entry.get('failed', False):
                # If target is no longer active (TF disbanded/destroyed) AND we don't own it
                # We need to verify planet ownership too
                p = next((p for p in self.engine.all_planets if p.name == entry['target_name']), None)
                if p:
                    # If we own it, campaign_manager should have marked success.
                    # If someone else owns it (and not Neutral? or changed owner?)
                    # Or if we just gave up (no active target)
                    
                    if p.owner == faction:
                        # Should have been caught by CampaignManager, but maybe just happened?
                        entry['success'] = True
                        entry['captured_turn'] = self.engine.turn_counter
                        continue
                        
                    if entry['target_name'] not in active_targets:
                        # We gave up or lost the TF
                        # Mark as FAILED
                        entry['success'] = False
                        entry['failed'] = True
                        entry['fail_turn'] = self.engine.turn_counter
                        # print(f"  > [LEARNING] {faction} failed to capture {entry['target_name']} (Attempt abandoned).")
                        
                    # Also if captured by another faction (e.g. Rival) while we were trying?
                    if p.owner != "Neutral" and p.owner != faction:
                         # Someone else took it!
                         entry['success'] = False
                         entry['failed'] = True
                         entry['fail_turn'] = self.engine.turn_counter
                         entry['reason'] = f"Captured by {p.owner}" 

    @profile_method
    def calculate_exploration_frontier(self, faction: str) -> set:
        """
        Identifies systems that are connected to known systems but are themselves unknown.
        """
        f_mgr = self.engine.factions.get(faction)
        if not f_mgr: return set()
        
        frontier = set()
        known = f_mgr.known_planets
        
        for k_name in known:
            p = next((x for x in self.engine.all_planets if x.name == k_name), None)
            if not p: continue
            
            # Check connections
            if hasattr(p, 'system'):
                # Check System Connections
                if hasattr(p.system, 'connections'):
                    for neighbor_sys in p.system.connections:
                         # Check planets in neighbor system
                         if hasattr(neighbor_sys, 'planets'):
                             for np in neighbor_sys.planets:
                                 if np.name not in known:
                                     frontier.add(np.name)
                                 
        return frontier

    def share_intelligence_with_allies(self, faction: str):
        """Synchronize intelligence_memory and known_planets with allied factions."""
        if not self.engine.diplomacy: return
        
        f_mgr = self.engine.factions.get(faction)
        if not f_mgr: return
        
        # Find Allies (RELATION > 50 or ALLIED)
        allies = []
        for other in self.engine.factions:
            if other == faction or other == "Neutral": continue
            stance = self.get_diplomatic_stance(faction, other)
            if stance in ["ALLIED", "FRIENDLY"]:
                allies.append(other)
                
        if not allies: return
        
        for ally in allies:
             ally_mgr = self.engine.factions.get(ally)
             if not ally_mgr: continue
             
             # 1. Share Known Planets (Bidirectional merge)
             # Doing one way here is enough if called for everyone, but bidirectional ensures immediate sync
             new_knowledge_mine = ally_mgr.known_planets - f_mgr.known_planets
             new_knowledge_theirs = f_mgr.known_planets - ally_mgr.known_planets
             
             if new_knowledge_mine:
                 f_mgr.known_planets.update(new_knowledge_mine)
             if new_knowledge_theirs:
                 ally_mgr.known_planets.update(new_knowledge_theirs)
                 
             if new_knowledge_mine or new_knowledge_theirs:
                 # Reward cooperation with a relationship bonus
                 if self.engine.diplomacy:
                     self.engine.diplomacy.modify_relation(faction, ally, 2, symmetric=True)
                 
             # 2. Share recent intelligence
             current_turn = self.engine.turn_counter
             
             # Share MY recent intel with ALLY
             shared_count = 0
             for p_name, info in f_mgr.intelligence_memory.items():
                 age = current_turn - info.get('last_seen_turn', 0)
                 # Only share FRESH intel (<= 3 turns old)
                 if age <= 3:
                     # Check if ally needs it (ally has older or no intel)
                     ally_info = ally_mgr.intelligence_memory.get(p_name)
                     ally_age = current_turn - ally_info.get('last_seen_turn', 0) if ally_info else 999
                     
                     if ally_age > age:
                         ally_mgr.intelligence_memory[p_name] = info.copy()
                         shared_count += 1
             
             if shared_count > 0:
                 self._track_alliance_stat(faction, ally, "shared_intelligence_count", shared_count)

    def _track_alliance_stat(self, f1, f2, stat, amount=1):
        """Helper to update alliance stats."""
        # Simple key based on sorted pair
        pair_key = "_".join(sorted([f1, f2]))
        if pair_key not in self.alliance_stats:
            self.alliance_stats[pair_key] = {"shared_intelligence_count": 0, "coordinated_attacks": 0, "members": [f1, f2]}
            
        self.alliance_stats[pair_key][stat] += amount

    def log_alliance_stats(self):
        """Logs alliance effectiveness (Metric #3)."""
        if not hasattr(self.engine, 'telemetry') or not self.engine.telemetry: return
        
        for pool_id, stats in self.alliance_stats.items():
            # Calculate simple score
            stability_score = 100 # Placeholder
            benefit_score = stats["shared_intelligence_count"] * 0.5 + stats["coordinated_attacks"] * 5
            
            self.engine.telemetry.log_event(
                EventCategory.DIPLOMACY,
                "alliance_effectiveness",
                {
                    "alliance_id": pool_id,
                    "members": stats["members"],
                    "turn": self.engine.turn_counter,
                    "metrics": {
                        "shared_intelligence_count": stats["shared_intelligence_count"],
                        "coordinated_attacks": stats["coordinated_attacks"]
                    },
                    "stability_score": stability_score,
                    "mutual_benefit_score": benefit_score
                },
                turn=self.engine.turn_counter
            )
        
        # Reset periodic counters? Or keep cumulative?
        # Metric definition implies snapshots.
        # Let's keep cumulative for now, or maybe reset if we want "per window"?
        # Recommendation says "metrics" object. History suggests cumulative is better for "effectiveness".
        pass 

    def _log_grudge_lifecycle(self, victim, aggressor, value, reason, event_type):
        """Logs grudge lifecycle events (Metric #4)."""
        print(f"[DEBUG] _log_grudge_lifecycle: {victim} vs {aggressor}, type={event_type}")
        # Telemetry logging for grudges would go here
        # Example:
        # if not hasattr(self.engine, 'telemetry') or not self.engine.telemetry: return
        # self.engine.telemetry.log_event(
        #     EventCategory.DIPLOMACY,
        #     "grudge_lifecycle",
        #     {
        #         "victim": victim,
        #         "aggressor": aggressor,
        #         "value": value,
        #         "reason": reason,
        #         "event_type": event_type,
        #         "turn": self.engine.turn_counter
        #     },
        #     turn=self.engine.turn_counter
        # )

    def _log_strategic_deployment(self, faction: str):
        """Logs strategic deployment metrics (Metric #4)."""
        if not hasattr(self.engine, 'telemetry') or not self.engine.telemetry: return
        
        # 1. Zone Coverage
        zones = self.classify_defense_zones(faction) if self.engine.diplomacy else {}
        total_planets = len(self.engine.planets_by_faction.get(faction, []))
        covered_planets = len(zones) # Simplified: Assumes all classified are "covered" or just registered
        
        # Determine actual coverage (fleets present in zones)
        # This is expensive to calc perfectly, let's use a proxy:
        # Ratio of TaskForces to Owned Planets
        tf_count = len(self.task_forces.get(faction, []))
        
        coverage_pct = (tf_count / total_planets) if total_planets > 0 else 0.0
        
        # 2. Fleet Utilization
        all_fleets = [f for f in self.engine.fleets if f.faction == faction and not f.is_destroyed]
        total_fleets = len(all_fleets)
        idle_fleets = len(self._get_idle_fleets(faction))
        active_fleets = total_fleets - idle_fleets
        
        utilization_pct = (active_fleets / total_fleets) if total_fleets > 0 else 0.0
        
        # 3. Rapid Response Readiness
        # Count fleets in "Reserve" task forces or strictly Defensive
        reserve_count = 0
        if faction in self.task_forces:
             for tf in self.task_forces[faction]:
                 if tf.strategy in ["DEFENSE", "RESERVE", "INTERCEPTION", "DEFEND"]:
                     reserve_count += 1
        
        readiness_pct = (reserve_count / tf_count) if tf_count > 0 else 0.0
        
        self.engine.telemetry.log_event(
            EventCategory.MOVEMENT,
            "strategic_deployment",
            {
                "faction": faction,
                "turn": self.engine.turn_counter,
                "zone_coverage": min(coverage_pct, 1.0),
                "fleet_utilization": utilization_pct,
                "rapid_response_readiness": readiness_pct,
                "total_fleets": total_fleets,
                "active_task_forces": tf_count
            },
            turn=self.engine.turn_counter,
            faction=faction
        ) 

