import random
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from src.utils.profiler import profile_method
from src.reporting.telemetry import EventCategory

from src.services.relation_service import RelationService
from src.managers.treaty_coordinator import TreatyCoordinator
from src.services.diplomatic_action_handler import DiplomaticActionHandler

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine

class DiplomacyManager:
    def __init__(self, factions, engine: Optional['CampaignEngine'] = None):
        """
        Initializes the DiplomacyManager by delegating to specialized services.
        """
        self.factions = factions
        self.engine = engine
        
        # Specialized Services
        self.relation_service = RelationService(factions, engine)
        self.treaty_coordinator = TreatyCoordinator(factions, self.relation_service, engine)
        self.action_handler = DiplomaticActionHandler(self)
        
        # Performance Cache
        self._war_cache = {} # {(f1, f2): status}
        self._war_matrix = {f: set() for f in factions} # Optimization 1.1: O(1) enemy lookup matrix
        
        # State change cooldowns (moved to coordinator but kept locally for easier access if needed)
        # However, it's better to let TreatyCoordinator own it.
        # Phase 22: War Exhaustion
        # {faction_name: {enemy_faction: exhaustion_percentage_0_to_1}}
        self.war_exhaustion = {} 
        
        # Initial Hydration
        self.invalidate_war_cache()
    # --- Backward Compatibility Properties ---
    @property
    def relations(self):
        return self.relation_service.relations
    
    @property
    def treaties(self):
        return self.treaty_coordinator.treaties

    def get_treaty(self, f1: str, f2: str) -> str:
        # Optimized with Cache (Strategy 1.1)
        key = tuple(sorted((f1, f2)))
        if key in self._war_cache:
            return self._war_cache[key]
            
        val = self.treaty_coordinator.get_treaty(f1, f2)
        self._war_cache[key] = val
        return val

    def get_enemies(self, faction: str) -> set:
        """Optimization 1.1: O(1) retrieval of all factions at war with this one."""
        return self._war_matrix.get(faction, set())

    def invalidate_war_cache(self):
        """Invalidates the treaty cache. Call whenever treaties change."""
        self._war_cache.clear()
        
        # Re-hydrate matrix
        self._war_matrix = {f: set() for f in self.factions}
        for f1 in self.factions:
            for f2 in self.factions:
                 if f1 == f2: continue
                 if self.treaty_coordinator.get_treaty(f1, f2) == "War":
                     self._war_matrix[f1].add(f2)

    def _set_treaty(self, f1: str, f2: str, treaty_type: str, **kwargs):
        """Wrapper to set treaty and invalidate cache."""
        self.treaty_coordinator.set_treaty(f1, f2, treaty_type, **kwargs)
        self.invalidate_war_cache()

    def get_treaties(self, faction: str) -> Dict[str, str]:
        """Returns all active treaties for a given faction."""
        return self.treaty_coordinator.treaties.get(faction, {})

    @property
    def grudges(self):
        return self.relation_service.grudges

    # --- Delegated Methods ---
    def get_relation(self, f1, f2):
        return self.relation_service.get_relation(f1, f2)
        
    def update_war_exhaustion(self, faction: str, enemy: str, amount: float):
        """
        Increases War Exhaustion for a faction against a specific enemy.
        If exhaustion reaches 1.0 (100%), triggers forced peace checks.
        """
        if faction not in self.war_exhaustion: self.war_exhaustion[faction] = {}
        current = self.war_exhaustion[faction].get(enemy, 0.0)
        
        # Apply gain
        new_val = min(1.0, current + amount)
        self.war_exhaustion[faction][enemy] = new_val
        
        # Logging
        if self.engine and self.engine.logger and amount > 0.01:
             self.engine.logger.diplomacy(f"[EXHAUSTION] {faction} exhaustion vs {enemy} rises to {new_val*100:.1f}% (+{amount*100:.1f}%)")
             
        # Check Force Peace Threshold
        if new_val >= 1.0:
            self.force_peace(faction, enemy)

    def force_peace(self, f1: str, f2: str):
        """Forces a Status Quo peace due to exhaustion."""
        # Ensure we are actually at war
        current_state = self.get_treaty(f1, f2)
        if current_state != "War": return
        
        if self.engine and self.engine.logger:
             self.engine.logger.diplomacy(f"[PEACE] {f1} collapses from War Exhaustion! Forced Status Quo with {f2}.")
             
        # Force Peace Treaty
        self._set_treaty(f1, f2, "Peace")
        
        # Reset Exhaustion for both sides (or just the exhausted one? usually resets war state)
        if f1 in self.war_exhaustion and f2 in self.war_exhaustion[f1]:
            self.war_exhaustion[f1][f2] = 0.0
        if f2 in self.war_exhaustion and f1 in self.war_exhaustion[f2]:
             # Optional: Should the winner also reset? Yes, new peace.
            self.war_exhaustion[f2][f1] = 0.0
            
        # [PHASE 25] Fix Forever War:
        # 1. Enforce Truce (10 turns)
        self.treaty_coordinator.update_cooldown(f1, f2, self.engine.turn_counter, duration=10)
        
        # 2. Reset Relations to "Cold Peace" (-45) if they are worse
        # If we leave them at -100, war restarts immediately after truce.
        current_rel = self.get_relation(f1, f2)
        if current_rel < -45:
             # Boost to -45 (Cold, but above the -50 war threshold)
             boost = -45 - current_rel
             self.relation_service.modify_relation(f1, f2, boost)
             
        # 3. Reduce Grudges by 50% (War Exhaustion makes you forget why you hated them)
        if f1 in self.relation_service.grudges and f2 in self.relation_service.grudges[f1]:
             self.relation_service.grudges[f1][f2]['value'] *= 0.5
        if f2 in self.relation_service.grudges and f1 in self.relation_service.grudges[f2]:
             self.relation_service.grudges[f2][f1]['value'] *= 0.5

        if self.engine and self.engine.logger:
             self.engine.logger.diplomacy(f"[PEACE] Relations reset to -45, Grudges halved to prevent instant relapse.")

    def add_grudge(self, f1, f2, amount, reason="Unspecified"):
        self.relation_service.add_grudge(f1, f2, amount, reason)
        
        # Logging/Telemetry (kept here as it's orchestrator level)
        if self.engine and self.engine.logger:
             self.engine.logger.diplomacy(f"[GRUDGE] {f1} holds a GRUDGE against {f2} for '{reason}' (Value: {self.relation_service.grudges[f1][f2]['value']})")

        if self.engine and hasattr(self.engine, 'telemetry'):
             self.engine.telemetry.log_event(
                 EventCategory.DIPLOMACY, "grudge_added",
                 {"victim": f1, "aggressor": f2, "value": amount, "reason": reason, "current_total": self.relation_service.grudges[f1][f2]['value']},
                 turn=getattr(self.engine, 'turn_counter', 0),
                 faction=f1
             )

    def modify_relation(self, f1, f2, amount, symmetric=True):
        self.relation_service.modify_relation(f1, f2, amount, symmetric)

    def share_blueprint(self, faction_a: str, faction_b: str, blueprint_id: str, engine: 'CampaignEngine'):
        return self.action_handler.share_blueprint(faction_a, faction_b, blueprint_id)

    @profile_method
    def process_turn(self):
        current_turn = getattr(self.engine, 'turn_counter', 0)

        # 1. Relation Drift & Grudge Decay
        for f1 in self.factions:
            # Passive Exhaustion Gain for Active Wars
            if f1 in self.war_exhaustion:
                for enemy, val in list(self.war_exhaustion[f1].items()):
                    if self.get_treaty(f1, enemy) == "War":
                        self.update_war_exhaustion(f1, enemy, 0.01) # +1% per turn passive

            for f2 in self.factions:
                if f1 == f2: continue
                
                state = self.treaty_coordinator.get_treaty(f1, f2)
                rel = self.get_relation(f1, f2)
                
                # Apply Drifts
                if state == "War":
                    if rel < -20: self.relation_service.drift_relation(f1, f2, 1)
                elif state == "Trade":
                    self.relation_service.drift_relation(f1, f2, 0.5) # Nerfed from 2.0 to prevent infinite peace
                else:
                    # [FIX] Regression to Mean vs Alignment
                    # If they are Natural Allies (Alignment Drift > 0), DO NOT regress positive relations.
                    # This allows Alignment to push them to +100.
                    alignment_drift = 0
                    a1 = self._get_alignment(f1, self._get_alignment_map())
                    a2 = self._get_alignment(f2, self._get_alignment_map())
                    if a1 == a2 and a1 != "NEUTRAL":
                         alignment_drift = 1

                    # [FIX] Death Spiral Prevention:
                    # Only regress relations if there is already "Bad Blood" (-25).
                    # Minor annoyances (-5 to -24) should decay naturally or stagnate, not spiral to war.
                    if rel < -25: self.relation_service.drift_relation(f1, f2, -1)
                    
                    # Only regress positive relations if NOT natural allies
                    if rel > 0 and alignment_drift <= 0: 
                         self.relation_service.drift_relation(f1, f2, -1)
            
                # Logic for forming new treaties (Alliance/Trade)
                # [FIX] Must run outside the 'else' (Peace) block to allow Trade -> Alliance upgrades
                self._check_for_new_treaties(f1, f2, rel, state)
                    
        self.relation_service.decay_grudges()
                    
        # 2. AI Decisions (War/Peace)
        self._process_ai_decisions(current_turn)

        # 3. Diplomatic Actions (Blueprint Sharing)
        self._process_diplomatic_actions(current_turn)
        
        # 4. Alignment Drift (Power Bloc Formation)
        self._apply_global_alignment_drift()

    def _get_alignment_map(self):
        return {
            # ORDER
            "Primeval_Sentinels": "ORDER", 
            "Transcendent_Order": "ORDER", 
            "Aurelian_Hegemony": "ORDER", 
            "Templars_of_the_Flux": "ORDER",
            
            # CHAOS
            "VoidSpawn_Entities": "CHAOS", 
            "Algorithmic_Hierarchy": "CHAOS",
            
            # DESTRUCTION
            "BioTide_Collective": "DESTRUCTION", 
            "SteelBound_Syndicate": "DESTRUCTION",
            
            # PROFIT
            "ScrapLord_Marauders": "PROFIT", 
            "Nebula_Drifters": "PROFIT"
        }

    def _apply_global_alignment_drift(self):
        """
        Applies passive relation changes based on ideological alignment.
        Creates 'Power Blocs' (Order vs Chaos vs Destruction vs Profit).
        """
        ALIGNMENT_MAP = self._get_alignment_map()
        
        for f1 in self.factions:
            a1 = self._get_alignment(f1, ALIGNMENT_MAP)
            for f2 in self.factions:
                if f1 == f2: continue
                # Symmetric check handled by iteration or strict ordering? 
                # RelationService handles symmetric updates, but we iterate F1->F2.
                # To avoid double counting, valid approach: modify pairwise. 
                # But modify_relation is symmetric. So we should only do it once per pair.
                if f1 > f2: continue # Unique pairs only
                
                a2 = self._get_alignment(f2, ALIGNMENT_MAP)
                
                drift = 0
                if a1 == a2 and a1 != "NEUTRAL":
                    # Natural Allies
                    drift = 1 
                elif (a1 == "ORDER" and a2 == "CHAOS") or (a2 == "ORDER" and a1 == "CHAOS"):
                    # Natural Enemies
                    drift = -1
                
                if drift != 0:
                    # [FIX] ALIGNMENT CAP
                    # Ideology alone should not cause War (-50).
                    # Cap negative drift so it cannot push below -40.
                    curr_rel = self.get_relation(f1, f2)
                    if drift < 0 and curr_rel <= -40:
                         drift = 0 # Already saturated by ideology
                    
                    if drift != 0:
                        self.modify_relation(f1, f2, drift)
                    # Log occasionally
                    if self.engine and self.engine.turn_counter % 20 == 0:
                         if self.engine.logger:
                             self.engine.logger.diplomacy(f"[ALIGNMENT] {f1}({a1}) <> {f2}({a2}) relation drift: {drift:+}")

    def _get_alignment(self, faction_name, alignment_map):
        # Handle specific instances "Hegemony 2" -> "Hegemony"
        base_name = faction_name.split(' ')[0] # Simple heuristic
        # Check full name first
        if faction_name in alignment_map: return alignment_map[faction_name]
        # Check base name
        if base_name in alignment_map: return alignment_map[base_name]
        # Fallback based on keywords (only if necessary)
        if "Hive" in faction_name: return "DESTRUCTION"
        return "NEUTRAL"

    def _check_for_new_treaties(self, f1, f2, rel, state):
        """Strategic treaty formation based on need and threat."""
        # [FIX] Allow upgrading from Trade -> Alliance
        if state not in ["Peace", "Trade"]: return
        
        # 1. Base Multipliers
        alliance_chance = 0.10
        trade_chance = 0.15
        
        # 2. Strategic Modifiers (Need-based)
        f1_obj = self.engine.get_faction(f1)
        f2_obj = self.engine.get_faction(f2)
        
        # Economic Need (Trade)
        if f1_obj and f2_obj:
            # Check if either is in economic trouble
            f1_econ = self.engine.economy_manager.get_faction_economic_report(f1)
            f2_econ = self.engine.economy_manager.get_faction_economic_report(f2)
            
            if f1_econ.get("margin", 1.0) < 1.1 or f2_econ.get("margin", 1.0) < 1.1:
                # Emergency Trade needed!
                trade_chance *= 3.0
                
        # Military Threat (Alliance)
        threatened = False
        if hasattr(self.engine, 'strategic_ai') and hasattr(self.engine.strategic_ai, 'predict_enemy_threats'):
            f1_threats = self.engine.strategic_ai.predict_enemy_threats(f1)
            f2_threats = self.engine.strategic_ai.predict_enemy_threats(f2)
            if f1_threats or f2_threats:
                threatened = True
                alliance_chance *= 4.0
        
        # 3. Evaluation
        roll = random.random()
        
        # ALLIANCE
        if rel > 60:
            if roll < alliance_chance:
                self._set_treaty(f1, f2, "Alliance")
                reason = "STRATEGIC DEFENSE" if threatened else "MUTUAL TRUST"
                if self.engine and self.engine.logger:
                    self.engine.logger.diplomacy(f"[{reason}] {f1} and {f2} have formed an ALLIANCE! (Rel: {rel})")
                if self.engine and self.engine.report_organizer:
                    self.engine.report_organizer.log_to_master_timeline(self.engine.turn_counter, "ALLIANCE", f"{f1} and {f2} formed an ALLIANCE ({reason})")
                return

        # TRADE
        if state != "Trade" and rel > 35: # Slightly lowered threshold for emergency trade
            if roll < trade_chance:
                self._set_treaty(f1, f2, "Trade")
                # [PHASE 25] Anti-Flicker: Enforce 5 turn stability
                self.treaty_coordinator.update_cooldown(f1, f2, self.engine.turn_counter, duration=5)
                
                if self.engine and self.engine.logger:
                    self.engine.logger.diplomacy(f"[TRADE] {f1} and {f2} established a TRADE TREATY to boost economies! (Rel: {rel})")
                if self.engine and self.engine.report_organizer:
                    self.engine.report_organizer.log_to_master_timeline(self.engine.turn_counter, "TRADE", f"{f1} and {f2} established a TRADE TREATY")

    def _process_ai_decisions(self, current_turn):
        for f1 in self.factions:
            for f2 in self.factions:
                if f1 == f2: continue
                if self.treaty_coordinator.is_on_cooldown(f1, f2, current_turn):
                    continue

                rel = self.get_relation(f1, f2)
                state = self.treaty_coordinator.get_treaty(f1, f2)
                
                # BREAK ALLIANCE
                if state == "Alliance" and rel < 45:
                    self._set_treaty(f1, f2, "Peace")
                    if self.engine and self.engine.logger:
                         self.engine.logger.diplomacy(f"[DIPLOMACY] Alliance between {f1} and {f2} has dissolved due to diverging interests. (Rel: {rel})")
                
                # BREAK TRADE
                elif state == "Trade" and rel < 30:
                    self._set_treaty(f1, f2, "Peace")
                    if self.engine and self.engine.logger:
                        self.engine.logger.diplomacy(f"[DIPLOMACY] Trade treaty between {f1} and {f2} has dissolved due to cooling relations. (Rel: {rel})")
                    
                    # [PROFILE] Breach Treaty
                    if hasattr(self.engine, 'strategic_ai') and hasattr(self.engine.strategic_ai, 'opponent_profiler'):
                        self.engine.strategic_ai.opponent_profiler.register_event(f1, "BROKE_TREATY", current_turn)
                
                # DECLARE WAR
                # Base Threshold: -50 (was -80)
                # Volatile Factions (Chaos/Destruction) might attack sooner
                war_threshold = -50
                a1 = self._get_alignment(f1, self._get_alignment_map())
                if a1 in ["CHAOS", "DESTRUCTION"]:
                     # [PHASE 25] Tuning: Reduced random war chance.
                     # Only trigger "impulse war" if relations are actually bad (<-60), not just mildly annoyed (-25).
                     if random.random() < 0.05:
                         war_threshold = -60

                if rel < war_threshold and state != "War":
                     # [FIX] War Saturation / Multi-Front Prevention
                     # Don't declare war if we are already fighting too many people.
                     active_wars = len([k for k,v in self.get_treaties(f1).items() if v == "War"])
                     saturation_limit = 2 if a1 in ["CHAOS", "DESTRUCTION"] else 1
                     
                     aggression_modifier = 1.0
                     if active_wars >= saturation_limit:
                          aggression_modifier = 0.1 # 90% reduced chance
                     
                     if random.random() < aggression_modifier:
                          self._declare_war(f1, f2, rel, current_turn)
                     else:
                          if self.engine and self.engine.logger and random.random() < 0.05:
                               self.engine.logger.diplomacy(f"[RESTRAINT] {f1} holds back war dealing with {f2} due to War Saturation ({active_wars} wars).")
                
                # Check Coalition Obligations
                if hasattr(self.engine, 'strategic_ai') and hasattr(self.engine.strategic_ai, 'coalition_builder'):
                     coalitions = self.engine.strategic_ai.coalition_builder.coalitions
                     for c in coalitions.values():
                          if c.is_active and f1 in c.members and f2 == c.target_faction and state != "War":
                               # FORCE war if in coalition against target
                               self._declare_war(f1, f2, rel, current_turn, reason="Coalition Obligation")
                
                # MAKE PEACE
                elif rel > -30 and state == "War":
                    self._try_make_peace(f1, f2, rel, current_turn)
                
                # [PHASE 7] CHECK FOR VASSALAGE
                elif state == "Peace" or state == "Trade" or state == "Alliance":
                    self._check_for_vassalage(f1, f2, rel, current_turn)

    def _declare_war(self, f1, f2, rel, current_turn, reason="Aggressive War Declaration"):
        self._set_treaty(f1, f2, "War")
        self.treaty_coordinator.update_cooldown(f1, f2, current_turn) # Default 5 turns
        self.relation_service.add_grudge(f2, f1, 20, reason)
        
        # [PHASE 7] VASSAL OBLIGATION: If f2 is an Overlord, declare war on their Vassals too
        # And if f1 has Vassals, they join too.
        self._enforce_vassal_war_obligations(f1, f2, current_turn)
        
        # [PHASE 7] ALLIANCE OBLIGATION (Call to Arms)
        self._enforce_alliance_war_obligations(f1, f2, current_turn)
        
        # [PROFILE] War Declaration
        if hasattr(self.engine, 'strategic_ai') and hasattr(self.engine.strategic_ai, 'opponent_profiler'):
             self.engine.strategic_ai.opponent_profiler.register_event(f1, "WAR_DECLARATION", current_turn)
        
        if self.engine:
            self.engine.faction_reporter.log_event(f1, "diplomacy", f"Declared WAR on {f2}", {"target": f2})
            self.engine.faction_reporter.log_event(f2, "diplomacy", f"{f1} declared WAR on us!", {"attacker": f1})
            for f in [f1, f2]:
                f_obj = self.engine.get_faction(f)
                if f_obj: f_obj.stats["turn_diplomacy_actions"] += 1
        
        if self.engine and self.engine.logger:
            self.engine.logger.diplomacy(f"[WAR] DIPLOMACY: {f1} declares WAR on {f2}! (Relation: {rel}, Reason: {reason})")
        if self.engine and self.engine.report_organizer:
            self.engine.report_organizer.log_to_master_timeline(self.engine.turn_counter, "WAR", f"{f1} DECLARED WAR on {f2} (Reason: {reason})")

    def _try_make_peace(self, f1, f2, rel, current_turn):
        f1_p = self.engine.strategic_ai.get_faction_personality(f1)
        f2_p = self.engine.strategic_ai.get_faction_personality(f2)
        
        f1_envoys = f1_p.quirks.get("can_receive_envoys", True) if hasattr(f1_p, "quirks") else getattr(f1_p, "can_receive_envoys", True)
        f2_envoys = f2_p.quirks.get("can_receive_envoys", True) if hasattr(f2_p, "quirks") else getattr(f2_p, "can_receive_envoys", True)
        
        if not f1_envoys or not f2_envoys: return
        if "Bio-Morphs" in f1 or "Bio-Morphs" in f2: return
        if "Chaos" in f1 and "Hegemony" in f2: return 
        
        # [PHASE 7] GRUDGE-LOCKED PEACE
        # If victim (f2) holds a significant grudge against proposer (f1), they refuse.
        grudge_data = self.relation_service.grudges.get(f2, {}).get(f1, {})
        if grudge_data.get('value', 0) > 40:
            if self.engine and self.engine.logger:
                self.engine.logger.diplomacy(f"[GRUDGE] {f2} refuses peace with {f1} due to unwashed sins: '{grudge_data['reason']}' (Grudge: {grudge_data['value']})")
            return

        rel_target = self.get_relation(f2, f1)
        
        # [NEW] WAR EXHAUSTION (Stalemate Logic)
        # If war has lasted > 50 turns, standards drop.
        war_duration = self.treaty_coordinator.get_treaty_duration(f1, f2, current_turn)
        peace_threshold = -50
        
        if war_duration > 50:
            peace_threshold = -150 # Desperate for peace
            if self.engine and self.engine.logger:
                 self.engine.logger.diplomacy(f"[EXHAUSTION] {f2} is considering PEACE with {f1} due to War Exhaustion ({war_duration} turns). Threshold relaxed.")

        if rel_target > peace_threshold:
            self._set_treaty(f1, f2, "Peace")
            # Mandatory 10-turn Ceasefire (Truce)
            self.treaty_coordinator.update_cooldown(f1, f2, current_turn, duration=10)
            
            # [PROFILE] Peace Offer (Successful)
            if hasattr(self.engine, 'strategic_ai') and hasattr(self.engine.strategic_ai, 'opponent_profiler'):
                 self.engine.strategic_ai.opponent_profiler.register_event(f1, "PEACE_OFFER", current_turn)
            
            if self.engine:
                self.engine.faction_reporter.log_event(f1, "diplomacy", f"Signed PEACE treaty with {f2}", {"partner": f2})
                self.engine.faction_reporter.log_event(f2, "diplomacy", f"Signed PEACE treaty with {f1}", {"partner": f1})
                for f in [f1, f2]:
                    f_obj = self.engine.get_faction(f)
                    if f_obj: f_obj.stats["turn_diplomacy_actions"] += 1
            
            if self.engine and self.engine.logger:
                self.engine.logger.diplomacy(f"[PEACE] DIPLOMACY: {f1} and {f2} sign PEACE TREATY. (Rel: {rel}/{rel_target}) -> 10 Turn Ceasefire Enforced.")
            if self.engine and self.engine.report_organizer:
                self.engine.report_organizer.log_to_master_timeline(self.engine.turn_counter, "PEACE", f"{f1} and {f2} signed a PEACE TREATY (10-Turn Truce)")
        else:
            if self.engine and hasattr(self.engine, 'telemetry'):
                self.engine.telemetry.log_event(
                    EventCategory.DIPLOMACY, "peace_rejected",
                    {"proposer": f1, "target": f2, "proposer_rel": rel, "target_rel": rel_target},
                    turn=current_turn
                )

    # --- [PHASE 7] NEW METHODS ---

    def _check_for_vassalage(self, f1: str, f2: str, rel: int, turn: int):
        """Strategic evaluation of subjugation opportunities."""
        # Only major powers demand vassalage
        f1_obj = self.engine.get_faction(f1)
        f2_obj = self.engine.get_faction(f2)
        if not f1_obj or not f2_obj: return

        # Power gap check (F1 > 4x F2)
        p1 = f1_obj.stats.get("total_power", 1)
        p2 = f2_obj.stats.get("total_power", 1)
        if p1 < p2 * 4: return

        # F2 is in trouble? (Low requisition or low systems)
        if f2_obj.requisition > 10000: return
        
        # Logic for 'Diplomatic Subjugation' (Offer Protection)
        if rel > 40 and random.random() < 0.05:
            self._apply_subjugation(f1, f2, "Diplomatic Protection", turn)
        
        # Logic for 'Intimidation' (Demand Submission)
        elif rel < 0 and random.random() < 0.02:
            self._apply_subjugation(f1, f2, "Intimidation", turn)

    def _apply_subjugation(self, overlord: str, vassal: str, reason: str, turn: int):
        """Formalizes a Vassalage relationship."""
        # Overlord view: f2 is a Vassal
        # Vassal view: f1 is an Overlord
        self._set_treaty(overlord, vassal, "Vassal", reciprocal_state="Overlord")
        self.treaty_coordinator.update_cooldown(overlord, vassal, turn, duration=20) # Long term binding
        
        msg = f"[VASSALAGE] {vassal} has been subjugated by {overlord} ({reason})!"
        if self.engine and self.engine.logger:
             self.engine.logger.diplomacy(msg)
        
        if self.engine and self.engine.report_organizer:
            self.engine.report_organizer.log_to_master_timeline(turn, "VASSALAGE", msg)

    def _enforce_vassal_war_obligations(self, f1: str, f2: str, turn: int):
        """Ensures vassals join their overlord's wars."""
        # If f2 has vassals, they declare war on f1
        for potential_vassal in self.factions:
            if self.treaty_coordinator.get_treaty(f2, potential_vassal) == "Vassal":
                if self.treaty_coordinator.get_treaty(potential_vassal, f1) != "War":
                    self._set_treaty(potential_vassal, f1, "War")
                    if self.engine.logger:
                        self.engine.logger.diplomacy(f"[VASSAL OBLIGATION] {potential_vassal} joins Overlord {f2} in war against {f1}!")

        # If f1 has vassals, they join against f2
        for potential_vassal in self.factions:
            if self.treaty_coordinator.get_treaty(f1, potential_vassal) == "Vassal":
                if self.treaty_coordinator.get_treaty(potential_vassal, f2) != "War":
                    self._set_treaty(potential_vassal, f2, "War")
                    if self.engine.logger:
                        self.engine.logger.diplomacy(f"[VASSAL OBLIGATION] {potential_vassal} supports Overlord {f1} against {f2}!")

    def _enforce_alliance_war_obligations(self, f1: str, f2: str, turn: int):
        """Ensures allies join defensive and offensive wars."""
        # Allies of f2 (Defensive)
        for potential_ally in self.factions:
            if potential_ally == f1: continue
            if self.treaty_coordinator.get_treaty(f2, potential_ally) == "Alliance":
                if self.treaty_coordinator.get_treaty(potential_ally, f1) != "War":
                    self._set_treaty(potential_ally, f1, "War")
                    # [PHASE 25] Alliance War Penalty
                    # Joining a war ruins relations, obviously.
                    self.relation_service.modify_relation(potential_ally, f1, -60) 
                    if self.engine.logger:
                        self.engine.logger.diplomacy(f"[ALLIANCE CALL] {potential_ally} joins Ally {f2} in defensive war against {f1}! (Rel dropped)")

        # Allies of f1 (Offensive)
        for potential_ally in self.factions:
            if potential_ally == f2: continue
            if self.treaty_coordinator.get_treaty(f1, potential_ally) == "Alliance":
                # Check Truce
                if self.treaty_coordinator.is_on_cooldown(potential_ally, f2, turn):
                     if self.engine.logger:
                          self.engine.logger.diplomacy(f"[ALLIANCE CALL] {potential_ally} refuses to join Offensive War against {f2} due to Truce/Cooldown.")
                     continue
                     
                if self.treaty_coordinator.get_treaty(potential_ally, f2) != "War":
                    # Offensive wars are slightly less certain but for now we force it
                    self._set_treaty(potential_ally, f2, "War")
                    # [PHASE 25] Alliance War Penalty
                    self.relation_service.modify_relation(potential_ally, f2, -60)
                    if self.engine.logger:
                        self.engine.logger.diplomacy(f"[ALLIANCE CALL] {potential_ally} supports Ally {f1} in offensive war against {f2}! (Rel dropped)")

    def _process_diplomatic_actions(self, current_turn):
        for f1 in self.factions:
            for f2 in self.factions:
                if f1 == f2: continue
                if self.treaty_coordinator.get_treaty(f1, f2) == "Trade" and self.get_relation(f1, f2) >= 60:
                     if random.random() < 0.20:
                          cd_key = f"{f1}_{f2}_share_cd"
                          if not hasattr(self, cd_key) or getattr(self, cd_key) < current_turn:
                               tech_values = self.engine.tech_manager.analyze_tech_tree(f1)
                               f1_obj = self.engine.get_faction(f1)
                               if f1_obj:
                                    candidates = [t for t in f1_obj.unlocked_techs if tech_values.get(t, 0) < 3.0]
                                    if candidates:
                                         bid = random.choice(candidates)
                                         if self.action_handler.share_blueprint(f1, f2, bid):
                                              setattr(self, cd_key, current_turn + 10)
