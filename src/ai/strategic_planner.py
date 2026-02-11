import random
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING
from src.reporting.telemetry import EventCategory
from universes.base.personality_template import FactionPersonality
from src.config import logging_config

if TYPE_CHECKING:
    from src.managers.ai_manager import StrategicAI

from src.ai.theater_manager import TheaterManager

@dataclass
class StrategicPlan:
    plan_id: str
    faction: str
    created_turn: int
    duration: int
    war_goal: str 
    diplomatic_goal: str = None 
    target_faction: str = None
    target_systems: List[str] = field(default_factory=list)
    priority_planets: List[str] = field(default_factory=list)
    current_phase: str = "PREPARATION"
    active_theater_id: str = None # [Phase 2]
    
    # Phase 5: Multi-Front Operations
    sub_plans: List[dict] = field(default_factory=list) # List of {theater_id, goal, target_systems}
    
    # Progress
    success_metrics: dict = "None" 
    contingency_triggers: list = "None"
    
    # [AAA Upgrade] Deep Trace Reasoning
    persistence_score: float = 10.0  # Decays over time, resists swift abandonment
    failure_reason: str = None       # "TIMEOUT", "OVERWHELMING_FORCE", "BETRAYAL"
    
    def __post_init__(self):
        if self.target_systems is None: self.target_systems = []
        if self.priority_planets is None: self.priority_planets = []
        if self.success_metrics == "None": self.success_metrics = {}
        if self.contingency_triggers == "None": self.contingency_triggers = []

