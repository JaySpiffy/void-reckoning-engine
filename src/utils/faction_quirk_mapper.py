
from typing import Dict, Any

class FactionQuirkMapper:
    """
    Standardizes the mapping of game-specific data to Faction quirks.
    Centralizes the logic previously scattered across parsers.
    
    Note: Third-party universe-specific quirk mapping functions (Stellaris, EaW) have been removed.
    To add custom universe quirk mapping, add new methods here.
    """
    
    def merge_quirks(self, *quirk_dicts) -> Dict[str, Any]:
        """
        Merges multiple quirk dictionaries. Later dictionaries override earlier ones.
        Numeric modifiers are generally multiplied or added depending on context,
        but for simplicity we'll just override for now unless specific merging logic is needed.
        """
        final_quirks = {}
        
        for qd in quirk_dicts:
            for k, v in qd.items():
                # Specialized merging for multipliers?
                if k.endswith("_mult") and k in final_quirks:
                    final_quirks[k] *= v # Accumulate multipliers
                elif k == "diplomacy_bonus" and k in final_quirks:
                    final_quirks[k] += v # Additive for diplo
                else:
                    final_quirks[k] = v
                    
        return final_quirks
