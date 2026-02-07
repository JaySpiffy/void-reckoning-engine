from typing import Any, Dict, List
import copy
from src.ai.strategic_planner import StrategicPlan
from src.utils.profiler import profile_method

class StrategyOrchestrator:
    def __init__(self, ai_manager: Any):
        self.ai = ai_manager
        self.engine = ai_manager.engine

    def process_turn(self):
        """Entry point for the AI turn, orchestrating all factions."""
        # Ensure personalities are loaded
        if not self.ai.personality_manager.personality_loader:
            from src.core.config import ACTIVE_UNIVERSE
            self.ai.personality_manager.load_personalities(ACTIVE_UNIVERSE or "void_reckoning")

        # 1. Performance Optimization: Build Turn Cache
        self.ai.build_turn_cache()
        
        for faction in sorted(list(self.engine.factions.keys())):
            if faction == "Neutral": continue
            
            f_obj = self.engine.factions[faction]
            
            # Learning Integration
            self.ai.learning_engine.update_performance_metrics(faction)
            
            # Process Hybrid Tech Adaptations
            self.ai.tech_doctrine_manager.process_adaptation_requests(f_obj, self.engine.turn_counter)
            
            self.process_faction_strategy(faction)
            
            # Intelligence & Diplomacy
            self.engine.intelligence_manager.update_spy_networks(faction)
            self.ai.intelligence_coordinator.process_espionage_decisions(f_obj)
            
            self.ai.proactive_diplomacy.process_turn(faction)
            self.ai.coalition_builder.process_turn(faction)
            
            self.ai.check_for_treaty_and_coalition_obligations(faction)
            
            # Innovation Cycle (Ship/Weapon Evolution)
            if self.engine.turn_counter % 25 == 0 or (f_obj.requisition > 100000 and len(f_obj.unlocked_techs) > 20):
                self.ai.production_planner.process_innovation_cycle(faction)
                
            # Composition Optimization (Adaptive Counters)
            if self.engine.turn_counter % 10 == 0:
                 self._optimize_composition(faction)
            
        # Intelligence sharing phase
        for faction in list(self.engine.factions.keys()):
            if faction == "Neutral": continue
            self.share_intelligence_with_allies(faction)
            
            # Research & Espionage Logic
            self.ai.economic_engine.evaluate_research_priorities(faction)
            self.ai.intelligence_coordinator.evaluate_espionage_targets(faction)
            self.ai.tech_doctrine_manager.process_intel_driven_research(self.engine.factions[faction], self.engine.turn_counter)

    def _optimize_composition(self, faction: str):
         """Analyzes threats and recommends doctrine adjustments."""
         threats = self.ai.expansion_logic.predict_enemy_threats(faction)
         if threats:
              primary_threat_faction = threats[0]["fleet"].faction
              profile = self.ai.composition_optimizer.analyze_enemy_composition(primary_threat_faction)
              doctrine = self.ai.composition_optimizer.recommend_counter_doctrine(profile)
              self.ai.composition_optimizer.adjust_production_priorities(faction, doctrine)

    @profile_method('ai_strategy_time')
    def process_faction_strategy(self, faction: str):
        """Main entry point for per-faction strategy logic."""
        if self.engine.turn_counter % 10 == 0:
             self._log_strategic_deployment(faction)
             if self.engine.diplomacy:
                 self.log_alliance_stats()

        f_mgr = self.engine.get_faction(faction)
        if not f_mgr: return
        
        owned_planets = self.engine.planets_by_faction.get(faction, [])
        if not owned_planets: return
        
        # 1. Context & Personality
        personality = self.ai._initialize_strategy_context(faction, f_mgr)
        
        # [LEARNING] Generate Counter-Mandates
        if not hasattr(self.ai, 'turn_cache'): self.ai.turn_cache = {}
        if 'mandates' not in self.ai.turn_cache: self.ai.turn_cache['mandates'] = {}
        
        mandates = self.ai.learning_engine.generate_counter_mandates(faction)
        self.ai.turn_cache['mandates'][faction] = mandates
        
        # 2. Strategic Planning
        self.ai._update_operational_plan(faction, f_mgr, personality)
        strategic_plan = f_mgr.active_strategic_plan
        
        # Calculate Context & Weights
        econ_health = self.ai.assess_economic_health(faction)
        context = self.ai._determine_strategic_context(faction, f_mgr, econ_health['state'])
        weights = self.ai.dynamic_weights.get_weights(context, personality)
        
        # 3. Execution Pipeline
        self._execute_strategy_pipeline(faction, f_mgr, personality, strategic_plan, owned_planets, weights)

        # 4. [Phase 22] Process Sieges & Invasions
        self.ai._process_sieges(faction)

    def _execute_strategy_pipeline(self, faction: str, f_mgr: Any, personality: Any, strategic_plan: Any, owned_planets: list, weights: dict):
        """Executes sequential strategy phases: Economic, Defensive, Offensive, and Research."""
        threatened_planets = [p for p in owned_planets if any(ag.faction != faction for ag in p.armies if not ag.is_destroyed)]
        econ_health = self.ai.assess_economic_health(faction)
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
        self.ai.economic_strategy.handle_economic_restraint(faction, econ_state)
        self.ai._manage_task_forces(faction)
        
        # --- PHASE: FLEET ASSIGNMENT ---
        idle_fleets = self.ai._get_idle_fleets(faction)
        idle_fleets = self.ai.tf_manager.split_overlarge_fleets(faction, idle_fleets)
        available_fleets = self.ai._get_available_fleets(faction, idle_fleets)
        
        if self.engine.turn_counter > 10:
             self.ai.tf_manager.form_construction_task_force(faction, available_fleets)
        
        # --- PHASE: DEFENSIVE & RESERVES ---
        is_bankrupt = econ_state == "BANKRUPT"
        available_fleets = self.ai.defensive_strategy.manage_strategic_reserves(faction, available_fleets, threatened_planets, is_bankrupt)
        self.ai.concentrate_forces(faction)
        
        zones = self.ai.expansion_logic.classify_defense_zones(faction) if self.engine.diplomacy else {} 
        available_fleets = self.ai.defensive_strategy.handle_defensive_priority(faction, available_fleets, threatened_planets, personality, econ_health, zones)

        # --- PHASE: INTERCEPTION ---
        available_fleets = self.ai.interception_strategy.handle_predictive_interception(faction, available_fleets, personality, econ_state, econ_health['upkeep'], econ_health['income'], zones)

        # --- PHASE: OFFENSIVE EXPANSION ---
        self.ai.expansion_logic.handle_expansion_logic(faction, f_mgr, available_fleets, personality, econ_state, owned_planets, expansion_bias, weights)
        
        # --- PHASE: RESEARCH ---
        self.ai.process_standard_research(faction, f_mgr)
        self.ai.process_intel_driven_research(f_mgr, self.engine.turn_counter)
        
        # --- POST-STRATEGY OPS ---
        self._handle_post_strategy_ops(faction, available_fleets, f_mgr, personality, econ_health, strategic_plan)

    def _initialize_strategy_context(self, faction: str, f_mgr: Any) -> Any:
        """Loads and adapts faction personality and strategic posture."""
        personality = self.ai.get_faction_personality(faction)

        # Adaptive Check (Every 3 turns)
        if self.engine.turn_counter % 3 == 0:
            self.ai.posture_manager.update_faction_posture(faction)
        
        # Apply adaptive learning
        personality = self.ai.learning_engine.adapt_personality(faction, personality)
        
        # [QUIRK] Chaos Randomness (Phase 5)
        if faction == "Chaos":
             import random
             if random.random() < 0.2:
                  personality.aggression += 0.5
             elif random.random() < 0.1:
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
        threats = self.ai.turn_cache.get("threats_by_faction", {}).get(faction, [])
        if not threats:
            threats = self.ai.expansion_logic.predict_enemy_threats(faction)
            
        if threats:
            return "THREATENED"
        
        # 6. Expansion
        if f_mgr.strategic_posture == "EXPANSION":
            return "EXPANSION"
            
        return "DEFAULT"

    def _update_operational_plan(self, faction: str, f_mgr: Any, personality: Any):
        """Updates the high-level strategic plan and checks for failures."""
        # [LEARNING] Check for Target Failures before planning new ones
        self.ai.check_target_failures(faction)
        
        # [PHASE 7] VASSAL ALIGNMENT
        if self.engine.diplomacy:
            treaties = self.engine.diplomacy.get_treaties(faction)
            overlord = next((other for other, state in treaties.items() if state == "Overlord"), None)
            
            if overlord:
                overlord_mgr = self.engine.get_faction(overlord)
                if overlord_mgr and overlord_mgr.active_strategic_plan:
                    if not f_mgr.active_strategic_plan or f_mgr.active_strategic_plan.plan_id != overlord_mgr.active_strategic_plan.plan_id:
                        import copy
                        f_mgr.active_strategic_plan = copy.deepcopy(overlord_mgr.active_strategic_plan)
                        if self.engine.logger:
                            self.engine.logger.strategy(f"[VASSAL ALIGNMENT] {faction} adopting Overlord {overlord}'s strategic plan.")
                    return # Skip normal planning
        
        econ_health = self.ai.assess_economic_health(faction)
        # New: Determine Context and Weights
        context = self._determine_strategic_context(faction, f_mgr, econ_health['state'])
        weights = self.ai.dynamic_weights.get_weights(context, personality)
        
        current_state = {
            'econ_health': {'state': econ_health['state']},
            'weights': weights
        }
        
        if not f_mgr.active_strategic_plan or \
           self.ai.planner.evaluate_plan_progress(faction, f_mgr.active_strategic_plan) == "COMPLETED":
             f_mgr.active_strategic_plan = self.ai.planner.create_plan(faction, personality, current_state)

    def _manage_task_forces(self, faction: str):
        self.ai.tf_manager.ensure_faction_list(faction)
        
        # Log Strategic Deployment (Metric #4)
        if self.engine.turn_counter % 5 == 0:
            self._log_strategic_deployment(faction)

    def _get_idle_fleets(self, faction: str) -> List[Any]:
        # Phase 17: Filter out ENGAGED fleets (they are busy fighting)
        return [f for f in self.engine.fleets if f.faction == faction and f.destination is None and not getattr(f, 'is_engaged', False)]

    def _get_available_fleets(self, faction: str, idle_fleets: List[Any]) -> List[Any]:
        active_fleets = []
        for tf in self.ai.task_forces.get(faction, []):
            active_fleets.extend(tf.fleets)
        return [f for f in idle_fleets if f not in active_fleets]

    def _handle_post_strategy_ops(self, faction: str, available_fleets: List[Any], f_mgr: Any, personality: Any, econ_health: dict, strategic_plan: Any):
        """Handles post-strategy operations: Task Force cleaning, patrols, and retreats."""
        self.ai.tf_manager.manage_task_forces_lifecycle(faction, available_fleets, f_mgr, personality, econ_health, strategic_plan)

        # 1.5 Empire-wide Fleet Consolidation (Idle Fleets)
        self.consolidate_available_fleets(faction, available_fleets)

        # 2. Legacy Random Move for Leftovers (Patrols)
        import random
        for f in available_fleets:
            if random.random() < 0.1:
                if hasattr(f.location, 'system') and f.location.system.connections:
                        dest_sys = random.choice(f.location.system.connections)
                        if dest_sys.planets:
                            f.move_to(dest_sys.planets[0], engine=self.engine)
                elif hasattr(f.location, 'metadata') and 'target_system' in f.location.metadata:
                    if hasattr(f.location.metadata['target_system'], 'planets'):
                         f.move_to(f.location.metadata['target_system'].planets[0], engine=self.engine)

    def consolidate_available_fleets(self, faction: str, available_fleets: List[Any]) -> None:
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
                    primary.merge_with(secondary)
                else:
                    primary = secondary

    def _log_strategic_deployment(self, faction: str):
        """Logs strategic deployment metrics (Metric #4)."""
        if not hasattr(self.engine, 'telemetry') or not self.engine.telemetry: return
        from src.reporting.telemetry import EventCategory
        
        # 1. Zone Coverage
        zones = self.ai.classify_defense_zones(faction) if self.engine.diplomacy else {}
        total_planets = len(self.engine.planets_by_faction.get(faction, []))
        
        # Ratio of TaskForces to Owned Planets
        tf_count = len(self.ai.task_forces.get(faction, []))
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
        if faction in self.ai.task_forces:
             for tf in self.ai.task_forces[faction]:
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


    def check_for_treaty_and_coalition_obligations(self, faction: str):
        """Checks active treaties (Defensive Pacts) and Coalition memberships."""
        if not self.engine.diplomacy: return
        diplomacy = self.engine.diplomacy
        treaty_mgr = diplomacy.treaty_coordinator
        
        # 1. Check Defensive Pacts
        allies = [other for other, treaty in treaty_mgr.active_treaties.get(faction, {}).items() if treaty == "Defensive Pact"]
        
        # Are any allies at war?
        for ally in allies:
             for (attacker, defender), start_turn in diplomacy.active_wars.items():
                 if defender == ally:
                      # Our ally is being attacked! Simplified for now.
                      pass

    def evaluate_offensive_targets(self, faction: str, candidates: List[Any]) -> List[Any]:
        """Filters offensive targets based on diplomatic status."""
        filtered = []
        diplomacy = getattr(self.engine, 'diplomacy', None)
        personality = self.ai.get_faction_personality(faction)
        betrayal_threshold = 0.8
        
        for target in candidates:
             owner = target.owner
             if owner == "Neutral" or owner == faction: 
                 filtered.append(target)
                 continue
                 
             if diplomacy:
                 treaty = diplomacy.treaty_coordinator.get_treaty(faction, owner)
                 if treaty in ["Non-Aggression Pact", "Defensive Pact", "Alliance"]:
                     if personality.honor > betrayal_threshold: continue
                     if personality.aggression < 0.9: continue
                         
             filtered.append(target)
        return filtered

    def share_intelligence_with_allies(self, faction: str):
        """Synchronize intelligence_memory and known_planets with allied factions."""
        if not self.engine.diplomacy: return
        f_mgr = self.engine.factions.get(faction)
        if not f_mgr: return
        
        allies = [o for o in self.engine.factions if o != faction and o != "Neutral" and 
                  self.ai.get_diplomatic_stance(faction, o) in ["ALLIED", "FRIENDLY"]]
                
        if not allies: return
        
        for ally in allies:
             ally_mgr = self.engine.factions.get(ally)
             if not ally_mgr: continue
             
             # Share Known Planets
             new_mine = ally_mgr.known_planets - f_mgr.known_planets
             new_theirs = f_mgr.known_planets - ally_mgr.known_planets
             if new_mine: f_mgr.known_planets.update(new_mine)
             if new_theirs: ally_mgr.known_planets.update(new_theirs)
                 
             if (new_mine or new_theirs) and self.engine.diplomacy:
                 self.engine.diplomacy.modify_relation(faction, ally, 2, symmetric=True)
                 
             # Share recent intelligence
             current_turn = self.engine.turn_counter
             shared_count = 0
             for p_name, info in f_mgr.intelligence_memory.items():
                 age = current_turn - info.get('last_seen_turn', 0)
                 if age <= 3:
                     ally_info = ally_mgr.intelligence_memory.get(p_name)
                     ally_age = current_turn - ally_info.get('last_seen_turn', 0) if ally_info else 999
                     if ally_age > age:
                         ally_mgr.intelligence_memory[p_name] = info.copy()
                         shared_count += 1
             
             if shared_count > 0:
                 self._track_alliance_stat(faction, ally, "shared_intelligence_count", shared_count)

    def _track_alliance_stat(self, f1, f2, stat, amount=1):
        pair_key = "_".join(sorted([f1, f2]))
        if pair_key not in self.ai.alliance_stats:
            self.ai.alliance_stats[pair_key] = {"shared_intelligence_count": 0, "coordinated_attacks": 0, "members": [f1, f2]}
        self.ai.alliance_stats[pair_key][stat] += amount

    def log_alliance_stats(self):
        """Logs alliance effectiveness."""
        if not hasattr(self.engine, 'telemetry') or not self.engine.telemetry: return
        from src.reporting.telemetry import EventCategory
        
        for pool_id, stats in self.ai.alliance_stats.items():
            benefit_score = stats["shared_intelligence_count"] * 0.5 + stats["coordinated_attacks"] * 5
            self.engine.telemetry.log_event(
                EventCategory.DIPLOMACY, "alliance_effectiveness",
                {
                    "alliance_id": pool_id, "members": stats["members"],
                    "turn": self.engine.turn_counter,
                    "metrics": stats.copy(),
                    "stability_score": 100, "mutual_benefit_score": benefit_score
                },
                turn=self.engine.turn_counter
            )
