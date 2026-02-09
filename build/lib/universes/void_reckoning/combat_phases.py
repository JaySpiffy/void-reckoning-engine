from typing import List, Dict, Any
from src.combat.combat_phases import (
    MovementPhase, ShootingPhase, AbilityPhase, MeleePhase, MoralePhase,
    CombatPhase
)

class EternalCrusadeCombatRules:
    """
    Defines the combat phases and rules specific to the Void Reckoning universe.
    """
    
    def __init__(self):
        self.name = "Void Reckoning Combat Rules"
        self.version = "1.0.0"

    def register_phases(self) -> List[CombatPhase]:
        """
        Returns the list of phase instances to be executed in a battle round.
        Void Reckoning follows the standard phase order but allows for expansion.
        """
        return [
            AbilityPhase(),
            MovementPhase(),
            ShootingPhase(),
            MeleePhase(),
            MoralePhase()
        ]

    def get_phase_order(self) -> List[str]:
        """
        Returns the keys of the phases in execution order.
        """
        return ['ability', 'movement', 'shooting', 'melee', 'morale']

    def initialize_combat_state(self, armies_dict, grid, tracker) -> Dict[str, Any]:
        """
        Initializes any universe-specific state at the start of combat.
        """
        return {}
