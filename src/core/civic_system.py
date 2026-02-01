
from typing import Dict, List, Any

class Civic:
    def __init__(self, id: str, name: str, category: str, 
                 modifiers: Dict[str, float], 
                 requirements: List[str] = None,
                 conflicts: List[str] = None,
                 description: str = ""):
        self.id = id
        self.name = name
        self.category = category  # government, policy, economic
        self.modifiers = modifiers
        self.requirements = requirements or []
        self.conflicts = conflicts or []
        self.description = description

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "modifiers": self.modifiers,
            "description": self.description
        }

class CivicSystem:
    """
    Manages faction-wide civic and policy traits.
    """
    def __init__(self):
        self.available_civics: Dict[str, Civic] = {}
        self.active_civics: List[str] = []
        self.civic_slots: int = 3  # Max civics per faction

    def register_civic(self, civic: Civic):
        self.available_civics[civic.id] = civic
        
    def activate_civic(self, civic_id: str) -> bool:
        if civic_id not in self.available_civics: return False
        if len(self.active_civics) >= self.civic_slots: return False
        
        # Check conflicts
        civic = self.available_civics[civic_id]
        if any(c in self.active_civics for c in civic.conflicts): return False
        
        self.active_civics.append(civic_id)
        return True
