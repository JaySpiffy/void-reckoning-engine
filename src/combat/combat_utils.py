import random
from src.utils.profiler import profile_method
import os
import re
from typing import List, Dict, Optional, Any

import src.core.config as config
from src.core import balance as bal
from src.data.weapon_data import WEAPON_DB, get_weapon_stats
from src.models.unit import Unit, Ship, Regiment, Component

from src.utils.rng_manager import get_stream

from src.combat.data.data_loader import DataLoader
from src.combat.calculators.combat_calculator import CombatCalculator


# Legacy compatibility (Deprecated)
def init_combat_rng(seed: Optional[int] = None):
    pass # Managed by RNGManager now

def load_traits():
    return DataLoader.load_traits()

TRAIT_DB = load_traits()

def apply_doctrine_modifiers(attacker, doctrine, combat_phase, faction_doctrine=None, intensity=1.0):
    return CombatCalculator.apply_doctrine_modifiers(attacker, doctrine, combat_phase, faction_doctrine, intensity)

def load_points_db():
    return DataLoader.load_points_db()

POINTS_DB = load_points_db()

def reload_combat_dbs():
    global TRAIT_DB, POINTS_DB
    TRAIT_DB = DataLoader.load_traits()
    p_map = DataLoader.load_points_db()
    POINTS_DB.clear() 
    POINTS_DB.update(p_map)

def check_keywords_attack(attacker, defender, hit_roll, is_charge=False):
    return CombatCalculator.check_keywords_attack(attacker, defender, hit_roll, is_charge)

def calculate_mitigation_v4(defender, ap_val, auto_wound=False, armor_override=None):
    return CombatCalculator.calculate_mitigation_v4(defender, ap_val, auto_wound, armor_override)

def trigger_titan_abilities(attacker, defender, detailed_log_file=None, round_num=0):
    return True, True, {"dmg_mult": 1.0, "ap_mod": 0, "attacks_mod": 1.0}

def find_unit_by_name(all_units, query, universe_name=None):
    return DataLoader.find_unit_by_name(all_units, query, universe_name)

def load_all_units():
    return DataLoader.load_all_units()



def calculate_hit_chance(attacker: Any, target: Any) -> int:
    """
    Calculates hit chance for Star Trek combat.
    Uses base BS and modifies based on target size/tags.
    """
    bs = getattr(attacker, "bs", 50)
    
    # Simple size/agility modifiers
    if "Escort" in getattr(target, "name", ""):
        bs -= 10
    elif "Station" in getattr(target, "name", ""):
        bs += 10
        
    return max(5, min(95, bs))

def roll_d100() -> int:
    """Roll a D100 using the global combat RNG."""
    return get_stream("combat").randint(1, 100)

def execute_weapon_fire(*args, **kwargs):
    """Legacy wrapper for WeaponExecutor.execute_weapon_fire"""
    from src.combat.execution.weapon_executor import WeaponExecutor
    return WeaponExecutor.execute_weapon_fire(*args, **kwargs)
