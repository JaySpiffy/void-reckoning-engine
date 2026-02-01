import random
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
        
        self.initialize_relations()

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
        # If we haven't met them, we don't know we hate them yet.
        if self.engine:
            faction_obj = self.engine.get_faction(f1)
            if faction_obj and hasattr(faction_obj, "known_factions"):
                if f2 not in faction_obj.known_factions:
                    return 0 # Perceived as Neutral until First Contact

        if f1 not in self.relations or f2 not in self.relations[f1]: 
            return 0
        
        base = self.relations[f1][f2]
        grudge = 0
        if f2 in self.grudges.get(f1, {}):
             grudge = self.grudges[f1][f2].get('value', 0)
             
        return int(base - grudge)

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

    def drift_relation(self, f1: str, f2: str, amount: int):
        """Helper for process_turn to apply drift."""
        if f1 in self.relations and f2 in self.relations[f1]:
            current = self.relations[f1][f2]
            if amount > 0: # Drift towards positive or just adjustment
                 self.relations[f1][f2] = min(100, current + amount)
            elif amount < 0:
                 self.relations[f1][f2] = max(-100, current + amount)

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
