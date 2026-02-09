import random
import os
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from src.core.universe_data import UniverseDataManager

from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine

class RelationService:
    """
    Handles numeric relation values, historical biases, and grudges between factions.
    Manages relation drift and grudge decay over time.
    """
    def __init__(self, factions: List[str], engine: Optional['CampaignEngine'] = None):
        self.factions = factions
        self.engine = engine
        self.relations: Dict[str, Dict[str, int]] = {} # {FactionA: {FactionB: Value}}
        self.grudges: Dict[str, Dict[str, Dict[str, Any]]] = {} # {FactionA: {FactionB: {value, reason, decay}}}
        
        # Performance: Trace logging to file instead of console
        self.trace_file = None
        if engine and hasattr(engine, 'reports_dir'):
            log_dir = os.path.join(engine.reports_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.trace_file = os.path.join(log_dir, "diplomacy_trace.txt")
            
        self.initialize_relations()

    def _log_trace(self, message: str):
        if self.trace_file:
            try:
                with open(self.trace_file, "a", encoding='utf-8') as f:
                    f.write(message + "\n")
            except Exception:
                pass

    def initialize_relations(self):
        """Initializes the relation matrix with historical biases and random drift."""
        for f1 in self.factions:
            self.relations[f1] = {}
            self.grudges[f1] = {}
            for f2 in self.factions:
                if f1 == f2: continue
                
                # Base Value
                val = 10 # [TUNING] Start with Cautious Trust ("Cold Peace") to prevent instant war spirals
                
                # Historical Bias
                historical_bias = UniverseDataManager.get_instance().get_historical_bias()
                pair_key = f"{f1}_{f2}"
                reverse_key = f"{f2}_{f1}"
                
                if pair_key in historical_bias: 
                    val = historical_bias[pair_key]
                elif reverse_key in historical_bias: 
                    val = historical_bias[reverse_key]
                
                # Special cases (moved from original manager)
                # [PHASE 25] Diplomacy Tuning
                # Reduced initial hate to allow for some breathing room / player agency.
                # Chaos: -80 -> -40 (Hostile, but not instant war)
                # Bio-Morphs: -100 -> -90 (Still basically KOS, but maybe 1 turn delay)
                if "Chaos" in f1 and "Chaos" not in f2: val -= 40
                if "Bio-Morphs" in f1 and "Bio-Morphs" not in f2: val -= 90
                
                # Generic Random Drift
                val += random.randint(-10, 10)
                
                # Clamp
                self.relations[f1][f2] = max(-100, min(100, val))

    def get_relation(self, f1: str, f2: str) -> int:
        """Computes the net relation score, accounting for active grudges."""
        # [FOW] Diplomatic Fog of War
        if self.engine:
            faction_obj = self.engine.get_faction(f1)
            if faction_obj and hasattr(faction_obj, "known_factions"):
                if f2 not in faction_obj.known_factions:
                    self._log_trace(f"DEBUG REL: FOW blocking {f1}->{f2}")
                    return 0 # Perceived as Neutral until First Contact

        if f1 not in self.relations or f2 not in self.relations[f1]: 
            return 0
        
        base = self.relations[f1][f2]
        self._log_trace(f"DEBUG REL: {f1}->{f2} Base: {base}")
        return base

    def drift_relation(self, f1: str, f2: str, amount: int):
        """Helper for process_turn to apply drift."""
        self._log_trace(f"DEBUG: Drift {f1}->{f2} by {amount}. Current Matrix Keys: {list(self.relations.keys())}")
        if f1 in self.relations and f2 in self.relations[f1]:
            current = self.relations[f1][f2]
            self._log_trace(f"  Current: {current}")
            if amount > 0: # Drift towards positive or just adjustment
                 self.relations[f1][f2] = min(100, current + amount)
            elif amount < 0:
                 self.relations[f1][f2] = max(-100, current + amount)
            self._log_trace(f"  New: {self.relations[f1][f2]}")

    def modify_relation(self, f1: str, f2: str, amount: int, symmetric: bool = True):
        """Modifies the base relation between factions."""
        if f1 == f2 or f1 == "Neutral" or f2 == "Neutral": return
        
        if f1 in self.relations:
            current = self.relations[f1].get(f2, 0)
            self.relations[f1][f2] = max(-100, min(100, current + amount))
        
        if symmetric and f2 in self.relations:
            current2 = self.relations[f2].get(f1, 0)
            self.relations[f2][f1] = max(-100, min(100, current2 + amount))

    def add_grudge(self, f1: str, f2: str, amount: int, reason: str = "Unspecified"):
        """Adds a persistent negative modifier (Grudge) against another faction."""
        if f1 == f2: return
        
        event_type = "increased"
        if f1 not in self.grudges: self.grudges[f1] = {}
        if f2 not in self.grudges[f1]:
            self.grudges[f1][f2] = {'value': 0, 'reason': reason, 'decay': 0.5}
            event_type = "added"
            
        self.grudges[f1][f2]['value'] += amount
        if amount > 10:
             self.grudges[f1][f2]['reason'] = reason
             
        # Log Grudge
        self._log_grudge_lifecycle(f1, f2, self.grudges[f1][f2]['value'], reason, event_type)

    def log_planet_lost(self, victim: str, conqueror: str, planet_name: str):
        """Heavy grudge for losing a planet."""
        self.add_grudge(victim, conqueror, 25, f"Lost planet: {planet_name}")
        self.modify_relation(victim, conqueror, -15)

    def log_fleet_destroyed(self, victim: str, aggressor: str, fleet_name: str):
        """Moderate grudge for losing a fleet."""
        self.add_grudge(victim, aggressor, 10, f"Fleetdestroyed: {fleet_name}")
        self.modify_relation(victim, aggressor, -5)

    def log_treaty_violation(self, victim: str, violator: str, treaty_type: str):
        """Significant grudge for breaking trust."""
        self.add_grudge(victim, violator, 40, f"Broke {treaty_type} treaty")
        self.modify_relation(victim, violator, -30)

    def process_turn_drifts(self):
        """Processes time-based relation normalization and grudge decay."""
        # Note: Treaty state knowledge is required for drift, 
        # but RelationService shouldn't own treaties.
        # We'll expect the caller to tell us the context or provide a callback.
        # For now, we'll implement a method that takes treaty context.
        pass


    def decay_grudges(self):
        """Time heals wounds (gradually)."""
        for f1 in self.factions:
            current_grudges = list(self.grudges.get(f1, {}).keys())
            for f2_g in current_grudges:
                g_data = self.grudges[f1][f2_g]
                old_val = g_data['value']
                g_data['value'] -= g_data.get('decay', 0.5)
                
                if g_data['value'] <= 0:
                    self._log_grudge_lifecycle(f1, f2_g, 0, g_data.get('reason', ''), "resolved")
                    del self.grudges[f1][f2_g]
                elif int(old_val) != int(g_data['value']) and int(g_data['value']) % 10 == 0:
                    # Log significant decay? Or just silent.
                    # Let's log 'decreased' roughly every 10 points to avoid spam
                    self._log_grudge_lifecycle(f1, f2_g, g_data['value'], g_data.get('reason', ''), "decreased")

    def _log_grudge_lifecycle(self, victim, aggressor, value, reason, event_type):
        """Logs grudge lifecycle events (Metric #4)."""
        if self.engine and self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.DIPLOMACY,
                "grudge_lifecycle",
                {
                    "victim_faction": victim,
                    "aggressor_faction": aggressor,
                    "turn": getattr(self.engine, 'turn_counter', 0),
                    "grudge_value": value,
                    "reason": reason,
                    "event": event_type
                },
                turn=getattr(self.engine, 'turn_counter', 0)
            )

    def calculate_border_friction(self, shared_border_count: int, tension_modifier: float = 1.0) -> int:
        """Calculates negative drift based on shared borders."""
        # 1 border = -1 drift/turn (annoying)
        # 3 borders = -2 drift/turn (tension)
        # 5+ borders = -3 drift/turn (pressure)
        base_friction = 0
        if shared_border_count > 0:
            base_friction = -1
        if shared_border_count >= 3:
            base_friction = -2
        if shared_border_count >= 5:
            base_friction = -3
            
        return int(base_friction * tension_modifier)

    def apply_trade_drift(self, diplomacy_manager):
        """
        [INTEGRATION] Applies positive drift for active Trade Agreements.
        Called by DiplomacyManager.process_turn.
        """
        for f1 in self.factions:
            treaties = diplomacy_manager.treaty_coordinator.treaties.get(f1, {})
            for f2, treaty_type in treaties.items():
                if treaty_type == "Trade Agreement":
                    self.drift_relation(f1, f2, 2) # +2 per turn (beats decay)

    def apply_ideological_drift(self):
        """
        [PHASE 3] Applies relation drift based on alignment compatibility.
        - Order vs Chaos: -2 (Friction)
        - Profit vs Profit: +1 (Business)
        - Destruction vs Anyone: -5 (Existential Threat)
        """
        # Heuristic Alignment Map (Should be in a proper Registry later)
        def get_align(f):
            if "Chaos" in f or "Templars" in f: return "CHAOS"
            if "Imperium" in f or "Astartes" in f or "Aurelian" in f or "Transcendent" in f: return "ORDER"
            if "League" in f or "Tau" in f or "SteelBound" in f or "Algorithmic" in f: return "PROFIT" # Approximation
            if "Hive" in f or "Tyranid" in f or "BioTide" in f or "VoidSpawn" in f: return "DESTRUCTION"
            if "Ork" in f or "ScrapLord" in f: return "DESTRUCTION"
            if "Eldar" in f or "Primeval" in f: return "ORDER" 
            if "Necron" in f: return "DESTRUCTION" # Usually
            return "NEUTRAL"

        for f1 in self.factions:
            a1 = get_align(f1)
            for f2 in self.factions:
                if f1 == f2: continue
                a2 = get_align(f2)
                
                drift = 0
                
                # 1. Existential Threats
                if a1 == "DESTRUCTION" or a2 == "DESTRUCTION":
                    drift = -5 
                
                # 2. Order vs Chaos
                elif (a1 == "ORDER" and a2 == "CHAOS") or (a1 == "CHAOS" and a2 == "ORDER"):
                    drift = -2
                    
                # 3. Compatible Alignments
                elif a1 == a2 and a1 != "NEUTRAL":
                    if a1 == "PROFIT": drift = 1 # Business partners check in
                    if a1 == "ORDER": drift = 0 # Order doesn't necessarily mean friends, just not enemies
                    if a1 == "CHAOS": drift = -1 # Chaos fights itself too
                    
                if drift != 0:
                    self.drift_relation(f1, f2, drift)

    def apply_global_event_drift(self, event_name: str, magnitude: int):
        """
        [PHASE 3] Applies a global drift to ALL relationships.
        Useful for 'Galactic Peace Summits' or 'Warp Storms' (forcing isolation/paranoia).
        """
        for f1 in self.factions:
            for f2 in self.factions:
                if f1 == f2: continue
                self.drift_relation(f1, f2, magnitude)
                
        if self.engine and self.engine.logger:
             self.engine.logger.diplomacy(f"[GLOBAL EVENT] {event_name} caused relation drift of {magnitude} everywhere.")
