import random
from typing import List, Any, TYPE_CHECKING
from src.models.fleet import Fleet, TaskForce
from src.models.faction import Faction

if TYPE_CHECKING:
    from src.managers.ai_manager import StrategicAI
    from src.managers.ai_manager import FactionPersonality

class OffensiveStrategy:
    """
    Handles offensive strategic decisions, including expansion targeting and raiding.
    """
    def __init__(self, ai_manager: 'StrategicAI'):
        self.ai = ai_manager

    def handle_offensive_expansion(self, faction: str, available_fleets: List[Fleet], f_mgr: Any, personality: 'FactionPersonality', econ_state: str, owned_planets: List[Any], expansion_bias: float, weights: dict = None):
        """
        Calculates expansion targets and forms offensive task forces.
        """
        # Check Personality: Expansion Bias (Modified by Economy)
        wants_to_expand = random.random() < expansion_bias
        
        if econ_state == "BANKRUPT":
            # 50% chance to launch a raid if fleets available
            if len(available_fleets) >= 2 and random.random() < 0.5:
                # Limit 1 raid per turn?
                if not any(tf.is_raid for tf in self.ai.task_forces[faction]):
                    self.ai.form_raiding_task_force(faction, available_fleets)
            return # Even if we didn't raid, don't expand normally

        # HUNTER-KILLER / PURSUIT LOGIC (Step 6)
        # Prioritize finishing off wounded/retreating enemies before expansion
        self.handle_pursuit(faction, available_fleets, f_mgr, owned_planets)

        is_bankrupt = econ_state == "BANKRUPT" # Redundant but for clarity

        if not is_bankrupt and len(available_fleets) >= 1 and wants_to_expand:
            self.ai.tf_counter += 1
            new_tf = TaskForce(f"TF-{self.ai.tf_counter}", faction)
            
            # Feature 110: Assign Combat Doctrine
            new_tf.faction_combat_doctrine = personality.combat_doctrine
            new_tf.doctrine_intensity = personality.doctrine_intensity
            new_tf.mission_role = "INVASION" # Default for expansion
            
            # [QUIRK] Tier/Recruitment Bonuses
            # Higher resource tier = more willing to expend fleets
            tier = personality.quirks.get("tier", 3)
            recruitment_mult = personality.quirks.get("navy_recruitment_mult", 1.0)
            
            # If Tier 1 (Super/Great Power), we are more aggressive
            if tier <= 2:
                new_tf.doctrine_intensity += 0.2
            
            # Recruitment Mult affects fleet size preferences?
            # For now, just store it on TF for BattleManager
            new_tf.retreat_threshold = personality.retreat_threshold # Pass to battle

            
            # 1.1 Calculate "Center of Power" for Distance Weighting
            # Use HQ if available, else average of owned planets
            hq = next((p for p in owned_planets if "Capital" in [n.type for n in p.provinces]), owned_planets[0])
            home_node = hq.system
            
            # Pick High-Value Target (ONLY from known_planets)
            # 1.2 Select Targets: Merge Enemies and Colonization Options
            # This allows the AI to choose between expanding peacefully or attacking based on score.
            col_cost = self.ai.engine.game_config.get("economy", {}).get("colonization_cost", 1000) # Default 1000
            # Relaxed Check: Allow colonization if we have at least 200 req (even if cost is 1000, go into debt)
            can_colonize = f_mgr.requisition >= 200 
            
            candidates = []
            for p in self.ai.engine.all_planets:
                if p.name not in f_mgr.known_planets: continue
                if p.owner == faction: continue
                
                # Neutral: Check colonization capability
                if p.owner == "Neutral":
                    if can_colonize: candidates.append(p)
                    
                # Enemy: Check Diplomatic Validity
                elif self.ai.is_valid_target(faction, p.owner):
                    candidates.append(p)
            
            # --- PHASE 64: PROXIMITY & STOCHASTIC TARGETING ---
            target = None
            if candidates:
                scored_targets = []
                for p in candidates:

                    
                    # --- CACHED SCORING CALL ---
                    score, rationale = self.ai.calculate_expansion_target_score(
                        p.name, faction, home_node.x, home_node.y, 
                        personality.name, econ_state, self.ai.engine.turn_counter,
                        weights=weights,
                        include_rationale=True
                    )
                    if self.ai.engine.logger:
                        self.ai.engine.logger.debug(f"[{faction}] Scored {p.name} for expansion: {score:.2f}")
                    
                    scored_targets.append((p, score, rationale))
                
                # Sort by score
                scored_targets.sort(key=lambda x: x[1], reverse=True)

                # [PHASE 6] Decision Logging ($DEEP_TRACER)
                if self.ai.decision_logger:
                    # Prep options for logging
                    options = []
                    for p, s, r in scored_targets[:3]: # Top 3
                        options.append({
                            "action": f"EXPAND_TO:{p.name}",
                            "score": s,
                            "rationale": r
                        })
                    
                    # Context for the decision
                    context = {
                        "available_fleets": len(available_fleets),
                        "econ_state": econ_state,
                        "expansion_bias": expansion_bias,
                        "personality": personality.name
                    }
                    
                    self.ai.decision_logger.log_decision(
                        decision_type="FLEET_MOVE",
                        actor_id=faction,
                        context=context,
                        options=options,
                        selected_action=f"EXPAND_TO:{scored_targets[0][0].name}" if scored_targets else "None",
                        outcome="Planning"
                    )
                
                # Weighted Selection (Phase 64c)
                # Select target probability proportional to score
                total_score = sum(s for p, s, r in scored_targets)
                if total_score > 0:
                    pick_val = random.uniform(0, total_score)
                    current = 0
                    for p, s, r in scored_targets:
                        current += s
                        if current >= pick_val:
                            target = p
                            break
                
                # Fallback
                if not target and scored_targets: target = scored_targets[0][0]
                
                if target:
                    new_tf.target = target
                    
                    # [LEARNING] Track Target Selection
                    f_mgr.learning_history['target_outcomes'].append({
                        'target_name': target.name,
                        'attempted_turn': self.ai.engine.turn_counter,
                        'captured_turn': None,  # Updated when captured
                        'estimated_cost': 0, # Difficult to calc upfront
                        'estimated_value': getattr(target, 'income_req', 100),
                        'actual_cost': 0,
                        'success': False
                    })
                    
                    # Phase 81: Composition & Strategy Selection
                    # Determine ideal composition based on target
                    # (Note: Logic repeated from original method, can be simplified or extracted further if needed)
                    is_capital = "Capital" in [n.type for n in target.provinces]
                    ideal_comp = "BALANCED"
                    
                    if is_capital:
                        ideal_comp = "ASSAULT"
                        new_tf.mission_role = "ASSAULT"
                    
                    required = 3
                    if is_capital: required = 6
                    
                    
                    # [INTEL] Calculate needed power based on last known strength
                    intel = self.ai.engine.intel_manager.get_cached_intel(faction, target.name, self.ai.engine.turn_counter)
                    # intel = (last_seen_turn, strength, income, threat, last_owner)
                    estimated_strength = intel[1]
                    
                    # Apply aggression modifier
                    aggression = personality.aggression
                    # [PHASE 12] DOOMSTACK LOGIC: significantly higher threshold (2000 vs 200)
                    # Lower floor for Neutral planets to allow early colonization
                    power_floor = 200 if target.owner == "Neutral" else 2000
                    needed_power = max(power_floor, estimated_strength * (1.5 / max(0.1, aggression)))
                    
                    chosen_fleets = []
                    current_power = 0
                    
                    if current_power < needed_power and available_fleets:
                        # Check total potential power if we used ALL available fleets
                        potential_power = current_power + sum(f.power for f in available_fleets)
                        if potential_power < needed_power:
                            if self.ai.engine.logger:
                                self.ai.engine.logger.debug(f"[{faction}] Skipping {target.name}: Need {needed_power} power, but only have {potential_power} available.")
                            return
                    
                    # Phase 22: Selective Fleet Assignment (Logistics Aware)
                    if new_tf.mission_role == "INVASION":
                        # Ensure we have at least one transport if possible
                        # Sort by capacity to get the best one
                        transport_fleets = sorted([f for f in available_fleets if f.transport_capacity > 0], 
                                                key=lambda x: x.transport_capacity, reverse=True)
                        if transport_fleets:
                            f = transport_fleets[0]
                            new_tf.add_fleet(f)
                            chosen_fleets.append(f)
                            current_power += f.power
                            available_fleets.remove(f)
                    
                    # Fill remaining slots with strongest available
                    available_fleets.sort(key=lambda x: x.power, reverse=True)
                    while len(chosen_fleets) < required and available_fleets:
                        f = available_fleets.pop(0)
                        new_tf.add_fleet(f)
                        chosen_fleets.append(f)
                        current_power += f.power
                    
                    if chosen_fleets:
                        # Phase 9 Fix: No more instant teleport-merging.
                        # Instead, we set the state to RALLYING and let the fleets move to a rally point.
                        
                        # Determine Rally Point (Use location of strongest fleet or closest to target?)
                        # Simple heuristic: Use location of the strongest fleet to minimize its movement.
                        chosen_fleets.sort(key=lambda x: x.power, reverse=True)
                        flagship = chosen_fleets[0]
                        rally_point = flagship.location
                        
                        # Add all fleets to TF
                        for f in chosen_fleets:
                            new_tf.add_fleet(f)
                            
                        new_tf.rally_point = rally_point
                        new_tf.state = "RALLYING" # Triggers the merge-on-arrival logic we added to TaskForce
                        
                        self.ai.task_forces[faction].append(new_tf)
                        
                        # Remove used fleets from pool
                        for f in chosen_fleets:
                            if f in available_fleets:
                                available_fleets.remove(f)
                       
                        if self.ai.engine.logger:
                            op_type = "COLONIZATION" if target.owner == "Neutral" else "CONQUEST"
                            self.ai.engine.logger.campaign(f"[{faction}] Formulated {op_type} plan. RALLYING {len(chosen_fleets)} fleets at {rally_point.name} before striking {target.name}")

    def handle_pursuit(self, faction: str, available_fleets: List[Fleet], f_mgr: Any, owned_planets: List[Any]):
        """
        [HUNTER-KILLER] 
        Scanning for vulnerable enemy fleets (retreated, weak) and dispatching interceptors.
        Run BEFORE expansion to prioritize cleaning up threats.
        """
        if not available_fleets: return

        # 1. Identify Enemies
        enemies = []
        diplomacy = getattr(self.ai.engine, 'diplomacy', None)
        if diplomacy:
             enemies = diplomacy.get_enemies(faction)
        
        if not enemies: return # Peaceful or no enemies

        # 2. Scan Visible Space for Vulnerable Targets
        # Use turn cache if available for performance? 
        # turn_cache["fleets_by_loc"] gives location->fleets.
        # But we need to scan known locations.
        # Better: Iterate all fleets and check visibility + faction.
        # O(N) where N is total fleets. N ~ 300-3000. Fast enough.
        
        visible_planets = getattr(f_mgr, 'visible_planets', set())
        
        candidates = []
        for f in self.ai.engine.fleets:
            if getattr(f, 'is_destroyed', False): continue
            if f.faction not in enemies: continue
            
            # Check Visibility
            loc_name = getattr(f.location, 'name', None)
            if not loc_name or loc_name not in visible_planets: continue
            
            # Check Vulnerability
            is_vulnerable = False
            reason = ""
            
            # A. RETREATED RECENTLY (High Priority)
            if getattr(f, 'has_retreated_this_turn', False):
                is_vulnerable = True
                reason = "RETREATED"
            
            # B. WOUNDED (Medium Priority)
            # Assuming getting current HP requires checking units.
            # Approximate with power? No.
            # Let's check power threshold for "Weakness"
            elif f.power < 500 and f.faction != "Neutral": # Ignore neutral scouts
                 # Only vulnerable if we have something stronger nearby
                 is_vulnerable = True
                 reason = "WEAK"
            
            if is_vulnerable:
                candidates.append((f, reason))
        
        if not candidates: return
        
        # 3. Match Targets to Available Fleets
        for target, reason in candidates:
             if not available_fleets: break
             
             # Find best interceptor (Closest + Stronger)
             best_hunter = None
             min_dist = 9999
             
             required_power = target.power * 1.2 # Need 20% advantage
             
             candidates_hunters = [hf for hf in available_fleets if hf.power >= required_power and hf.power > 0]
             
             for hf in candidates_hunters:
                 # Check distance manually (Fleet might not have distance_to)
                 loc1 = hf.location
                 loc2 = target.location
                 
                 # Ensure locations have coordinates
                 if not hasattr(loc1, 'x') or not hasattr(loc2, 'x'): continue
                 
                 d = ((loc1.x - loc2.x)**2 + (loc1.y - loc2.y)**2)**0.5
                 
                 if d < min_dist and d < 20.0: # Only pursue if reasonably close
                     min_dist = d
                     best_hunter = hf
             
             if best_hunter:
                 # Dispatch Hunter-Killer
                 self.ai.tf_counter += 1
                 tf = TaskForce(f"TF-HK-{self.ai.tf_counter}", faction)
                 tf.mission_role = "PURSUIT"
                 tf.target = target # Targeting FLEET not Planet
                 tf.add_fleet(best_hunter)
                 
                 self.ai.task_forces[faction].append(tf)
                 
                 available_fleets.remove(best_hunter)
                 
                 if self.ai.engine.logger:
                      self.ai.engine.logger.campaign(f"[{faction}] Dispatched HUNTER-KILLER {best_hunter.id} to intercept {reason} enemy {target.id} at {target.location.name}.")
