from typing import Dict, List, Optional, Any, TYPE_CHECKING
import random
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.services.relation_service import RelationService

class TreatyCoordinator:
    """
    Manages diplomatic states (War, Peace, Trade, Alliance) and their transitions.
    Coordinates mutual consent for peace and enforces cooldowns.
    """
    def __init__(self, factions: List[str], relation_service: 'RelationService', engine: Optional['CampaignEngine'] = None):
        self.factions = factions
        self.relation_service = relation_service
        self.engine = engine
        self.treaties: Dict[str, Dict[str, str]] = {} # {FactionA: {FactionB: "War"|"Peace"|"Trade"|"Alliance"|"Vassal"}}
        self.state_change_cooldowns: Dict[str, int] = {} # "f1_f2": turn_number
        self.treaty_start_turns: Dict[str, int] = {} # "f1_f2": start_turn
        
        # Treaty history tracking for telemetry
        self.treaty_history: Dict[str, List[Dict]] = {} # {faction_a: [{faction_b, treaty_type, start_turn, end_turn, events_during_treaty}]}
        
        # Phase 14: Alliance Effectiveness
        self.alliance_metrics: Dict[str, Dict[str, Any]] = {} # "f1_f2": {shared_intel: int, shared_tech: int, joint_victories: int}
        
        self.alliance_metrics: Dict[str, Dict[str, Any]] = {} # "f1_f2": {shared_intel: int, shared_tech: int, joint_victories: int}
        
        self.initialize_treaties()

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'engine' in state: del state['engine']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.engine = None # Restored by reinit_services


    def initialize_treaties(self):
        """Sets initial treaty states based on relations."""
        for f1 in self.factions:
            self.treaties[f1] = {}
            for f2 in self.factions:
                if f1 == f2: continue
                
                rel = self.relation_service.get_relation(f1, f2)
                if rel < -50:
                    self.treaties[f1][f2] = "War"
                else:
                    self.treaties[f1][f2] = "Peace"

    def get_treaty(self, f1: str, f2: str) -> str:
        return self.treaties.get(f1, {}).get(f2, "Peace")

    def set_treaty(self, f1: str, f2: str, state: str, symmetric: bool = True, reciprocal_state: Optional[str] = None):
        """Sets treaty state and logs if engine provided."""
        if f1 not in self.treaties: self.treaties[f1] = {}
        previous_state = self.treaties[f1].get(f2, "Peace")
        self.treaties[f1][f2] = state
        
        # [NEW] Track start turn for duration-based logic (e.g. War Exhaustion)
        pair_key = "_".join(sorted([f1, f2]))
        current_turn = self.engine.turn_counter if self.engine else 0
        if state != previous_state:
            self.treaty_start_turns[pair_key] = current_turn
        
        target_reciprocal = reciprocal_state if reciprocal_state else state
        
        if symmetric:
            if f2 not in self.treaties: self.treaties[f2] = {}
            previous_state_b2 = self.treaties[f2].get(f1, "Peace")
            self.treaties[f2][f1] = target_reciprocal
        else:
            previous_state_b2 = None
        
        # Log treaty history
        self._log_treaty_history(f1, f2, state, current_turn, None, [])
        
        # Log diplomatic state transition
        if self.engine and self.engine.telemetry:
            relation_service = self.relation_service
            relation_before = relation_service.get_relation(f1, f2) if previous_state_b2 is None else 0
            relation_after = relation_service.get_relation(f1, f2) if state == "War" else 100
            
            trigger_event = "peace_treaty" if state == "Peace" else "war_declaration"
            if state == "Alliance":
                trigger_event = "alliance_formed"
            elif state == "Trade":
                trigger_event = "trade_dissolved"
            
            self._log_diplomatic_state_transition(f1, f2, previous_state or "Unknown", state, relation_before, relation_after, trigger_event)

    def get_treaty_duration(self, f1: str, f2: str, current_turn: int) -> int:
        """Returns the number of turns the current treaty has been active."""
        pair_key = "_".join(sorted([f1, f2]))
        start_turn = self.treaty_start_turns.get(pair_key, 0)
        return max(0, current_turn - start_turn)

    def update_cooldown(self, f1: str, f2: str, current_turn: int, duration: int = 5):
        pair_key = "_".join(sorted([f1, f2]))
        # Store the turn when the cooldown EXPIRES
        self.state_change_cooldowns[pair_key] = current_turn + duration
    
    def is_on_cooldown(self, f1: str, f2: str, current_turn: int) -> bool:
        pair_key = "_".join(sorted([f1, f2]))
        expiry_turn = self.state_change_cooldowns.get(pair_key, 0)
        return (current_turn < expiry_turn)
    
    def _log_treaty_history(self, faction_a: str, faction_b: str, treaty_type: str, start_turn: int, end_turn: int = None, events_during_treaty: List[str] = None):
        """Log treaty history telemetry."""
        if self.engine and self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.DIPLOMACY,
                "treaty_history",
                {
                    "faction_a": faction_a,
                    "faction_b": faction_b,
                    "treaty_type": treaty_type,
                    "start_turn": start_turn,
                    "end_turn": end_turn,
                    "duration_turns": (end_turn - start_turn) if end_turn else None,
                    "events_during_treaty": events_during_treaty or []
                },
                turn=self.engine.turn_counter
            )
            
            # Update faction history
            pair_key = "_".join(sorted([faction_a, faction_b]))
            if faction_a not in self.treaty_history:
                self.treaty_history[faction_a] = []
            
            self.treaty_history[faction_a].append({
                "faction_b": faction_b,
                "treaty_type": treaty_type,
                "start_turn": start_turn,
                "end_turn": end_turn,
                "duration_turns": (end_turn - start_turn) if end_turn else None,
                "events_during_treaty": events_during_treaty or []
            })
    
    def _log_diplomatic_state_transition(self, faction_a: str, faction_b: str, previous_state: str, new_state: str, relation_before: int, relation_after: int, trigger_event: str):
        """Log diplomatic state transition telemetry."""
        if self.engine and self.engine.telemetry:
            # Calculate transition speed
            relation_delta = abs(relation_after - relation_before)
            if relation_delta > 50:
                transition_speed = "rapid"
            elif relation_delta > 20:
                transition_speed = "gradual"
            else:
                transition_speed = "sudden"
            
            self.engine.telemetry.log_event(
                EventCategory.DIPLOMACY,
                "diplomatic_state_transition",
                {
                    "faction_a": faction_a,
                    "faction_b": faction_b,
                    "turn": self.engine.turn_counter,
                    "previous_state": previous_state,
                    "new_state": new_state,
                    "relation_before": relation_before,
                    "relation_after": relation_after,
                    "trigger_event": trigger_event,
                    "transition_speed": transition_speed
                },
                turn=self.engine.turn_counter
            )

    def log_alliance_interaction(self, f1: str, f2: str, interaction_type: str):
        """
        Record interactions between allied factions (Metric #11).
        Types: shared_intel, shared_tech, joint_victory, resource_sharing
        """
        if self.get_treaty(f1, f2) != "Alliance":
            return
            
        pair_key = "_".join(sorted([f1, f2]))
        if pair_key not in self.alliance_metrics:
            self.alliance_metrics[pair_key] = {
                "shared_intel_count": 0,
                "shared_tech_count": 0,
                "joint_victories": 0,
                "resource_sharing_events": 0,
                "start_turn": self.engine.turn_counter
            }
            
        metrics = self.alliance_metrics[pair_key]
        if interaction_type == "shared_intel": metrics["shared_intel_count"] += 1
        elif interaction_type == "shared_tech": metrics["shared_tech_count"] += 1
        elif interaction_type == "joint_victory": metrics["joint_victories"] += 1
        elif interaction_type == "resource_sharing": metrics["resource_sharing_events"] += 1
        
        # Log telemetry event
        if self.engine and self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.DIPLOMACY,
                "alliance_effectiveness",
                {
                    "alliance_id": pair_key,
                    "members": [f1, f2],
                    "interaction_type": interaction_type,
                    "metrics": metrics,
                    "turn": self.engine.turn_counter
                },
                turn=self.engine.turn_counter
            )

    def check_treaty_violation(self, actor: str, target: str, action_type: str) -> int:
        """
        Checks if an action violates the current treaty.
        Returns the penalty magnitude (0 if no violation).
        """
        treaty = self.get_treaty(actor, target)
        
        if treaty == "War": return 0
        
        penalty = 0
        if action_type == "ATTACK":
            if treaty == "Non_Aggression_Pact": penalty = 50
            elif treaty == "Defensive_Pact": penalty = 80
            elif treaty == "Alliance": penalty = 100
            elif treaty == "Peace": penalty = 20 # Breaking standard peace
            elif treaty == "Trade": penalty = 30
            
        return penalty
