
import os
from typing import Dict, List, Any
from src.utils.paradox_parser import ParadoxParser

class DiplomacyExtractor:
    """
    Extracts diplomatic rules, opinion modifiers, and historical biases
    from game files.
    
    Note: Third-party universe-specific diplomacy extraction functions (Stellaris, EaW) have been removed.
    To add custom universe diplomacy extraction, add new methods here.
    """
    
    def __init__(self, mod_root: str):
        self.mod_root = mod_root
        self.parser = ParadoxParser()
