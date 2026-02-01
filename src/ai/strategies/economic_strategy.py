from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from src.managers.ai_manager import StrategicAI

class EconomicStrategy:
    """
    Handles economic-driven strategic decisions, such as restraining operations during bankruptcy.
    """
    def __init__(self, ai_manager: 'StrategicAI'):
        self.ai = ai_manager

    def handle_economic_restraint(self, faction: str, econ_state: str) -> None:
        """
        If bankrupt, cancel regular offensives but allow Raids separately.
        """
        # If bankrupt, cancel regular offensives but allow Raids separately
        if econ_state == "BANKRUPT":
            if faction in self.ai.task_forces:
                for tf in self.ai.task_forces[faction]:
                     if tf.state == "MUSTERING" and not getattr(tf, 'is_raid', False):
                         tf.state = "IDLE"
                         tf.target = None
