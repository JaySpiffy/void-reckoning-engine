
from typing import Dict, List, Any

class AscensionPerk:
    def __init__(self, id: str, name: str, tier: int, 
                 modifiers: Dict[str, float], 
                 requirements: List[str] = None,
                 conflicts: List[str] = None,
                 description: str = ""):
        self.id = id
        self.name = name
        self.tier = tier  # 1, 2, 3, etc.
        self.modifiers = modifiers
        self.requirements = requirements or []
        self.conflicts = conflicts or []
        self.description = description

class AscensionSystem:
    """
    Manages late-game ascension perks and evolution.
    """
    def __init__(self):
        self.available_perks: Dict[str, AscensionPerk] = {}
        self.earned_perks: List[str] = []
        self.ascension_tier: int = 0
        self.perk_slots: int = 8

    def register_perk(self, perk: AscensionPerk):
        self.available_perks[perk.id] = perk
        
    def unlock_perk(self, perk_id: str) -> bool:
        if perk_id not in self.available_perks: return False
        if len(self.earned_perks) >= self.perk_slots: return False
        if perk_id in self.earned_perks: return False
        
        perk = self.available_perks[perk_id]
        if perk.tier > self.ascension_tier + 1: return False # Need valid tier
        
        # Check conflicts
        if any(c in self.earned_perks for c in perk.conflicts): return False
        
        self.earned_perks.append(perk_id)
        return True
