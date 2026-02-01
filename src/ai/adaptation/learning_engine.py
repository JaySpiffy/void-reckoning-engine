import copy
from typing import TYPE_CHECKING, List, Dict, Any, Optional

from src.reporting.telemetry import EventCategory
from universes.base.personality_template import FactionPersonality

if TYPE_CHECKING:
    from src.managers.ai_manager import StrategicAI

class AdaptiveLearningEngine:
    def __init__(self, ai_manager: 'StrategicAI'):
        self.ai = ai_manager

    def update_performance_metrics(self, faction: str):
        """Records current faction state for performance tracking."""
        f_mgr = self.ai.engine.factions[faction]
        owned_planets = len(self.ai.engine.planets_by_faction.get(faction, []))
        total_power = sum(f.power for f in self.ai.engine.fleets if f.faction == faction)
        
        snapshot = {
            'turn': self.ai.engine.turn_counter,
            'planets_owned': owned_planets,
            'total_power': total_power,
            'req_balance': f_mgr.requisition,
            'battles_won': f_mgr.stats.get('turn_battles_won', 0),
            'combat_doctrine': f_mgr.learned_personality.combat_doctrine if f_mgr.learned_personality else "STANDARD",
            'doctrine_intensity': f_mgr.learned_personality.doctrine_intensity if f_mgr.learned_personality else 1.0
        }
        
        f_mgr.learning_history['performance_window'].append(snapshot)
        
        # Keep only last 10 turns
        if len(f_mgr.learning_history['performance_window']) > 10:
            f_mgr.learning_history['performance_window'].pop(0)

    def adapt_personality(self, faction: str, personality: FactionPersonality) -> FactionPersonality:
        """
        Analyzes learning history and mutates personality traits based on ROI.
        Returns modified personality (does not mutate original PERSONALITY_DB).
        """
        f_mgr = self.ai.engine.factions[faction]
        current_turn = self.ai.engine.turn_counter
        
        # Cooldown check
        if current_turn - f_mgr.last_adaptation_turn < f_mgr.adaptation_cooldown:
            return personality
        
        # Calculate performance metrics from last 10 turns
        perf_window = f_mgr.learning_history['performance_window']
        if len(perf_window) < 5:  # Need minimum data
            return personality
        
        # Helper Computations
        def calculate_trend(values):
            if len(values) < 2: return 0
            # Simple slope: (last - first) / length
            return (values[-1] - values[0]) / len(values)

        def calculate_win_rate(battles):
            if not battles: return 0.5
            wins = sum(1 for b in battles if b['won'])
            return wins / len(battles)
            
        def calculate_avg_plan_success(plans):
             if not plans: return 50.0
             total = sum(p['success_score'] for p in plans)
             return total / len(plans)
        
        territory_trend = calculate_trend([p['planets_owned'] for p in perf_window])
        battle_window = f_mgr.learning_history['battle_outcomes'][-10:] if f_mgr.learning_history['battle_outcomes'] else []
        battle_win_rate = calculate_win_rate(battle_window)
        
        econ_trend = calculate_trend([p['req_balance'] for p in perf_window])
        
        plan_window = f_mgr.learning_history['plan_outcomes'][-3:] if f_mgr.learning_history['plan_outcomes'] else []
        plan_success_rate = calculate_avg_plan_success(plan_window)
        
        # Determine if performance is poor
        is_poor = (territory_trend < -0.1 or battle_win_rate < 0.3 or 
                   econ_trend < -500 or plan_success_rate < 40)
        
        if is_poor:
            f_mgr.poor_performance_streak += 1
        else:
            f_mgr.poor_performance_streak = 0
            
        # Trigger adaptation logic
        has_positive_trigger = (battle_win_rate > 0.7 or econ_trend > 500 or plan_success_rate > 80)
        
        should_adapt = False
        if f_mgr.poor_performance_streak >= 10: should_adapt = True
        if has_positive_trigger: should_adapt = True
        
        if not should_adapt:
            return personality
        
        # Create modified personality (copy)
        new_personality = copy.deepcopy(personality)
        mutations = []
        
        # --- Weighted Heuristics System ---
        # Instead of multipliers, we accumulate "pressure" (positive/negative)
        # Pressure is then applied as an additive delta: new = old + (pressure * learning_rate)
        
        # Pressure Accumulators
        pressures = {
            'aggression': 0.0,
            'expansion_bias': 0.0,
            'cohesiveness': 0.0,
            'retreat_threshold': 0.0,
            'planning_horizon': 0.0,
            'doctrine_intensity': 0.0
        }
        
        reasons = []

        # 1. Military Performance Heuristics
        if battle_win_rate < 0.3:
            # Demoralized: Become defensive and cohesive
            pressures['aggression'] -= 0.3
            pressures['cohesiveness'] += 0.2
            reasons.append(f"low_win_rate_{battle_win_rate:.2f}")
        elif battle_win_rate > 0.7:
            # Confident: Become aggressive, refuse to retreat
            pressures['aggression'] += 0.3
            pressures['retreat_threshold'] -= 0.1
            reasons.append(f"high_win_rate_{battle_win_rate:.2f}")
        elif battle_win_rate < 0.5:
             # Slight caution
             pressures['aggression'] -= 0.1

        # 2. Territorial Heuristics
        if territory_trend < -0.1:
            # Losing ground: Hunker down
            pressures['expansion_bias'] -= 0.3
            pressures['cohesiveness'] += 0.2
            pressures['retreat_threshold'] += 0.1 # Retreat earlier to save ships
            reasons.append("losing_territory")
        elif territory_trend > 0.1:
            # Expanding: Maintain momentum
            pressures['expansion_bias'] += 0.1
        
        # 3. Economic Heuristics
        if econ_trend < -500:
            # Crisis: Stop expanding, reduce aggression (save money)
            pressures['expansion_bias'] -= 0.4
            pressures['aggression'] -= 0.2
            reasons.append("economic_crisis")
        elif econ_trend > 500:
            # Boom: Expand more
            pressures['expansion_bias'] += 0.3
            reasons.append("economic_boom")

        # 4. Planning Efficacy
        if plan_success_rate < 30:
            # Plans failing: Shorten horizon, pivot faster
            pressures['planning_horizon'] -= 2.0 # Integer pressure
            reasons.append("plan_failures")
        elif plan_success_rate > 80:
             # Plans working: Think bigger
             pressures['planning_horizon'] += 2.0
             reasons.append("plan_success")

        # 5. Doctrine Tuning (Performance Based)
        if hasattr(self.ai.engine, 'telemetry'):
             doctrine_perf = self.ai.engine.telemetry.get_doctrine_performance(faction, personality.combat_doctrine)
             if doctrine_perf['total_battles'] >= 5:
                 d_win_rate = doctrine_perf['win_rate']
                 if d_win_rate < 0.4:
                     pressures['doctrine_intensity'] -= 0.15
                     reasons.append("doctrine_fail")
                 elif d_win_rate > 0.6:
                     pressures['doctrine_intensity'] += 0.15
                     reasons.append("doctrine_success")

        # Apply Pressures
        LEARNING_RATE = 0.5  # Modulates how fast personality shifts
        
        for trait, pressure in pressures.items():
            if abs(pressure) < 0.01: continue
            
            old_val = getattr(new_personality, trait)
            
            # Special handling for integers
            if trait == 'planning_horizon':
                delta = int(pressure)
                new_val = max(3, min(20, old_val + delta))
            else:
                delta = pressure * LEARNING_RATE
                new_val = old_val + delta
                
                # Clamp floats
                if trait == 'retreat_threshold':
                    new_val = max(0.0, min(1.0, new_val))
                else: # Generic 0.0 - 2.0 range for most traits
                    new_val = max(0.1, min(2.0, new_val))
            
            if new_val != old_val:
                setattr(new_personality, trait, new_val)
                mutations.append((trait, old_val, new_val, ",".join(reasons)))
        
        # Record mutations
        for trait, old_val, new_val, reason in mutations:
            f_mgr.learning_history['personality_mutations'].append({
                'turn': current_turn,
                'trait': trait,
                'old_value': old_val,
                'new_value': new_val,
                'reason': reason
            })
        
        f_mgr.last_adaptation_turn = current_turn
        f_mgr.poor_performance_streak = 0 
        
        # Telemetry
        if hasattr(self.ai.engine, 'telemetry') and mutations:
            self.ai.engine.telemetry.log_event(
                EventCategory.STRATEGY, "personality_adapted",
                {"faction": faction, "mutations": mutations, "trigger": "weighted_heuristics"},
                turn=current_turn
            )
        
        if mutations:
             print(f"  > [LEARNING] {faction} adapted personality. Mutations: {len(mutations)}")
        
        # [PHASE 6] Doctrine Adaptation Trace
        from src.config import logging_config
        if logging_config.LOGGING_FEATURES.get('doctrine_adaptation_tracing', False):
            if hasattr(self.ai.engine.logger, 'campaign'):
                trace_msg = {
                    "event_type": "doctrine_adaptation_trace",
                    "faction": faction,
                    "reasons": reasons,
                    "pressures": pressures,
                    "mutations": mutations,
                    "turn": current_turn
                }
                self.ai.engine.logger.campaign(f"[DOCTRINE] {faction} adapted personality", extra=trace_msg)

        return new_personality

    def export_learning_report(self, faction: str, output_dir: str):
        """Generates detailed learning analytics for a faction."""
        f_mgr = self.ai.engine.factions[faction]
    def generate_counter_mandates(self, faction: str) -> Dict[str, Any]:
        """
        Generates tactical mandates based on opponent profiling.
        Returns: Dict {target_faction: {weight_adjustments}}
        """
        if not hasattr(self.ai, 'opponent_profiler'):
             return {}
             
        mandates = {}
        f_mgr = self.ai.engine.factions[faction]
        history = f_mgr.learning_history.get('battle_outcomes', [])
        
        # Calculate win rates per opponent
        stats = {}
        for b in history:
            opp = b.get('opponent')
            if not opp or opp == "Unknown": continue
            if opp not in stats: stats[opp] = {'wins': 0, 'total': 0}
            stats[opp]['total'] += 1
            if b['won']: stats[opp]['wins'] += 1
            
        # Analysis loop
        for opp_name in f_mgr.known_factions:
            if opp_name == "Neutral": continue
            profile = self.ai.opponent_profiler.get_profile(opp_name)
            
            adjustments = {}
            
            # 1. Performance Based Adaptation (Reactive)
            if opp_name in stats:
                wr = stats[opp_name]['wins'] / stats[opp_name]['total']
                if wr < 0.3:
                    # We are losing badly: Fortify
                    adjustments['defense_bias'] = 1.5
                    adjustments['retreat_threshold'] = 0.8
                elif wr > 0.8:
                    # We are crushing them: Aggression
                    adjustments['inflict_casualties_bias'] = 1.2
                    
            # 2. Profile Based Adaptation (Predictive)
            if profile.aggression > 0.8:
                 # Enemy is a berserker
                 adjustments['threat_weight'] = 2.0 # Prioritize avoiding their main fleet
                 adjustments['defense_weight'] = 1.5 # Defend borders
            
            if profile.expansionism > 0.8:
                 # Enemy is expanding fast -> Containment
                 adjustments['strategic_value_weight'] = 1.5 # Grab choke points
            
            if adjustments:
                mandates[opp_name] = adjustments
                
        return mandates
