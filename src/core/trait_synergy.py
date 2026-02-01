
from typing import Dict, List, Any

class TraitSynergy:
    """
    Defines how traits interact when combined.
    """
    def __init__(self, id: str, name: str, trait_ids: List[str], modifiers: Dict[str, float], bonus_traits: List[str] = None):
        self.id = id
        self.name = name
        self.trait_ids = trait_ids # List of required traits
        self.modifiers = modifiers # Bonus stats if all present
        self.bonus_traits = bonus_traits or [] # Free extra traits if all present

    def check_synergy(self, unit_traits: List[str]) -> bool:
        """Returns True if unit has all required traits."""
        return all(t in unit_traits for t in self.trait_ids)
        
    def calculate_synergy_bonus(self, unit_traits: List[str]) -> Dict[str, float]:
        """Calculate bonus modifiers when traits are combined."""
        # Simple Logic: If all present, return full modifiers
        if self.check_synergy(unit_traits):
            return self.modifiers
        return {}

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "trait_ids": self.trait_ids,
            "modifiers": self.modifiers,
            "bonus_traits": self.bonus_traits
        }
