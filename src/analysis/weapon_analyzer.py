from enum import Enum
from typing import Dict, List, Any

class WeaponRole(Enum):
    ANTI_INFANTRY = "Anti-Infantry"
    ANTI_TANK = "Anti-Tank"
    TITAN_KILLER = "Titan-Killer"
    MONSTER_HUNTER = "Monster-Hunter"
    GENERAL_PURPOSE = "General-Purpose"
    ARTILLERY = "Artillery"
    MELEE = "Melee-Duelist"

class WeaponAnalyzer:
    """
    Analyzes raw weapon statistics to separate "Anti-Tank" from "Anti-Infantry" weapons.
    Used by AI to make smarter target selection decisions.
    
    Principles:
    - High Strength (>6) + High AP (< -2) = Anti-Tank
    - High Shots (Rapid Fire/Heavy > 3) + Low Strength = Anti-Infantry
    - Extreme Strength (>12) = Titan-Killer
    """
    
    @staticmethod
    def classify_weapon(stats: Dict[str, Any]) -> str:
        """
        Determines the primary role of a weapon.
        Stats expectations: {'S': int, 'AP': int, 'D': float/int, 'Range': int, 'Type': str}
        """
        s = stats.get("S", 4)
        ap = stats.get("AP", 0)
        d = stats.get("D", 1)
        rng = stats.get("Range", 24)
        w_type = stats.get("Type", "Rapid Fire 1")
        
        # 1. Titan Killers (Volcano Cannons, Flux Missiles)
        if s >= 14 or (s >= 10 and d >= 3.5 and getattr(stats, 'Macro', False)):
            return WeaponRole.TITAN_KILLER.value
            
        # 2. Melee Duelist (Power Fists, Thunder Hammers)
        # Prioritize Melee check because High Strength Melee is not Anti-Tank (usually) in this context
        if rng == 0 or "Melee" in w_type:
            if s >= 8 or (s >= 5 and ap <= -2 and d >= 2):
                return WeaponRole.MELEE.value # High value melee
            # Chaff melee is just general purpose/anti-infantry usually
            if s <= 4:
                return WeaponRole.ANTI_INFANTRY.value
            
        # 3. Anti-Tank (Lascannons, Meltas)
        # Criteria: S8+, or S7 with good AP
        if s >= 8:
            return WeaponRole.ANTI_TANK.value
        if s >= 7 and ap <= -2:
            return WeaponRole.ANTI_TANK.value
        if s >= 6 and ap <= -3 and d >= 2: # Melta-like
            return WeaponRole.ANTI_TANK.value

        # 4. Artillery (Basilisk, mortars)
        if rng >= 100 and "Blast" in w_type:
            return WeaponRole.ARTILLERY.value
            
        # 5. Anti-Infantry (Bolters, Flamers)
        # Criteria: Low Strength, High Volume
        if s <= 5 and ap >= -1 and d == 1:
            return WeaponRole.ANTI_INFANTRY.value
        if "Blast" in w_type and s <= 6:
            return WeaponRole.ANTI_INFANTRY.value

        # 6. Monster Hunter (Heavy Bolters, Autocannons)
        if s >= 5 and s <= 7 and d >= 2:
            return WeaponRole.MONSTER_HUNTER.value
            
        return WeaponRole.GENERAL_PURPOSE.value

    @staticmethod
    def calculate_efficiency_score(stats: Dict[str, Any], target_profile: str = "MEQ") -> float:
        """
        Calculates a heuristic score (0-100) of how good this weapon is against a target.
        Profiles: 
         - GEQ (T3, 5+)
         - MEQ (T4, 3+)
         - TEQ (T5, 2+)
         - VEHICLE (T7, 3+)
         - KNIGHT (T8, 3+, 5++ invuln implied)
        """
        s = stats.get("S", 4)
        ap = stats.get("AP", 0)
        d = stats.get("D", 1)
        
        # Target Stats
        t_stats = {
            "GEQ": {"T": 3, "Sv": 5},
            "MEQ": {"T": 4, "Sv": 3},
            "TEQ": {"T": 5, "Sv": 2},
            "VEHICLE": {"T": 7, "Sv": 3},
            "KNIGHT": {"T": 8, "Sv": 3}
        }
        
        target = t_stats.get(target_profile, t_stats["MEQ"])
        t_tough = target["T"]
        t_save = target["Sv"]
        
        # 1. Wound Roll Math
        if s >= t_tough * 2: wound_prob = 5/6 # 2+
        elif s > t_tough: wound_prob = 4/6 # 3+
        elif s == t_tough: wound_prob = 3/6 # 4+
        elif s < t_tough and s * 2 > t_tough: wound_prob = 2/6 # 5+
        else: wound_prob = 1/6 # 6+
        
        # 2. Save Roll Math (AP is usually negative in 8th/10th, or positive modifier in older? 
        # weapon_registry.json has "AP": -1 or "AP": 0.
        # Assuming modern AP (negatives subtract from save roll).
        # Save 3+ means roll >= 3. Modified roll D - AP >= Sv. => D >= Sv + AP.
        # Wait, AP reduces the die. Rolled 3 with AP-1 becomes 2. Fails 3+.
        # So effective save target = Sv + abs(AP).
        # AP is usually stored as negative integer (e.g. -1). abs(-1) = 1.
        # Or positive integer in older editions.
        # weapon_data.py parse: ap = int(ap_val) if str(ap_val).replace("-","").isdigit() else 0.
        # It handles "-1" correctly.
        
        eff_save = t_save + abs(ap)
        if eff_save > 7: eff_save = 7 # 7+ save is impossible on D6 (usually) unless invuln
        
        # Prob of FAILING save = (eff_save - 1) / 6. 
        # e.g. Save 3+. Fails on 1, 2. (2/6). Passes 3,4,5,6.
        # With AP-1, Save effectively 4+. Fails on 1,2,3 (3/6).
        # Fail Prob = (Effective_Target - 1) / 6.
        # Max fail prob is 1.0 (no save).
        
        fail_save_prob = (eff_save - 1) / 6.0
        fail_save_prob = min(1.0, max(0.0, fail_save_prob))
        
        # 3. shots? We don't have shots count in stats easily (It's in "Type" string "Rapid Fire 2").
        # Detailed shot parsing is complex. Assume 1 shot for "efficiency per shot".
        
        damage_potential = wound_prob * fail_save_prob * d
        
        return damage_potential * 10
