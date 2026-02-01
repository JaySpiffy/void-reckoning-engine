
from typing import Dict, List, Any

class Origin:
    def __init__(self, id: str, name: str, category: str, 
                 modifiers: Dict[str, float], 
                 requirements: List[str] = None,
                 conflicts: List[str] = None,
                 description: str = ""):
        self.id = id
        self.name = name
        self.category = category  # biological, machine, etc.
        self.modifiers = modifiers
        self.requirements = requirements or []
        self.conflicts = conflicts or []
        self.description = description

class OriginSystem:
    """
    Manages species origins with unique bonuses.
    """
    def __init__(self):
        self.available_origins: Dict[str, Origin] = {}
        self.active_origin: str = None

    def register_origin(self, origin: Origin):
        self.available_origins[origin.id] = origin
        
    def set_origin(self, origin_id: str) -> bool:
        if origin_id not in self.available_origins: return False
        self.active_origin = origin_id
        return True