class StrategicPlanner:
    def __init__(self, ai_manager: 'StrategicAI'):
        self.ai = ai_manager
        self.active_plans: Dict[str, StrategicPlan] = {} 
        self.theater_manager = TheaterManager(self.ai.engine) # [Phase 2]

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'ai' in state: del state['ai']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.ai = None
        
    def create_plan(self, faction: str, personality: FactionPersonality, current_state: dict) -> StrategicPlan:
        """Generates a new strategic plan based on faction situation."""
        turn = self.ai.engine.turn_counter
        plan_id = f"PLAN-{faction}-{turn}"
        duration = personality.planning_horizon
        
        # [PHASE 6] AI Decision Trace Init
        trace = {}
        trace_enabled = logging_config.LOGGING_FEATURES.get('ai_decision_trace', False)
        if trace_enabled:
            trace = {
                "event_type": "ai_decision_trace",
                "decision_id": plan_id,
                "faction": faction,
                "turn": turn,
                "decision_type": "strategic_plan_creation",
                "context": {
                    "planning_horizon": duration,
                    "econ_state": current_state.get('econ_health', {}).get('state', 'UNKNOWN')
                },
                "steps": []
            }
        
        # [Phase 5] Analyze All Theaters
        theaters = self.theater_manager.analyze_theaters(faction)
        if trace_enabled:
             trace["steps"].append({
                 "step": "theater_analysis",
                 "theaters_found": len(theaters),
                 "theater_ids": [t.id for t in theaters]
             })
             
        # [AAA Upgrade] Predictive Profiling Check
        # Check for massing fleets on borders
        threats = []
        if hasattr(self.ai, 'profiler') and self.ai.profiler:
            # We need to populate theater.enemy_fleets first (usually done in analyze_theaters)
            threats = self.ai.profiler.analyze_threats(faction, theaters)
            
        # Global Goals (Fallback or Overarching)
        war_goal = "GRAND_STRATEGY_WAIT"

        sub_plans = []
        
        # Global Goals (Fallback or Overarching)
        war_goal = "GRAND_STRATEGY_WAIT"
        diplomatic_goal = None
        target_f = None
        target_sys = []
        
        econ = current_state.get('econ_health', {})
        if econ.get('state') == 'BANKRUPT':
             war_goal = "RAID_ECONOMY"
             duration = 5
             if trace_enabled:
                 trace["steps"].append({
                     "step": "global_goal_selection",
                     "trigger": "bankrupt_state",
                     "selected_goal": war_goal
                 })
             # Select a rich neighbor randomly
        
        # Theater-Level Planning
        if theaters:
            war_goal = "MULTI_FRONT_COORDINATION"
            if trace_enabled and trace["steps"][-1]["step"] != "global_goal_selection":
                 trace["steps"].append({
                     "step": "global_goal_selection",
                     "trigger": "theaters_active",
                     "selected_goal": war_goal
                 })
            
            # [AAA Upgrade] Threat Override
            # If any theater has a massive threat, prioritize defense there
            highest_threat = None
            for t_event in threats:
                 # If threat value is very high (> 50k), panic switch
                 if t_event['value'] > 50000:
                     highest_threat = t_event
                     print(f"  > [STRATEGY] {faction} DETECTED MASSING by {t_event['source']} in {t_event['theater']}! Switching to DEFEND.")
                     war_goal = "EMERGENCY_DEFENSE"
                     break
            
            for index, theater in enumerate(theaters):
                # Assign Doctrine
                self.theater_manager.assign_theater_doctrine(faction, theater, personality)
                self.theater_manager._analyze_choke_points(theater) # Ensure border info
                self.theater_manager.calculate_strategic_value(theater)

                # Determine Sub-Goal
                sub_goal = theater.assigned_goal # DEFEND, ATTACK, EXPAND, SIEGE, BLITZ
                sub_target_f = None
                sub_targets = []
                
                # Identify Local Enemies
                frontier = getattr(theater, 'border_systems', set())
                # Or just use neighbors logic if border_systems empty
                enemy_systems = []
                
                # Check neighbors of theater systems
                for sys_name in theater.system_names:
                    sys_obj = self.theater_manager._get_system_by_name(sys_name)
                    if not sys_obj: continue
                    
                    # If system is ours, look at neighbors
                    if sys_obj.owner == faction:
                        for n in sys_obj.connections:
                            if n.owner != faction and n.owner != "Neutral":
                                enemy_systems.append((n.name, n.owner))
                    # If system in theater is enemy (invasion), add it
                    elif sys_obj.owner != faction and sys_obj.owner != "Neutral":
                        enemy_systems.append((sys_name, sys_obj.owner))
                
                if enemy_systems:
                    # Pick primary enemy in theater
                    counts = {}
                    for _, owner in enemy_systems:
                        counts[owner] = counts.get(owner, 0) + 1
                    primary_enemy = max(counts, key=counts.get)
                    
                    # [AAA Upgrade] Check Memory Blacklist
                    if hasattr(self.ai, 'memory') and self.ai.memory:
                        if self.ai.memory.is_strategy_blacklisted(faction, sub_goal, primary_enemy, turn):
                             if trace_enabled:
                                 trace["steps"].append({
                                     "step": "blacklist_check",
                                     "rejected_goal": sub_goal,
                                     "rejected_target": primary_enemy,
                                     "reason": "Previous Failure"
                                 })
                             print(f"  > [STRATEGY] {faction} skipping blacklisted strategy {sub_goal} vs {primary_enemy}")
                             sub_goal = "DEFEND" # Fallback
                             sub_target_f = None
                        else:
                             sub_target_f = primary_enemy
                    else:
                        sub_target_f = primary_enemy

                    # [FIX] Proactive War Declaration
                    # "War must be declared BEFORE attacking" - User
                    if sub_target_f and sub_target_f != "Neutral":
                         if hasattr(self.ai.engine, 'diplomacy') and self.ai.engine.diplomacy:
                             dm = self.ai.engine.diplomacy
                             state = dm.treaty_coordinator.get_treaty(faction, sub_target_f)
                             
                             rel = dm.get_relation(faction, sub_target_f)
                             if state != "War" and rel < -25:
                                 # We are planning to attack them. Declare WAR now.
                                 print(f"  > [DIPLOMACY] {faction} declaring PRE-EMPTIVE WAR on {sub_target_f} to authorize Theater Operations (Rel: {rel}).")
                                 # Access internal method to ensure side effects (vassals, cooldowns, logs) trigger
                                 dm._declare_war(faction, sub_target_f, rel, turn, reason="Strategic Theater Target")
                    
                    # Pick Targets
                    sub_targets = [s[0] for s in enemy_systems if s[1] == primary_enemy][:3]
                else:
                    # Expansion?
                    neutrals = [s.name for s in [self.theater_manager._get_system_by_name(x) for x in frontier] if s and s.owner == "Neutral"]
                    # This logic is a bit weak without proper frontier analysis, but acceptable for first pass
                    if neutrals:
                        sub_goal = "EXPAND_FRONTIER"
                        sub_targets = neutrals[:2]
                        
                sub_plans.append({
                    "theater_id": theater.id,
                    "goal": sub_goal,
                    "target_faction": sub_target_f,
                    "target_systems": sub_targets,
                    "priority": theater.strategic_value + theater.threat_score
                })
                
                if trace_enabled:
                    trace["steps"].append({
                        "step": "theater_sub_plan",
                        "theater_id": theater.id,
                        "assigned_doctrine": theater.doctrine,
                        "strategic_value": theater.strategic_value,
                        "sub_goal": sub_goal,
                        "target_faction": sub_target_f
                    })
                
                print(f"  > [THEATER] {faction} :: {theater.name} -> {sub_goal} vs {sub_target_f}")

        # Fallback (No Theaters / New Game)
        else:
             if personality.strategic_doctrine == "AGGRESSIVE_EXPANSION":
                war_goal = "CONQUER_FACTION_X"
                # ... existing legacy target logic ...
                if trace_enabled:
                     trace["steps"].append({
                         "step": "global_goal_selection",
                         "trigger": "fallback_aggressive",
                         "selected_goal": war_goal
                     })

        new_plan = StrategicPlan(
            plan_id=plan_id,
            faction=faction,
            created_turn=turn,
            duration=duration,
            war_goal=war_goal,
            current_phase="EXECUTION",
            sub_plans=sub_plans,
            active_theater_id="GLOBAL",
            persistence_score=10.0 + (personality.determination * 5.0) # [AAA] Personality impacts commitment
        )
                                
        self.active_plans[faction] = new_plan
        print(f"  > [STRATEGY] {faction} formulated GRAND PLAN: {war_goal} with {len(sub_plans)} theater ops.")
        
        # Telemetry
        if hasattr(self.ai, '_log_plan_execution'):
            try:
                self.ai._log_plan_execution(
                    faction, 
                    plan_id, 
                    war_goal, 
                    "CREATED", 
                    [f"Target: {target_f}", f"Diplo: {diplomatic_goal}", f"Duration: {duration}"]
                )
            except Exception as e:
                print(f"CRASH in telemetry.log_event: {e}")
                
        # [PHASE 3] Update Faction Context for Decision Trace
        # This links all subsequent tactical actions (build/recruit/move) to this plan
        f_mgr = self.ai.engine.factions.get(faction)
        if f_mgr:
            f_mgr.strategic_context = {
                "plan_id": plan_id,
                "root_goal": war_goal,
                "doctrine": personality.strategic_doctrine,
                "active_theater": new_plan.active_theater_id,
                "turn": turn
            }

        # [PHASE 6] Commit Trace via DecisionLogger
        if hasattr(self.ai, 'decision_logger') and self.ai.decision_logger:
            trigger_reason = "Situation Analysis"
            if trace_enabled and trace.get("steps"):
                trigger_reason = f"Triggered by {trace['steps'][-1].get('trigger', 'unknown')}"
                
            self.ai.decision_logger.log_decision(
                "STRATEGY",
                faction,
                {
                    "plan_id": plan_id,
                    "duration": duration,
                    "econ_state": current_state.get('econ_health', {}).get('state', 'UNKNOWN'),
                    "theaters_active": len(theaters) if theaters else 0
                },
                [
                    {"action": war_goal, "score": 1.0, "rationale": trigger_reason}
                ],
                war_goal,
                "Plan Created"
            )
            
        return new_plan

    def evaluate_plan_progress(self, faction: str, plan: StrategicPlan):
        """Checks if plan is on track or succeeded."""
        elapsed = self.ai.engine.turn_counter - plan.created_turn
        
        # Check if plan duration expired
        if elapsed >= plan.duration:
            # Calculate Success Score
            score = self.calculate_plan_success_score(faction, plan)
            
            # Record outcome
            f_mgr = self.ai.engine.factions.get(faction)
            if f_mgr:
                outcome = {
                    'plan_id': plan.plan_id,
                    'goal': plan.war_goal,
                    'duration': plan.duration,
                    'success_score': score,
                    'final_metrics': plan.success_metrics
                }
                f_mgr.learning_history['plan_outcomes'].append(outcome)
            
            print(f"  > [STRATEGY] {faction} plan {plan.plan_id} completed. Score: {score}")
            
            # Telemetry
            if hasattr(self.ai, '_log_plan_execution'):
                 self.ai._log_plan_execution(
                    faction, 
                    plan.plan_id, 
                    plan.war_goal, 
                    "COMPLETED", 
                    [f"Score: {score}", f"Result: COMPLETED"],
                    outcome={
                        "score": score,
                        "duration": elapsed,
                        "goal": plan.war_goal,
                        "success": score >= 70
                    }
                )
                
            return "COMPLETED"
            
        # [AAA Upgrade] Deep Trace Reasoning - Persistence Check
        # Decay persistence
        plan.persistence_score -= 1.0
        
        # Check against failure conditions (e.g., losing too many ships/planets)
        # For now, we simulate a 'disaster check' based on recent events (passed in context usually, but we'll assume access)
        # If persistence drops too low and success probability is low -> ABANDON
        
        if plan.persistence_score <= 0:
            # Check if we should abandon
            # This is where we'd check "Current Win Probability"
            # For now, if persistence is 0, we treat it as a potential timeout or forced change
            
            # Record Failure in Memory
            if hasattr(self.ai, 'memory') and self.ai.memory:
                 # Check active theater sub-plans to blacklist specific failures
                 for sp in plan.sub_plans:
                     if sp.get('goal') not in ["DEFEND", "EXPAND_FRONTIER"]:
                         self.ai.memory.record_failure(
                             faction, 
                             sp.get('goal'), 
                             sp.get('target_faction'), 
                             self.ai.engine.turn_counter
                         )
            
            print(f"  > [STRATEGY] {faction} ABANDONING plan {plan.plan_id} (Persistence Depleted)")
            return "FAILED"

        return "IN_PROGRESS"

    def calculate_plan_success_score(self, faction: str, plan: StrategicPlan) -> float:
        """Calculates a 0-100 success score for a completed plan."""
        f_mgr = self.ai.engine.factions.get(faction)
        if not f_mgr: return 0.0
        
        score = 50.0 # Base
        
        if plan.war_goal == "CONQUER_FACTION_X":
            # Check planets gained vs target systems
            captured = 0
            if plan.target_systems:
                for sys_name in plan.target_systems: # These are planet names in create_plan currently?
                     # create_plan puts enemy_planets[:3] into target_systems
                     p = next((p for p in self.ai.engine.all_planets if p.name == sys_name), None)
                     if p and p.owner == faction:
                         captured += 1
                
                if len(plan.target_systems) > 0:
                    ratio = captured / len(plan.target_systems)
                    score = ratio * 100.0
            else:
                 score = 50.0 # Indeterminate

            # Diplomatic Goal Bonus
            if plan.diplomatic_goal == "BETRAY_WEAK_ALLY":
                # Check if betrayal was successful (captured target planets)
                if plan.target_faction and plan.target_systems:
                    start_captured = captured
                    score += (captured / len(plan.target_systems)) * 20  # Bonus for successful betrayal
                    
            elif plan.diplomatic_goal == "COORDINATE_WITH_ALLY":
                # Check if alliance still holds
                if plan.target_faction:
                    stance = self.ai.get_diplomatic_stance(faction, plan.target_faction)
                    if stance in ["ALLIED", "FRIENDLY"]:
                        score += 10  # Bonus for maintaining alliance
                 
        elif plan.war_goal == "RAID_ECONOMY":
            # Check requisition gain logic (metrics not fully populated but we can infer)
            # If we are not bankrupt anymore?
            if f_mgr.requisition > 0: score = 100.0
            else: score = 20.0
            
        elif plan.war_goal == "CONSOLIDATE_HOLDINGS":
            # Check if we lost any planets
            # Hard to track delta without snapshot, but assume stability = success
            score = 80.0
            
        return max(0.0, min(100.0, score))
        
    def should_adapt_strategy(self, faction: str, plan: StrategicPlan) -> bool:
        """Determines if strategy switch needed."""
        # Check contingencies
        return False # Placeholder
