
from typing import Dict, List, Any

class Ethics:
    def __init__(self, id: str, name: str, category: str, 
                 modifiers: Dict[str, float], 
                 requirements: List[str] = None,
                 conflicts: List[str] = None,
                 description: str = ""):
        self.id = id
        self.name = name
        self.category = category  # militarist, pacifist, etc.
        self.modifiers = modifiers
        self.requirements = requirements or []
        self.conflicts = conflicts or []
        self.description = description

class EthicsSystem:
    """
    Manages faction ethics and their effects.
    """
    def __init__(self):
        self.available_ethics: Dict[str, Ethics] = {}
        self.active_ethics: List[str] = []
        self.ethics_slots: int = 3 

    def register_ethics(self, ethic: Ethics):
        self.available_ethics[ethic.id] = ethic

    def select_ethics(self, ethic_id: str) -> bool:
        if ethic_id not in self.available_ethics: return False
        if len(self.active_ethics) >= self.ethics_slots: return False
        
        ethic = self.available_ethics[ethic_id]
        if any(c in self.active_ethics for c in ethic.conflicts): return False
        
        self.active_ethics.append(ethic_id)
        return True
