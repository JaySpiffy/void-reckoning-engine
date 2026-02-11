import random
import time
from typing import List, Optional, Any, TYPE_CHECKING
from src.reporting.telemetry import EventCategory, VerbosityLevel
from src.core.constants import (
    FLEET_COMMISSION_THRESHOLD, FLEET_COMMISSION_COST, CONSTRUCTION_REQ_THRESHOLD,
    COLONIZATION_REQ_COST, RESEARCH_COST_THRESHOLD
)
from src.core import balance as bal
from src.utils.profiler import profile_method
import math

# Services
from src.services.recruitment_service import RecruitmentService
from src.services.construction_service import ConstructionService

# Components
from src.managers.economy.resource_handler import ResourceHandler
from src.managers.economy.budget_allocator import BudgetAllocator
from src.managers.economy.insolvency_handler import InsolvencyHandler
from src.utils.rust_economy import RustEconomyWrapper

if TYPE_CHECKING:
    from src.core.interfaces import IEngine
    from src.models.faction import Faction
    from src.models.planet import Planet

class EconomyManager:
    """
    Coordinator for the economic system.
    Delegates specific tasks to:
    - ResourceHandler (Income/Upkeep)
    - BudgetAllocator (Spending)
    - InsolvencyHandler (Bankruptcy)
    - Recruitment/Construction Services
    """
    def __init__(self, campaign_engine: 'IEngine') -> None:
        self.engine: 'IEngine' = campaign_engine
        
        # RNG Initialization
        base_seed = self.engine.game_config.get("simulation", {}).get("random_seed")
        if base_seed is not None:
            self._economy_rng = random.Random(base_seed + 300)
            if self.engine.logger:
                self.engine.logger.info(f"[RNG] EconomyManager Initialized with Seed: {base_seed} -> Init: {base_seed + 300}")
        else:
            self._economy_rng = random.Random()
            if self.engine.logger:
                self.engine.logger.warning("[RNG] EconomyManager Initialized with NO SEED (Non-Deterministic)")
            
        self.recruitment_service = RecruitmentService(campaign_engine, self._economy_rng)
        self.construction_service = ConstructionService(campaign_engine, self._economy_rng)
        
        # New Components
        self.resource_handler = ResourceHandler(campaign_engine)
        self.rust_econ = RustEconomyWrapper()
        
        self.budget_allocator = BudgetAllocator(
            campaign_engine, 
            self.recruitment_service, 
            self.construction_service, 
            rng=self._economy_rng
        )
        self.insolvency_handler = InsolvencyHandler(campaign_engine)
        
        self.faction_econ_cache = {}
        
        # Performance Counters
        self.perf_metrics = {
            "economy_time": 0.0,
            "upkeep_calc_time": 0.0, # Now aggregated manually or retrieved
            "insolvency_time": 0.0,
            "disbanded_count": 0
        }
        
        # Recovery tracking for telemetry
        self.faction_recovery_state = {}  # {faction: {"mode": str, "start_turn": int, "accumulated_debt_max": 0}}
        
        # Cumulative Recovery Impact (New)
        self.cumulative_recovery_impact = {} # {faction: {"grants": 0, "forgiven": 0, "disbanded": 0, "liquidated": 0, "events": 0, "durations": []}}

    def register_caches(self):
        """Registers economic caches with the engine's cache manager."""
        if hasattr(self.engine, 'cache_manager'):
            self.engine.cache_manager.register_cache(self.clear_caches, "economy_econ_cache")

    def clear_caches(self):
        """Clears all cached economic data."""
        self.faction_econ_cache.clear()

    # [PHASE 8] Serialization Support
    def __getstate__(self):
        """Custom serialization to handle RNG and circular references."""
        state = self.__dict__.copy()
        # Remove unpicklable or reconstructed objects
        if 'engine' in state: del state['engine']
        if 'rust_econ' in state: del state['rust_econ'] # Rust wrapper might not picklable
        if '_economy_rng' in state:
             state['_economy_rng_state'] = self._economy_rng.getstate()
             del state['_economy_rng']
             
        return state

    def __setstate__(self, state):
        """Custom deserialization to restore state."""
        # Restore RNG
        if '_economy_rng_state' in state:
            self._economy_rng = random.Random()
            self._economy_rng.setstate(state['_economy_rng_state'])
            del state['_economy_rng_state']
        else:
            self._economy_rng = random.Random()
            
        self.__dict__.update(state)
        # 'engine' must be re-injected by SnapshotManager
        # Rust wrappers re-init
        self.rust_econ = RustEconomyWrapper()
    
    def process_economy(self) -> None:
        """
        Executes the full economic cycle for the current turn.
        """
        start_time = time.time()
        
        # [Iron Bank] Process Loans & Interest (Priority 1)
        # We process this FIRST so the Bank gets paid before any spending or income calculation.
        if hasattr(self.engine, 'banking_manager'):
            self.engine.banking_manager.process_banking_cycle()

        # [PHASE 5] Rust Economy Integration
        self._sync_rust_economy()
        self.rust_reports = self.rust_econ.get_all_reports()
        
        # Flush Rust Economy Events (Insolvency, etc.)
        if hasattr(self.engine, 'telemetry') and self.engine.telemetry:
            self.rust_econ.flush_logs(self.engine.telemetry)
        
        # Step 0: Global Banking (Debt, etc.)
        if hasattr(self.engine, 'banking_manager'):
            self.engine.banking_manager.process_banking_cycle()

        for f_name in sorted([f.name for f in self.engine.get_all_factions()]):
            if f_name == "Neutral": continue
            
            report = self.rust_reports.get(f_name)
            if not report: continue
                
            self.process_faction_economy(f_name, report=report)

        self.perf_metrics["economy_time"] = time.time() - start_time
        # Sync metrics from sub-components
        self.perf_metrics["insolvency_time"] += self.insolvency_handler.perf_metrics["insolvency_time"]
        self.perf_metrics["disbanded_count"] += self.insolvency_handler.perf_metrics["disbanded_count"]

    @profile_method
    def process_faction_economy(self, f_name: str, report: dict = None) -> None:
        faction_mgr = self.engine.get_faction(f_name)
        if not faction_mgr: return
        
        # 1. Map Rust Report to Python Economic State
        if not report:
             # Fallback to local calculation if Rust fails or missing (Safety check)
             cached_econ = self.resource_handler.precalculate_economics().get(f_name, {})
             econ_data = self._hydrate_cached_econ(f_name, cached_econ, faction_mgr)
        else:
             # Rust provided the raw deterministic numbers (The Processor)
             econ_data = {
                "income": report["total_income"]["credits"],
                "total_upkeep": report["total_upkeep"]["credits"],
                "net_profit": report["net_profit"]["credits"],
                "research_income": report["total_income"]["research"],
                "income_by_category": {cat: res["credits"] for cat, res in report.get("income_by_category", {}).items()},
                "is_insolvent": report.get("is_insolvent", False),
                # We still need margin for AI decisions
                "margin": 1.0
             }
             if econ_data["total_upkeep"] > 0:
                  econ_data["margin"] = round(econ_data["income"] / econ_data["total_upkeep"], 2)
             else:
                  econ_data["margin"] = 5.0 # Max healthy margin for AI
            
        # 1b. Process Construction Queues (Before Spending)
        self.construction_service.process_queues_for_faction(f_name)
        
        # 2. Telemetry: resource_production
        if self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "resource_production",
                {
                    "resources": ["Requisition"],
                    "amount": econ_data["income"],
                    "planet_id": None,  # Aggregate
                    "total_income": econ_data["income"],
                    "research_gross": econ_data.get("research_income", 0),
                    "breakdown": econ_data.get("income_by_category", {})
                },
                faction=f_name
            )
        
        # [PHASE 6] Aggregate Production Trace
        from src.config import logging_config
        if logging_config.LOGGING_FEATURES.get('resource_production_breakdown', False):
            if hasattr(self.engine.logger, 'economy'):
                trace_msg = {
                    "event_type": "aggregate_production_trace",
                    "faction": f_name,
                    "income": econ_data["income"],
                    "upkeep": econ_data["upkeep"],
                    "net": econ_data["income"] - econ_data["upkeep"],
                    "breakdown": econ_data.get("income_by_category", {}),
                    "turn": self.engine.turn_counter
                }
                self.engine.logger.economy(f"[ECON] {f_name} aggregate economy trace", extra=trace_msg)
            
            # Telemetry: resource_consumption (Upkeep)
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "resource_consumption",
                {
                    "resources": ["Requisition"],
                    "amount": econ_data["upkeep"],
                    "purpose": "upkeep",
                    "total_upkeep": econ_data["upkeep"],
                    "military_upkeep": econ_data.get("military_upkeep", 0),
                    "infrastructure_upkeep": econ_data.get("infrastructure_upkeep", 0)
                },
                faction=f_name
            )

            # Telemetry: trade_route_activity (if any)
            trade_inc = econ_data.get("income_by_category", {}).get("Trade", 0)
            if trade_inc > 0:
                self.engine.telemetry.log_event(
                    EventCategory.ECONOMY,
                    "trade_route_activity",
                    {
                        "route_id": "faction_aggregate",
                        "trade_type": "tax",
                        "volume": trade_inc,
                        "trade_income": trade_inc,
                        "turn": self.engine.turn_counter
                    },
                    faction=f_name
                )

        # 3. Insolvency Protocols
        income, upkeep = econ_data["income"], econ_data["upkeep"]
        if faction_mgr.requisition < 0:
            my_fleets = [f for f in self.engine.fleets_by_faction.get(f_name, []) if not f.is_destroyed]
            self.insolvency_handler.handle_insolvency(f_name, faction_mgr, my_fleets, income, upkeep, cached_upkeep=upkeep)
            
            # Recheck check (simple) - if strongly negative still, return?
            # Original logic: If still broke, we can't spend physical cash.
            # Recheck check (simple) - if strongly negative still, return?
            # Original logic: If still broke, we can't spend physical cash.
            if faction_mgr.requisition < 0:
                # NEW: Emergency Funding Check
                if hasattr(faction_mgr, 'emergency_aid_cooldown'):
                    faction_mgr.emergency_aid_cooldown -= 1
                else:
                    faction_mgr.emergency_aid_cooldown = 0
                
                if faction_mgr.emergency_aid_cooldown <= 0:
                    self.process_emergency_funding(f_name, faction_mgr)
            
            # NEW: Debt Restructuring
            self.process_debt_restructuring(f_name, faction_mgr)

            # FALLTHROUGH: We allow the Budget Allocator to run even if Requisition < 0 
            # so that RECOVERY mode logic (which handles debt exceptions) can execute. 

        # 2b. Negative Income Streak Check
        net_income = income - upkeep
        if net_income < 0:
            faction_mgr.consecutive_negative_turns = getattr(faction_mgr, 'consecutive_negative_turns', 0) + 1
        else:
            faction_mgr.consecutive_negative_turns = 0
            
        if faction_mgr.consecutive_negative_turns >= 3 and self.engine.telemetry:
             # Prevent spam: log only on 3, 5, 10, etc.
             if faction_mgr.consecutive_negative_turns in [3, 5, 10, 20]:
                 self.engine.telemetry.log_event(
                     EventCategory.ECONOMY,
                     "consecutive_negative_income",
                     {
                         "consecutive_turns": faction_mgr.consecutive_negative_turns,
                         "current_net_income": net_income,
                         "stockpile": faction_mgr.requisition
                     },
                     turn=self.engine.turn_counter,
                     faction=f_name
                 ) 

        # 3. Execute Budget & Spending (BudgetAllocator)
        with open("debug_army.txt", "a") as f:
              f.write(f"DEBUG_ECON_MGR: Processing {f_name} Req: {faction_mgr.requisition}\n")
              
        self.budget_allocator.execute_budget(f_name, faction_mgr, econ_data)
        
        # Log insolvency prediction telemetry
        prediction = self._predict_insolvency(f_name, faction_mgr, income, upkeep)
        if self.engine.telemetry and prediction["predicted_turns_until_zero"] < 50:
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "insolvency_prediction",
                {
                    "faction": f_name,
                    "turn": self.engine.turn_counter,
                    "current_stockpile": faction_mgr.requisition,
                    "predicted_turns_until_zero": prediction["predicted_turns_until_zero"],
                    "confidence": prediction["confidence"],
                    "contributing_factors": prediction["contributing_factors"],
                    "recommended_actions": prediction["recommended_actions"]
                },
                faction=f_name
            )

        # Log Economic Health Score (New)
        if self.engine.telemetry:
             self.engine.telemetry.metrics.log_economic_health_event(f_name, faction_mgr, self.engine.telemetry)
             
             if self.engine.turn_counter % 20 == 0 and f_name in self.cumulative_recovery_impact:
                 impact = self.cumulative_recovery_impact[f_name]
                 if impact["events"] > 0:
                     self.engine.telemetry.log_event(
                         EventCategory.ECONOMY,
                         "cumulative_recovery_impact",
                         {
                             "faction": f_name,
                             "total_grants": impact.get("grants", 0),
                             "total_forgiven": impact.get("forgiven", 0),
                             "total_events": impact.get("events", 0)
                         },
                         turn=self.engine.turn_counter,
                         faction=f_name
                     )
                     
             # Batch 3: Bottleneck Analysis & Combat Correlation (Every 10 turns)
             if self.engine.turn_counter % 10 == 0:
                 # Bottlenecks
                 if hasattr(self.engine, 'resource_handler'):
                      bottlenecks = self.engine.resource_handler.analyze_flow_bottlenecks(f_name, econ_data)
                      if bottlenecks.get("bottlenecks"):
                          self.engine.telemetry.log_event(
                              EventCategory.ECONOMY,
                              "resource_flow_bottleneck",
                              bottlenecks,
                              turn=self.engine.turn_counter,
                              faction=f_name
                          )
                 
                 # Combat Correlation
                 correlation = self.engine.telemetry.metrics.correlate_combat_economy(f_name)
                 if correlation.get("correlation_score", 0) > 0.3:
                      self.engine.telemetry.log_event(
                          EventCategory.ECONOMY,
                          "combat_economic_correlation",
                          correlation,
                          turn=self.engine.turn_counter,
                          faction=f_name
                      )
             # Building Effectiveness (Metric #3)
             # Log every 20 turns
             if self.engine.turn_counter % 20 == 0:
                 self._log_building_effectiveness(f_name, faction_mgr, econ_data)
                 self._log_recovery_effectiveness(f_name)
        
        # Record faction stats for indexer (Telemetry)
        if self.engine.telemetry and hasattr(self.engine, 'tech_manager'):
            tech_depth = self.engine.tech_manager.calculate_tech_tree_depth(
                f_name,
                faction_mgr.unlocked_techs
            )
            
            if not hasattr(self.engine.telemetry, 'faction_stats_cache'):
                self.engine.telemetry.faction_stats_cache = {}
            
            live_metrics = self.engine.telemetry.metrics.get_live_metrics()
            self.engine.telemetry.faction_stats_cache[f_name] = {
                "tech_depth": tech_depth,
                "unlocked_techs": faction_mgr.unlocked_techs,
                "construction_activity": live_metrics.get("construction_activity", {}).get(f_name, {}),
                "research_impact": live_metrics.get("research_impact", {}).get(f_name, {})
            }

    def _hydrate_cached_econ(self, f_name, cached_econ, faction_mgr):
        """Reconstructs full econ data from cache + dynamic mode determination."""
        upkeep = cached_econ["total_upkeep"]
        income = cached_econ["income"]
        margin = income / upkeep if upkeep > 0 else 1.0
        
        # [ENGINE MANAGED] AI Economy Modes
        # The engine now dictates these rules, removing reliance on external config loops.
        modes = [
            {
                "name": "EXPANSION",
                "condition_type": "rich",
                "threshold": 50000.0, # Reduced from 300k to 50k for more aggressive expansion
                "budget": {"recruitment": 0.5, "construction": 0.4, "research": 0.1} # Increased recruitment from 0.3 to 0.5
            },
            {
                "name": "WAR",
                "condition_type": "at_war",
                "threshold": 0.0,
                "budget": {"recruitment": 0.6, "construction": 0.1, "research": 0.3}
            },
            {
                "name": "DESPERATE_DEFENSE",
                "condition_type": "losing",
                "threshold": 0.3, # Margin < 0.3
                "budget": {"recruitment": 0.8, "construction": 0.1, "research": 0.1}
            },
            {
                "name": "CONSOLIDATION",
                "condition_type": "default",
                "threshold": 0.0,
                "budget": {"recruitment": 0.3, "construction": 0.5, "research": 0.2}
            }
        ]
        
        # Default fallback
        active_mode = modes[-1] 
        
        # Track previous mode for change detection
        previous_mode = self.faction_recovery_state.get(f_name, {}).get("mode", "UNKNOWN")
        
        # Step 5: RECOVERY MODE (Override)
        # Step 5: RECOVERY MODE (Override)
        if faction_mgr.requisition < 0:
            # Calculate recovery level based on debt severity
            debt_severity = abs(faction_mgr.requisition)
            recruitment_budget = 0.0
            
            if debt_severity < bal.RECOVERY_DEBT_THRESHOLD_MILD:
                 recruitment_budget = bal.RECOVERY_RECRUITMENT_MILD
            elif debt_severity < bal.RECOVERY_DEBT_THRESHOLD_MODERATE:
                 recruitment_budget = bal.RECOVERY_RECRUITMENT_MODERATE
            
            active_mode = {
                "name": "RECOVERY",
                "budget": {
                    "recruitment": recruitment_budget,
                    "construction": 1.0 - recruitment_budget, # Focus on Economy
                    "research": 0.0
                }
            }
        # [AAA Refinement] Economic Adaptation for Poor Performance
        elif getattr(faction_mgr, 'poor_performance_streak', 0) > 5:
            # If we are failing repeatedly, stop expanding and consolidate.
            # Check if we are at war to decide defense vs consolidation
            if hasattr(faction_mgr, 'enemies') and faction_mgr.enemies:
                 active_mode = {
                    "name": "DESPERATE_DEFENSE",
                    "condition_type": "losing",
                    "threshold": 0.3,
                    "budget": {"recruitment": 0.8, "construction": 0.1, "research": 0.1}
                 }
            else:
                 active_mode = {
                    "name": "CONSOLIDATION",
                    "condition_type": "default",
                    "threshold": 0.0,
                    "budget": {"recruitment": 0.1, "construction": 0.5, "research": 0.4} # Boost tech to catch up
                 }
        else:
            for m in modes:
                c_type = m.get("condition_type")
                threshold = m.get("threshold", 0)
                if c_type == "margin":
                    if margin < threshold: active_mode = m; break
                elif c_type == "stockpile" or c_type == "rich":
                    if faction_mgr.requisition > threshold: active_mode = m; break
                elif c_type == "at_war":
                    if hasattr(faction_mgr, 'enemies') and faction_mgr.enemies: active_mode = m; break
                elif c_type == "losing":
                    if margin < threshold: active_mode = m; break
                elif c_type == "default":
                    active_mode = m
        
        # Log mode change if detected
        new_mode = active_mode["name"]
        if new_mode != previous_mode:
            # Check if we are EXITING recovery
            if previous_mode == "RECOVERY":
                 state = self.faction_recovery_state.get(f_name, {})
                 duration = self.engine.turn_counter - state.get("start_turn", self.engine.turn_counter)
                 max_debt = state.get("accumulated_debt_max", 0)
                 
                 # Log RECOVERY DURATION
                 if self.engine.telemetry:
                     self.engine.telemetry.log_event(
                         EventCategory.ECONOMY,
                         "recovery_mode_duration",
                         {
                             "faction": f_name,
                             "recovery_start_turn": state.get("start_turn"),
                             "recovery_end_turn": self.engine.turn_counter,
                             "duration_turns": duration,
                             "max_debt_encountered": max_debt
                         },
                         turn=self.engine.turn_counter,
                         faction=f_name
                     )

            self._log_mode_change(f_name, previous_mode, new_mode, faction_mgr.requisition)
            self.faction_recovery_state[f_name] = {"mode": new_mode, "start_turn": self.engine.turn_counter, "accumulated_debt_max": abs(min(0, faction_mgr.requisition))}

        elif new_mode == "RECOVERY" and f_name in self.faction_recovery_state:
            # Update recovery state tracking
            self.faction_recovery_state[f_name]["mode"] = new_mode
            current_debt = abs(min(0, faction_mgr.requisition))
            if current_debt > self.faction_recovery_state[f_name].get("accumulated_debt_max", 0):
                 self.faction_recovery_state[f_name]["accumulated_debt_max"] = current_debt

        
        return {
            "income": income,
            "upkeep": upkeep,
            "margin": margin,
            "active_mode": active_mode,
            "income_by_category": cached_econ.get("income_by_category", {}),
            "research_income": cached_econ.get("research_income", 0),
            "military_upkeep": cached_econ.get("military_upkeep", 0),
            "infrastructure_upkeep": cached_econ.get("infrastructure_upkeep", 0)
        }

    def _sync_rust_economy(self):
        """
        Populates the Rust economy engine with data from the simulation.
        Translates Python models (Planet, Fleet, ArmyGroup) into Rust EconomicNodes.
        """
        self.rust_econ.reset()
        
        # 1. Set Global Rules from balance.py
        self.rust_econ.set_rules(
            orbit_discount=getattr(bal, 'ORBIT_DISCOUNT_MULTIPLIER', 0.5),
            garrison_discount=getattr(bal, 'GARRISON_UPKEEP_MULTIPLIER', 0.5),
            navy_penalty_ratio=4, # Baseline: 4 fleets per planet
            navy_penalty_rate=getattr(bal, 'ECON_NAVY_PENALTY_RATE', 0.25),
            vassal_tribute_rate=0.2, # 20%
            fleet_upkeep_scalar=getattr(bal, 'FLEET_MAINTENANCE_SCALAR', 1.0)
        )
        
        # 2. Add Economic Nodes
        for faction in self.engine.get_all_factions():
            f_name = faction.name
            if f_name == "Neutral": continue
            
            # --- Planets & Armies ---
            planets = self.engine.planets_by_faction.get(f_name, [])
            for p in planets:
                p.update_economy_cache()
                cached = p._cached_econ_output
                
                # Planet Node
                self.rust_econ.add_node(
                    node_id=p.name,
                    owner_faction=f_name,
                    node_type="Planet",
                    base_income={
                        "credits": cached["total_gross"] + bal.MIN_PLANET_INCOME,
                        "research": cached["research_output"] + 5 # Passive planetary research
                    },
                    base_upkeep={
                        "credits": p._cached_maintenance
                    },
                    efficiency=0.5 if p.is_sieged else 1.0
                )
                
                # Armies on this planet (Garrisoned or Excess)
                if hasattr(p, 'armies'):
                    p_armies = [ag for ag in p.armies if ag.faction == f_name and not ag.is_destroyed]
                    if p_armies:
                        capacity = getattr(p, 'garrison_capacity', 1)
                        # We sort by upkeep to ensure the most expensive are garrisoned first for discount
                        # Wait, Rust engine applies discount to efficiency_scaled < 1.0
                        # So we mark the first 'capacity' armies as 'garrisoned' (efficiency 0.5)
                        armies_data = []
                        for ag in p_armies:
                            upkeep = sum(getattr(u, 'upkeep', 0) for u in ag.units)
                            armies_data.append((ag.id if hasattr(ag, 'id') else f"Army_{ag.location.name}_{f_name}", upkeep))
                        
                        armies_data.sort(key=lambda x: x[1], reverse=True)
                        
                        for i, (a_id, a_upkeep) in enumerate(armies_data):
                            is_garrisoned = (i < capacity)
                            self.rust_econ.add_node(
                                node_id=f"AG_{a_id}",
                                owner_faction=f_name,
                                node_type="Army",
                                base_income={"credits": 0},
                                base_upkeep={"credits": a_upkeep},
                                efficiency=0.5 if is_garrisoned else 1.0
                            )

            # --- Fleets ---
            fleets = self.engine.fleets_by_faction.get(f_name, [])
            for fl in fleets:
                if fl.is_destroyed: continue
                
                # Fleet Node
                self.rust_econ.add_node(
                    node_id=fl.id,
                    owner_faction=f_name,
                    node_type="Fleet",
                    base_income={"credits": 0},
                    base_upkeep={"credits": fl.upkeep},
                    efficiency=0.5 if fl.is_in_orbit else 1.0
                )
                
                # Special Nodes (Mining Station / Research Outpost)
                for u in fl.units:
                    if getattr(u, 'unit_class', '') == 'MiningStation':
                         self.rust_econ.add_node(
                             node_id=f"Mining_{fl.id}_{u.name}",
                             owner_faction=f_name,
                             node_type="Station",
                             base_income={"credits": 500},
                             base_upkeep={"credits": 0}
                         )
                    elif getattr(u, 'unit_class', '') == 'ResearchOutpost':
                         self.rust_econ.add_node(
                             node_id=f"Research_{fl.id}_{u.name}",
                             owner_faction=f_name,
                             node_type="Station",
                             base_income={"research": 10},
                             base_upkeep={"credits": 0}
                         )

    def get_faction_economic_report(self, f_name: str) -> dict:
        """Public accessor for AI Manager."""
        return self._calculate_economics(f_name)

    @profile_method
    def _calculate_economics(self, f_name: str) -> dict:
        """Helper to calculate economics on demand (bypassing pre-calc/cache logic if needed)."""
        # Note: This duplicates logic from ResourceHandler but for single-shot use. 
        # Ideally ResourceHandler should have a single-faction method.
        # But this is rarely called outside of AI ticks.
        # For now, we can use the cache if available or warn.
        if f_name in self.faction_econ_cache:
            return self._hydrate_cached_econ(f_name, self.faction_econ_cache[f_name], self.engine.get_faction(f_name))
        else:
             # Fallback: empty or error.
             return {"income": 0, "upkeep": 0, "margin": 1.0, "active_mode": {"name": "UNKNOWN", "budget": {}}}

    def _determine_severity(self, debt_amount: int) -> str:
        """Determine severity level based on debt amount."""
        if debt_amount < bal.RECOVERY_DEBT_THRESHOLD_MILD:
            return "mild"
        elif debt_amount < bal.RECOVERY_DEBT_THRESHOLD_MODERATE:
            return "moderate"
        else:
            return "severe"
    
    def _log_mode_change(self, f_name: str, previous_mode: str, new_mode: str, stockpile: int):
        """Log mode change telemetry."""
        if self.engine.telemetry and previous_mode != "UNKNOWN":
            # Calculate duration if exiting a mode
            duration_turns = None
            if f_name in self.faction_recovery_state:
                duration_turns = self.engine.turn_counter - self.faction_recovery_state[f_name].get("start_turn", self.engine.turn_counter)
            
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "recovery_event",
                {
                    "event_type": "mode_change",
                    "faction": f_name,
                    "turn": self.engine.turn_counter,
                    "severity": self._determine_severity(abs(stockpile)),
                    "details": {
                        "previous_mode": previous_mode,
                        "new_mode": new_mode,
                        "stockpile": stockpile,
                        "duration_turns": duration_turns
                    },
                    "outcome": {
                        "success": True,
                        "turns_to_recover": duration_turns
                    }
                },
                turn=self.engine.turn_counter,
                faction=f_name
            )

            # Store duration for cumulative tracking
            if new_mode != "RECOVERY" and previous_mode == "RECOVERY" and duration_turns is not None:
                 if f_name not in self.cumulative_recovery_impact:
                     self.cumulative_recovery_impact[f_name] = {"grants": 0, "forgiven": 0, "disbanded": 0, "liquidated": 0, "events": 0, "durations": []}
                 
                 impact = self.cumulative_recovery_impact[f_name]
                 if "durations" not in impact: impact["durations"] = []
                 impact["durations"].append(duration_turns)
    
    def _log_recovery_event(self, f_name: str, event_type: str, details: dict, outcome: dict):
        """Log recovery event telemetry."""
        if self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "recovery_event",
                {
                    "event_type": event_type,
                    "faction": f_name,
                    "turn": self.engine.turn_counter,
                    "severity": self._determine_severity(abs(self.engine.get_faction(f_name).requisition)),
                    "details": details,
                    "outcome": outcome
                },
                turn=self.engine.turn_counter,
                faction=f_name
            )

    def _log_recovery_effectiveness(self, f_name: str):
        """Logs summary of recovery efforts (Metric #13)."""
        if f_name not in self.cumulative_recovery_impact: return
        
        impact = self.cumulative_recovery_impact[f_name]
        durations = impact.get("durations", [])
        avg_dur = sum(durations) / len(durations) if durations else 0.0
        
        if self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "recovery_effectiveness",
                {
                    "faction": f_name,
                    "total_recovery_events": impact.get("events", 0),
                    "average_turns_to_stabilize": avg_dur,
                    "total_bailout_cost": impact.get("grants", 0) + impact.get("forgiven", 0),
                    "recovery_count": len(durations)
                },
                turn=self.engine.turn_counter,
                faction=f_name
            )

    def _predict_insolvency(self, f_name: str, faction_mgr: 'Faction', income: int, upkeep: int) -> dict:
        """Predict when faction will run out of resources."""
        current_stockpile = faction_mgr.requisition
        net_income = income - upkeep
        
        if net_income >= 0:
            return {
                "predicted_turns_until_zero": 999,
                "confidence": 0.95,
                "contributing_factors": [],
                "recommended_actions": []
            }
        
        # Calculate turns until zero
        predicted_turns = int(abs(current_stockpile) / abs(net_income)) if net_income != 0 else 0
        
        # Determine contributing factors
        factors = []
        if net_income < 0:
            factors.append({"factor": "negative_net_income", "impact": abs(net_income)})
        
        if income > 0 and upkeep > income:
            factors.append({"factor": "upkeep_exceeds_income", "impact": (upkeep - income) / income})
        
        # Check income trend (simplified)
        econ_history = self.faction_econ_cache.get(f_name, {})
        if econ_history.get("income", 0) > 0 and income < econ_history["income"] * 0.8:
            factors.append({"factor": "declining_trend", "impact": (econ_history["income"] - income) / econ_history["income"]})
        
        # Recommended actions
        actions = []
        if predicted_turns < 10:
            actions.append({"action": "reduce_upkeep", "priority": "critical"})
            actions.append({"action": "seek_aid", "priority": "critical"})
        elif predicted_turns < 20:
            actions.append({"action": "reduce_upkeep", "priority": "high"})
            actions.append({"action": "increase_income", "priority": "medium"})
        
        confidence = min(1.0, 0.5 + (len(factors) * 0.15))
        
        return {
            "predicted_turns_until_zero": predicted_turns,
            "confidence": confidence,
            "contributing_factors": factors,
            "recommended_actions": actions
        }
    
    def process_emergency_funding(self, f_name: str, faction_mgr: 'Faction') -> None:
        """
        Provides emergency funding to factions in deep economic collapse.
        """
        # [USER REQUEST] "No magic money." 
        # Emergency Funding is DISABLED. Factions must use the Bank.
        return 
        
        # Only trigger for factions with planets but no income
        owned_planets = self.engine.planets_by_faction.get(f_name, [])
        
        if len(owned_planets) == 0:
            return  # No planets, no help
        
        econ_data = self.faction_econ_cache.get(f_name, {})
        income = econ_data.get("income", 0)
        upkeep = econ_data.get("total_upkeep", 0)
        
        # Check if faction qualifies for emergency aid
        # Must have planets, low income, and negative requisition
        if income < 100 and faction_mgr.requisition < -1000:
            # Calculate emergency grant based on planet count
            grant_per_planet = bal.EMERGENCY_GRANT_PER_PLANET
            emergency_grant = len(owned_planets) * grant_per_planet
            
            # Cap the grant
            emergency_grant = min(emergency_grant, bal.EMERGENCY_GRANT_MAX)
            
            stockpile_before = faction_mgr.requisition
            # Apply grant
            faction_mgr.requisition += emergency_grant
            
            if self.engine.logger:
                self.engine.logger.economy(f"[EMERGENCY] {f_name} received emergency grant of {emergency_grant} Req")
            
            # Track emergency aid in faction stats
            if not hasattr(faction_mgr, 'emergency_aid_received'):
                faction_mgr.emergency_aid_received = 0
            faction_mgr.emergency_aid_received += emergency_grant
            
            # Add cooldown to prevent abuse
            faction_mgr.emergency_aid_cooldown = bal.EMERGENCY_AID_COOLDOWN
            
            # Update Cumulative Impact
            if f_name not in self.cumulative_recovery_impact:
                self.cumulative_recovery_impact[f_name] = {"grants": 0, "forgiven": 0, "disbanded": 0, "liquidated": 0, "events": 0}
            self.cumulative_recovery_impact[f_name]["grants"] += emergency_grant
            self.cumulative_recovery_impact[f_name]["events"] += 1
            
            # Log telemetry event
            self._log_recovery_event(
                f_name,
                "emergency_grant",
                {
                    "grant_amount": emergency_grant,
                    "stockpile_before": stockpile_before,
                    "planets_count": len(owned_planets),
                    "trigger_reason": "low_income_high_debt"
                },
                {
                    "success": True,
                    "stockpile_after": faction_mgr.requisition,
                    "income_after": income,
                    "upkeep_after": upkeep
                }
            )

    def process_debt_restructuring(self, f_name: str, faction_mgr: 'Faction') -> None:
        """
        Forgives a portion of debt for factions in long-term economic collapse.
        """
        # [USER REQUEST] "No magic money."
        # Debt Restructuring is DISABLED. Factions must pay their debts.
        return

        # Track consecutive turns of insolvency
        if not hasattr(faction_mgr, 'insolvent_turns'):
            faction_mgr.insolvent_turns = 0
        
        if faction_mgr.requisition < 0:
            faction_mgr.insolvent_turns += 1
        else:
            faction_mgr.insolvent_turns = 0
        
        # After X turns of continuous insolvency, forgive portion of debt
        if faction_mgr.insolvent_turns >= bal.DEBT_RESTRUCTURING_TURNS:
            debt_amount = abs(faction_mgr.requisition)
            forgiven_amount = int(debt_amount * bal.DEBT_FORGIVENESS_RATIO)
            
            stockpile_before = faction_mgr.requisition
            faction_mgr.requisition += forgiven_amount
            faction_mgr.insolvent_turns = 0  # Reset counter
            
            if self.engine.logger:
                self.engine.logger.economy(f"[DEBT] {f_name} debt restructured: {forgiven_amount} Req forgiven (50%)")
            
            # Track in faction stats
            if not hasattr(faction_mgr, 'debt_forgiven'):
                faction_mgr.debt_forgiven = 0
            faction_mgr.debt_forgiven += forgiven_amount
            
            # Update Cumulative Impact
            if f_name not in self.cumulative_recovery_impact:
                self.cumulative_recovery_impact[f_name] = {"grants": 0, "forgiven": 0, "disbanded": 0, "liquidated": 0, "events": 0, "durations": []}
            self.cumulative_recovery_impact[f_name]["forgiven"] += forgiven_amount
            self.cumulative_recovery_impact[f_name]["events"] += 1
            
            # Get economic data for outcome
            econ_data = self.faction_econ_cache.get(f_name, {})
            income = econ_data.get("income", 0)
            upkeep = econ_data.get("total_upkeep", 0)
            
            # Log telemetry event
            self._log_recovery_event(
                f_name,
                "debt_restructuring",
                {
                    "debt_forgiven": forgiven_amount,
                    "debt_before": debt_amount,
                    "insolvent_turns": bal.DEBT_RESTRUCTURING_TURNS,
                    "trigger_reason": "long_term_insolvency"
                },
                {
                    "success": True,
                    "stockpile_after": faction_mgr.requisition,
                    "income_after": income,
                    "upkeep_after": upkeep
                }
            )

    def _log_building_effectiveness(self, f_name: str, faction_mgr: 'Faction', econ_data: dict):
        """
        Logs effectiveness metrics for buildings (Metric #3).
        Calculates approximate ROI based on output vs upkeep.
        """
        if not self.engine.telemetry: return
        
        # Aggregate effectiveness
        owned_planets = self.engine.planets_by_faction.get(f_name, [])
        total_roi = 0.0
        building_count = 0
        
        from src.core.constants import get_building_database

        for p in owned_planets:
            nodes = p.provinces if hasattr(p, 'provinces') and p.provinces else [p]
            for node in nodes:
                buildings = getattr(node, 'buildings', [])
                for b_id in buildings:
                    b_data = get_building_database().get(b_id, {})
                    upkeep = b_data.get("maintenance", 0)
                    if upkeep <= 0: continue
                    
                    # Estimate Value (Simplified)
                    value = 0
                    desc = b_data.get("effects", {}).get("description", "")
                    
                    if "requisition_output" in b_data:
                        value += b_data["requisition_output"]
                    elif "tax" in desc.lower():
                        value += 200 # Proxy
                    elif "Mining" in desc:
                        value += 500 # Proxy
                        
                    roi = (value / upkeep) if upkeep > 0 else 0
                    total_roi += roi
                    building_count += 1
                    
        avg_roi = total_roi / building_count if building_count > 0 else 0.0
        
        self.engine.telemetry.log_event(
            EventCategory.ECONOMY,
            "building_effectiveness",
            {
                "faction": f_name,
                "turn": self.engine.turn_counter,
                "average_roi": avg_roi,
                "building_count": building_count,
                "total_upkeep": econ_data.get("infrastructure_upkeep", 0)
            },
            turn=self.engine.turn_counter,
            faction=f_name
        )

    def record_market_transaction(self, f_name: str, item: str, amount: int, price: int, t_type: str = "buy"):
        """Placeholder for future market system integration."""
        if self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "market_transaction",
                {
                    "transaction_type": t_type,
                    "resources": [item],
                    "item": item,
                    "amount": amount,
                    "price": price,
                    "type": t_type,
                    "turn": self.engine.turn_counter
                },
                faction=f_name
            )

    def __getstate__(self):
        """Custom serialization to handle engine reference."""
        state = self.__dict__.copy()
        if 'engine' in state: del state['engine']
        if 'rust_econ' in state: del state['rust_econ']
        
        # Exclude services to prevent 'module' pickling errors
        if 'recruitment_service' in state: del state['recruitment_service']
        if 'construction_service' in state: del state['construction_service']
        if 'resource_handler' in state: del state['resource_handler']
        if 'budget_allocator' in state: del state['budget_allocator']
        if 'insolvency_handler' in state: del state['insolvency_handler']

        return state

    def __setstate__(self, state):
        """Custom deserialization."""
        self.__dict__.update(state)
        # Engine re-injected by SnapshotManager
        self.rust_econ = None
        # Services re-inited by reinit_services
        self.recruitment_service = None
        self.construction_service = None
        self.resource_handler = None
        self.budget_allocator = None
        self.insolvency_handler = None

    def reinit_services(self, engine):
        """Re-initializes services after snapshot restore."""
        self.engine = engine
        # Ensure RNG is restored (handled in __setstate__), pass it to services
        rng = getattr(self, '_economy_rng', None)
        
        self.recruitment_service = RecruitmentService(engine, rng)
        self.construction_service = ConstructionService(engine, rng)
        self.resource_handler = ResourceHandler(engine)
        
        self.budget_allocator = BudgetAllocator(
            engine,
            self.recruitment_service,
            self.construction_service,
            rng=rng
        )
        self.insolvency_handler = InsolvencyHandler(engine)
        
        # Restore Rust bridge if possible
        try:
             from src.core.rust_bridge import RustEconomyBridge
             self.rust_econ = RustEconomyBridge()
        except:
             self.rust_econ = None

