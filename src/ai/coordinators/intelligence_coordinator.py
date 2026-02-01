from src.reporting.telemetry import EventCategory
from src.config import logging_config
import json

class IntelligenceCoordinator:
    """
    Manages espionage, betrayal logic, and diplomatic target validation.
    Extracts intelligence logic from StrategicAI.
    """
    def __init__(self, engine, ai_manager):
        self.engine = engine
        self.ai = ai_manager

    def evaluate_espionage_targets(self, faction_name: str):
        """
        Decides if faction should attempt to steal weapons.
        Trigger: At War, Enemy has superior tech.
        """
        f = self.engine.factions.get(faction_name)
        if not f: return
        
        # Diplomacy check
        if not self.engine.diplomacy: return
        
        enemies = [e for e, status in self.engine.diplomacy.treaties.get(faction_name, {}).items() if status == "War"]
        if not enemies: return
        
        for enemy in enemies:
            enemy_f = self.engine.factions.get(enemy)
            if not enemy_f: continue
            
            # Attempt Theft
            # Check Intel Points (Assume abstract cost or cooldown handled by Manager)
            # Invoke Manager
            success = self.engine.intelligence_manager.attempt_weapon_theft(faction_name, enemy, f.weapon_registry, enemy_f.weapon_registry)
            
            if success:
                 # CRITICAL: Trigger Ship Refit
                 self.ai.update_ship_designs(faction_name)
                 
                 # [PHASE 6] Espionage Decision Trace
                 if logging_config.LOGGING_FEATURES.get('intelligence_espionage_tracing', False):
                     if hasattr(self.engine.logger, 'campaign'):
                         trace_msg = {
                             "event_type": "espionage_opportunity_evaluated",
                             "faction": faction_name,
                             "target": enemy,
                             "result": "SUCCESS",
                             "turn": self.engine.turn_counter
                         }
                         self.engine.logger.campaign(f"[INTEL] Espionage theft SUCCESS from {enemy}", extra=trace_msg)
                 break # One theft per turn per faction
            else:
                 # [PHASE 6] Espionage Failure Trace
                 if logging_config.LOGGING_FEATURES.get('intelligence_espionage_tracing', False):
                     if hasattr(self.engine.logger, 'campaign'):
                         trace_msg = {
                             "event_type": "espionage_opportunity_evaluated",
                             "faction": faction_name,
                             "target": enemy,
                             "result": "FAILURE",
                             "turn": self.engine.turn_counter
                         }
                         self.engine.logger.campaign(f"[INTEL] Espionage theft FAILURE from {enemy}", extra=trace_msg)

    def process_espionage_decisions(self, faction_obj):
        """AI decision loop for Advanced Espionage (Phase 2)."""
        if not hasattr(faction_obj, 'intel_points'): return
        
        # 1. Network Maintenance / Establishment
        self._manage_networks(faction_obj)
        
        # 2. Mission Execution
        self._execute_missions(faction_obj)

    def _manage_networks(self, faction):
        """Decides where to plant new spy networks."""
        # Budget check (Reserve 200 for operations)
        if faction.intel_points < 700: return # Cost 500 + Buffer
        
        # Target Selection: At War > Rivals > Leaders
        candidates = []
        
        # A. War Targets
        if self.engine.diplomacy:
             enemies = [e for e, status in self.engine.diplomacy.treaties.get(faction.name, {}).items() if status == "War"]
             for e in enemies:
                 if e not in faction.spy_networks:
                     candidates.append((100, e))
                     
        # B. Score Leaders
        sorted_factions = sorted([f for f in self.engine.factions.values() if f.name != faction.name], 
                               key=lambda x: getattr(x, 'score', 0), reverse=True)
        if sorted_factions:
             leader = sorted_factions[0]
             if leader.name not in faction.spy_networks and leader.name != faction.name:
                 candidates.append((50, leader.name))
                 
        if not candidates: return
        
        # Pick best
        candidates.sort(key=lambda x: x[0], reverse=True)
        target = candidates[0][1]
        
        self.engine.intelligence_manager.establish_spy_network(faction.name, target)

    def _execute_missions(self, faction):
        """Decides whether to launch missions from established networks."""
        if not faction.spy_networks: return
        
        for target_name, net in faction.spy_networks.items():
            if net.is_exposed: continue
            
            # Mission Selection Logic
            
            # A. Sabotage Production (War or Rival)
            # useful if they are building something big or we are at war
            is_at_war = self.get_diplomatic_stance(faction.name, target_name) == "HOSTILE"
            
            if is_at_war and net.infiltration_level >= 30 and faction.intel_points >= 300:
                # 50% chance to sabotage if affordable
                if self.engine.turn_counter % 5 == 0: # Throttle attempts
                     self.engine.intelligence_manager.conduct_espionage_mission(faction.name, target_name, "SABOTAGE_PRODUCTION")
                     continue

            # B. Incite Unrest (Mid-War destabilization)
            if is_at_war and net.infiltration_level >= 70 and faction.intel_points >= 800:
                 self.engine.intelligence_manager.conduct_espionage_mission(faction.name, target_name, "INCITE_UNREST")
                 continue
                 
            # C. Steal Tech (Peace or War, if they are advanced)
            # Simple check: Do they have more tech?
            target_f = self.engine.get_faction(target_name)
            if target_f and len(target_f.unlocked_techs) > len(faction.unlocked_techs):
                if net.infiltration_level >= 50 and faction.intel_points >= 500:
                    self.engine.intelligence_manager.conduct_espionage_mission(faction.name, target_name, "STEAL_TECH")


    def is_valid_target(self, faction: str, target_faction: str) -> bool:
        """Check if target_faction is diplomatically valid for offensive action."""
        if not self.engine.diplomacy:
            return True
        treaty = self.engine.diplomacy.treaties.get(faction, {}).get(target_faction, "Peace")
        
        # Access personality via AI Manager
        personality = self.ai.personality_manager.get_faction_personality(faction)
        return treaty == "War" or self.should_betray(faction, target_faction, personality)

    def should_betray(self, faction: str, target_faction: str, personality) -> bool:
        """Determine if faction should break alliance/truce with target_faction."""
        if not self.engine.diplomacy: return False
        
        # Only betray if existing relation is effectively allied/peace but we want to attack
        # Check current relation (INCLUDES GRUDGES)
        relation = self.engine.diplomacy.get_relation(faction, target_faction)
        
        # Betrayal Thresholds
        # Aggressive factions betray more easily
        threshold = -80
        if personality.aggression > 1.2: threshold = -50
        
        betrayal_triggered = False
        if relation < threshold:
             # Check relative strength
             my_power = sum(f.power for f in self.engine.fleets if f.faction == faction)
             their_power = sum(f.power for f in self.engine.fleets if f.faction == target_faction)
             
             if my_power > their_power * 1.5:
                 betrayal_triggered = True
                 
        if betrayal_triggered:
            # Trigger War Declaration
            self.engine.diplomacy.treaties[faction][target_faction] = "War"
            self.engine.diplomacy.treaties[target_faction][faction] = "War"
            
            # [PHASE 5] Grudge Trigger: Betrayal (Severe)
            if self.engine.diplomacy:
                self.engine.diplomacy.add_grudge(target_faction, faction, 50, "Betrayed our alliance")
            
            if hasattr(self.engine, 'telemetry'):
                self.engine.telemetry.log_event(
                    EventCategory.DIPLOMACY, "betrayal",
                    {"betrayer": faction, "victim": target_faction, "relation": relation},
                    turn=self.engine.turn_counter,
                    faction=faction
                )
                
            print(f"  > [DIPLOMACY] {faction} BETRAYS {target_faction}! (Relation: {relation})")
            
        return betrayal_triggered

    def get_diplomatic_stance(self, faction: str, target_faction: str) -> str:
        """Returns: 'HOSTILE', 'NEUTRAL', 'FRIENDLY', 'ALLIED'."""
        if not self.engine.diplomacy: return "HOSTILE"
        
        treaty = self.engine.diplomacy.treaties.get(faction, {}).get(target_faction, "Peace")
        if treaty == "War": return "HOSTILE"
        if treaty == "Trade": return "ALLIED"
        
        relation = self.engine.diplomacy.get_relation(faction, target_faction)
        if relation > 50: return "FRIENDLY"
        if relation < -50: return "HOSTILE"
        
        return "NEUTRAL"
