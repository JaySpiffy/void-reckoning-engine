from typing import Dict, Any, Optional
from src.core import balance as bal

class CombatCalculator:
    """Pure functions for combat calculations."""
    
    @staticmethod
    def apply_doctrine_modifiers(attacker: Any, doctrine: str, combat_phase: str, faction_doctrine: Optional[str] = None, intensity: float = 1.0) -> Dict[str, float]:
        """Returns modifiers dict based on doctrine and phase."""
        mods = {"dmg_mult": 1.0, "bs_mod": 0, "defense_mod": 0}
        
        if doctrine == "CHARGE":
            if combat_phase == "MELEE":
                mods["dmg_mult"] = bal.MOD_DOCTRINE_CHARGE_DMG_MULT 
                mods["defense_mod"] = bal.MOD_DOCTRINE_CHARGE_DEFENSE_PENALTY 
                
        elif doctrine == "KITE":
            if combat_phase == "SHOOTING":
                mods["bs_mod"] = bal.MOD_DOCTRINE_KITE_BS_BONUS 
                
        elif doctrine == "DEFEND":
            mods["defense_mod"] = bal.MOD_DOCTRINE_DEFEND_DEFENSE_BONUS
        
        return mods

    @staticmethod
    def check_keywords_attack(attacker: Any, defender: Any, hit_roll: int, is_charge: bool = False) -> tuple:
        """Calculates hit modifiers and special effects based on keyword interactions."""
        att_ma = attacker.ma
        dmg_mult = 1.0
        ap_val = 0
        auto_wound = False
        crit_chance = 0
        
        target_tags = defender.abilities.get("Tags", [])
        
        if "Anti-Infantry" in attacker.abilities and "Infantry" in target_tags:
            dmg_mult += bal.MOD_ANTI_INFANTRY_MULT
            
        if "Anti-Large" in attacker.abilities and ("Vehicle" in target_tags or "Monster" in target_tags):
            dmg_mult += bal.MOD_ANTI_LARGE_MULT
            
        if "Monster-Slayer" in attacker.abilities and "Monster" in target_tags:
            crit_chance += bal.MOD_CRIT_CHANCE_MONSTER_SLAYER
            
        if "Tank-Hunter" in attacker.abilities and "Vehicle" in target_tags:
            ap_val += bal.MOD_TANK_HUNTER_AP_BONUS 

        if "Lethal Hits" in attacker.abilities and hit_roll >= (100 - crit_chance):
            auto_wound = True

        if is_charge:
            att_ma += bal.MOD_MELEE_CHARGE_BASE
            if "Shock" in attacker.abilities or "ChargeBonus" in attacker.abilities:
                att_ma += bal.MOD_MELEE_CHARGE_SHOCK
            
        if "Stealth" in defender.abilities:
            att_ma += bal.MOD_STEALTH_PENALTY

        # [PHASE 5] Exotic Keyword Support
        if "gauss" in attacker.tags and hit_roll >= 90:
             auto_wound = True
             ap_val += 1 

        return att_ma, dmg_mult, ap_val, auto_wound

    @staticmethod
    def calculate_mitigation_v4(defender: Any, ap_val: int, auto_wound: bool = False, armor_override: Optional[int] = None) -> float:
        """Calculates damage mitigation percentage."""
        if auto_wound:
            return 0.0
        
        armor = armor_override if armor_override is not None else defender.armor
        save_target = 7 - (armor // 10)
        save_target += (ap_val // 10)
        
        if "Cover" in defender.abilities:
            save_target -= bal.COVER_SAVE_IMPROVEMENT
            
        save_target = max(bal.SAVE_TARGET_D6_MIN, min(bal.SAVE_TARGET_D6_MAX, save_target))
        stop_chance = (bal.SAVE_TARGET_D6_MAX - save_target) / 6.0
        
        invuln = defender.abilities.get("Invuln", bal.SAVE_TARGET_D6_MAX)
        invuln_chance = (bal.SAVE_TARGET_D6_MAX - invuln) / 6.0
        
        final_mitigation = max(stop_chance, invuln_chance)
        final_mitigation = min(bal.MAX_MITIGATION_PCT, final_mitigation)
        
        return final_mitigation

    @staticmethod
    def calculate_hit_chance(attacker: Any, target: Any) -> int:
        """Calculates hit chance for simplified combat."""
        bs = getattr(attacker, "bs", 50)
        if "Escort" in getattr(target, "name", ""):
            bs -= 10
        elif "Station" in getattr(target, "name", ""):
            bs += 10
        return max(5, min(95, bs))
