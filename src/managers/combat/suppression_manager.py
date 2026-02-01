
from typing import List, Dict, Any, Optional
from src.models.unit import Unit
from src.core.constants import SUPPRESSED_THRESHOLD, PINNED_THRESHOLD

class SuppressionManager:
    """
    [Phase 23] Manages suppression mechanics for ground units (Firefight Model).
    Handles suppression accumulation, decay, and state transitions (Suppressed/Pinned).
    """
    def __init__(self, context=None):
        self.context = context

    def apply_suppression(self, target: Unit, amount: float):
        """
        Applies suppression damage to a unit. Logic accounts for resistance.
        """
        if not target.is_alive(): return
        
        # Resistance Check
        # Resistance acts as a flat reduction or percentage mitigation
        resistance = getattr(target, 'suppression_resistance', 0)
        
        # Formula: Effective Suppression = Amount * (100 / (100 + Resistance))
        effective_amount = amount * (100.0 / (100.0 + resistance))
        
        target.current_suppression += effective_amount
        target.current_suppression = min(target.current_suppression, 100.0) # Cap at 100%
        
        self._check_state_transitions(target)

    def process_decay(self, units: List[Unit]):
        """
        Decays suppression for all units. Called at end of round/turn.
        """
        for unit in units:
            if not unit.is_alive(): continue
            if unit.current_suppression > 0:
                # Default decay - 10 per turn, plus bonus if in cover?
                decay = 10.0
                if getattr(unit, 'in_cover', False):
                    decay += 5.0
                    
                unit.current_suppression = max(0.0, unit.current_suppression - decay)
                self._check_state_transitions(unit)

    def _check_state_transitions(self, unit: Unit):
        """
        Updates is_suppressed and is_pinned flags based on current suppression levels.
        """
        level = unit.current_suppression
        
        # 1. Check Pinned (> 75%)
        # [MODERNIZATION] "Pinned" means immobilized and severe accuracy penalties.
        if level >= 75.0:
            if not unit.is_pinned:
                unit.is_pinned = True
                unit.is_suppressed = True # Pinned implies Suppressed
                # Apply Speed/Accuracy/Morale Logic here or in CombatSimulator
                
        # 2. Check Suppressed (> 25%)
        elif level >= 25.0:
            unit.is_pinned = False
            if not unit.is_suppressed:
                unit.is_suppressed = True
                
        # 3. Clear States
        else:
            unit.is_pinned = False
            unit.is_suppressed = False

    def get_suppression_modifiers(self, unit: Unit) -> Dict[str, float]:
        """
        Returns combat modifiers based on current state.
        """
        mods = {"accuracy_mult": 1.0, "speed_mult": 1.0, "morale_dmg": 0.0}
        
        if unit.is_pinned:
            mods["accuracy_mult"] = 0.50 # -50% Accuracy
            mods["speed_mult"] = 0.10    # -90% Speed (Immobilized)
            mods["morale_dmg"] = -5.0    # Per turn penalty
        elif unit.is_suppressed:
            mods["accuracy_mult"] = 0.90 # -10% Accuracy
            mods["speed_mult"] = 0.75    # -25% Speed
            
        return mods
