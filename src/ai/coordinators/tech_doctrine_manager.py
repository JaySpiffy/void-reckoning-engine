from src.utils.profiler import profile_method
from src.reporting.telemetry import EventCategory
from src.config import logging_config

class TechDoctrineManager:
    """
    Manages hybrid technology research, adaptation queuing, and doctrine-based filtering.
    Extracts tech logic from StrategicAI.
    """
    def __init__(self, engine, ai_manager):
        self.engine = engine
        self.ai = ai_manager
        self.hybrid_tech_manager = self.engine.tech_manager

    @profile_method
    def process_adaptation_requests(self, faction_obj, turn_num):
        """Processes cross-universe tech adaptation queue."""
        if not hasattr(faction_obj, 'pending_adaptations'): return
        
        completed = []
        for adaptation in faction_obj.pending_adaptations:
            if adaptation["status"] == "pending":
                adaptation["turns_left"] -= 1
                if adaptation["turns_left"] <= 0:
                    # Final Unlock
                    tech_id = adaptation["tech_id"]
                    cost = adaptation.get("cost", 0)
                    
                    # Verbatim: Spend intel on completion
                    if faction_obj.intel_points >= cost:
                        faction_obj.intel_points -= cost
                        self.hybrid_tech_manager.unlock_hybrid_tech(faction_obj, tech_id, turn=turn_num)
                        adaptation["status"] = "completed"
                        completed.append(adaptation)
                        
                        # Apply doctrine effects (Step 7)
                        self.apply_doctrine_effects(faction_obj, "complete_adaptation", tech_id)
                        
                        # Log event
                        if faction_obj.learning_history:
                            faction_obj.learning_history.setdefault('adaptations', []).append({
                                'turn': turn_num,
                                'tech_id': tech_id,
                                'result': 'success'
                            })
                        print(f"  > [STRATEGY] {faction_obj.name} completed adaptation: {tech_id} (Spent {cost} IP)")
                    else:
                        # Failed to complete due to lack of intel points (maybe spent elsewhere?)
                        print(f"  > [STRATEGY] {faction_obj.name} failed to complete adaptation {tech_id}: Insufficient Intel ({faction_obj.intel_points}/{cost})")
                        adaptation["status"] = "failed"
                        completed.append(adaptation)
        
        # Cleanup completed
        faction_obj.pending_adaptations = [a for a in faction_obj.pending_adaptations if a["status"] != "completed"]

    def process_intel_driven_research(self, faction_obj, turn_num):
        """AI decision loop for automated hybrid technology research, espionage, and synthesis."""
        if not hasattr(faction_obj, 'intel_points') or faction_obj.intel_points < 500:
            return
            
        current_turn = self.engine.turn_counter
        # Plan Cooldown: Max 1 tech request per 10 turns per faction
        if current_turn - getattr(faction_obj, 'last_hybrid_tech_request_turn', 0) < 10:
            return

        # --- ACTION 1: STEAL TECH (Cost ~2000) ---
        if faction_obj.intel_points > 2000 and self.ai.rng.random() < 0.3:
             # Find viable target (Enemy with more tech)
             target = self._find_espionage_target(faction_obj)
             if target:
                 # Pick a tech we don't have
                 stealable = [t for t in target.unlocked_techs if t not in faction_obj.unlocked_techs and "Hybrid" not in t]
                 if stealable:
                     stolen = self.ai.rng.choice(stealable)
                     faction_obj.intel_points -= 2000
                     self.hybrid_tech_manager.steal_technology(faction_obj, target, stolen)
                     faction_obj.last_hybrid_tech_request_turn = current_turn
                     return # One action per turn

        # --- ACTION 2: SYNTHESIZE TECH (Cost ~5000) ---
        if faction_obj.intel_points > 5000 and self.ai.rng.random() < 0.2:
             # Find two compatible techs
             # Heuristic: Combine Weapon + Defense, or Engine + Weapon
             unlocked = list(faction_obj.unlocked_techs)
             if len(unlocked) >= 2:
                 t1 = self.ai.rng.choice(unlocked)
                 t2 = self.ai.rng.choice(unlocked)
                 if t1 != t2:
                     hybrid_id = self.hybrid_tech_manager.combine_technologies(faction_obj, t1, t2)
                     if hybrid_id:
                         faction_obj.intel_points -= 5000
                         faction_obj.unlock_tech(hybrid_id) # Unlock immediately for now (or queue it?)
                         # TechManager.combine_technologies adds to tree, but doesn't necessarily unlock?
                         # Let's check. It returns ID. We unlock it.
                         faction_obj.last_hybrid_tech_request_turn = current_turn
                         return

        # --- ACTION 3: HYBRID ADAPTATION (Existing) ---
        # 2. Get all available hybrid techs
        available_techs = []
        for tech_id in self.hybrid_tech_manager.hybrid_tech_trees:
            if self.hybrid_tech_manager.is_hybrid_tech_available(faction_obj, tech_id):
                # 5. Apply doctrine filter
                if self.filter_tech_by_doctrine(faction_obj, tech_id, "research"):
                    score = self.evaluate_hybrid_tech_value(faction_obj, tech_id)
                    available_techs.append((score, tech_id))
        
        if available_techs:
            available_techs.sort(key=lambda x: x[0], reverse=True)
            best_score, best_tech_id = available_techs[0]
            
            if best_score > 5.0:
                if self.request_adaptation(faction_obj, best_tech_id):
                    faction_obj.last_hybrid_tech_request_turn = current_turn

    def _find_espionage_target(self, faction_obj):
        """Finds a suitable enemy faction to steal from."""
        potential_targets = []
        for other_name, other_f in self.engine.factions.items():
            if other_name == faction_obj.name: continue
            
            # Check relation (War only? or anyone?)
            # User said "stealing", implies hostile or covert.
            # Simplified: Anyone with more techs
            if len(other_f.unlocked_techs) > len(faction_obj.unlocked_techs):
                potential_targets.append(other_f)
                
        if potential_targets:
            return self.ai.rng.choice(potential_targets)
        return None

    def evaluate_hybrid_tech_value(self, faction_obj, tech_id):
        """Scores hybrid tech based on strategic value and cost."""
        tech_values = self.hybrid_tech_manager.analyze_tech_tree(faction_obj.name)
        base_value = tech_values.get(tech_id, 0.0)
        
        reqs = self.hybrid_tech_manager.get_hybrid_tech_requirements(tech_id)
        intel_cost = reqs.get("intel_cost", 5000)
        
        if intel_cost == 0: return 0.0
        
        # Simple Priority Score: Value / Cost Ratio
        score = (base_value * 1000) / (intel_cost / 100)
        return score

    def filter_tech_by_doctrine(self, faction_obj, tech_id, acquisition_type="research"):
        """Filters tech acquisition based on faction doctrine tags."""
        personality = self.ai.personality_manager.get_faction_personality(faction_obj.name)
        if not personality: return True  # Default allow
        
        doctrine = getattr(personality, 'tech_doctrine', 'PRAGMATIC')
        
        # Get tech metadata
        tech_data = self.hybrid_tech_manager.hybrid_tech_trees.get(tech_id, {})
        
        # Doctrine Logic
        if doctrine == "RADICAL":
            return True  # Always accept
        elif doctrine == "PURITAN":
            if acquisition_type in ["theft", "salvage"]:
                return False  # Reject alien tech
            return False # Reject hybrid research for Puritans
        elif doctrine == "PRAGMATIC":
            # Accept if strategic value > 3.0
            value = self.evaluate_hybrid_tech_value(faction_obj, tech_id)
            return value > 3.0
        elif doctrine == "XENOPHOBIC":
            return False  # Reject all cross-universe tech
        elif doctrine == "ADAPTIVE":
            # Accept from allies/neutrals, reject from enemies
            if acquisition_type == "share":
                return True
            elif acquisition_type in ["theft", "salvage"]:
                # Check source faction relationship
                source_faction = tech_data.get("source_faction")
                if source_faction:
                    treaty = "Peace"  # Default neutral
                    if (hasattr(self.engine, 'diplomacy') and 
                        self.engine.diplomacy and 
                        hasattr(self.engine.diplomacy, 'treaties')):
                        treaty = self.engine.diplomacy.treaties.get(faction_obj.name, {}).get(source_faction, "Peace")
                    return treaty != "War"
            return True
        
        return True  # Default fallback

    def apply_doctrine_effects(self, faction_obj, effect_type, tech_id):
        """Applies morale, research, or diplomatic effects based on doctrine."""
        personality = self.ai.personality_manager.get_faction_personality(faction_obj.name)
        if not personality: return
        
        doctrine = getattr(personality, 'tech_doctrine', 'PRAGMATIC')

        if effect_type == "complete_adaptation":
            if doctrine == "RADICAL":
                # +10% research speed
                old_mult = getattr(faction_obj, 'research_multiplier', 1.0)
                faction_obj.research_multiplier = old_mult * 1.1
                
        elif effect_type == "reject_alien_tech":
            if doctrine == "PURITAN":
                # +5 morale when destroying alien tech
                if hasattr(self.engine, 'morale_manager'):
                    self.engine.morale_manager.modify_faction_morale(faction_obj.name, 5, reason=f"Rejected alien tech {tech_id}")
            
            elif doctrine == "ADAPTIVE" and effect_type == "combat_success":
                 # +5% intel gain from combat with alien tech users (Handled in earn_intel potentially)
                 pass

        # Telemetry
        if hasattr(self.engine, 'telemetry'):
            self.engine.telemetry.log_event(
                EventCategory.TECHNOLOGY, "doctrine_effect",
                {"faction": faction_obj.name, "doctrine": doctrine, "effect": effect_type, "tech_id": tech_id},
                turn=self.engine.turn_counter,
                faction=faction_obj.name
            )

    def request_adaptation(self, faction_obj, tech_id):
        """Validates and queues a hybrid tech adaptation."""
        if not self.hybrid_tech_manager.is_hybrid_tech_available(faction_obj, tech_id):
            return False
            
        reqs = self.hybrid_tech_manager.get_hybrid_tech_requirements(tech_id)
        cost = reqs["intel_cost"]
        
        # Verbatim: Queue adaptation requests using intel cost and prereqs (don't spend yet)
        if faction_obj.intel_points >= cost:
            faction_obj.queue_adaptation(tech_id, cost, reqs["research_turns"])
            print(f"  > [STRATEGY] {faction_obj.name} queued adaptation for {tech_id} (Cost: {cost}, Turns: {reqs['research_turns']})")
            return True
        return False

    def log_doctrine_effectiveness(self, faction_name: str):
        """Logs the effectiveness of the current doctrine (Metric #2)."""
        if not hasattr(self.engine, 'telemetry') or not self.engine.telemetry:
            return
            
        f_obj = self.engine.get_faction(faction_name)
        if not f_obj: return
        
        personality = self.ai.personality_manager.get_faction_personality(faction_name)
        doctrine = getattr(personality, 'tech_doctrine', 'PRAGMATIC')
        
        # Calculate win rate from stats
        battles = f_obj.stats.get("battles_won", 0) + f_obj.stats.get("battles_lost", 0)
        win_rate = f_obj.stats.get("battles_won", 0) / battles if battles > 0 else 0.0
        
        # Get Avg CER (Combat Effectiveness Ratio) from telemetry performance cache if available
        cer_avg = 0.0
        if hasattr(self.engine.telemetry, 'battle_performance'):
            perf = self.engine.telemetry.battle_performance.get(faction_name, [])
            if perf:
                cer_avg = sum(p.get('cer', 0) for p in perf) / len(perf)

        self.engine.telemetry.log_event(
            EventCategory.DOCTRINE,
            "doctrine_effectiveness",
            {
                "faction": faction_name,
                "turn": self.engine.turn_counter,
                "doctrine": doctrine,
                "metrics": {
                    "win_rate": win_rate,
                    "avg_cer": cer_avg,
                    "planets_controlled": len(self.engine.planets_by_faction.get(faction_name, [])),
                    "techs_unlocked": len(f_obj.unlocked_techs)
                },
                "effectiveness_score": (win_rate * 50) + (min(cer_avg, 2.0) * 25) # Simplistic score
            },
            turn=self.engine.turn_counter,
            faction=faction_name
        )
