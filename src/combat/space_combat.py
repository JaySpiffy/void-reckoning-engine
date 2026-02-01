
import random
from typing import Optional

from src.utils.rng_manager import get_stream

# Legacy compatibility
def init_space_rng(seed: Optional[int] = None):
    pass
from src.core import balance as bal
from src.combat.combat_utils import apply_doctrine_modifiers

def resolve_boarding_phase(active_army, enemy_army, round_num, detailed_log_file=None, current_distance=60, tracker=None, doctrine=None, **kwargs):
    """
    Executes Boarding Actions for Ships.
    """
    boarders = [u for u in active_army if u.is_alive() and u.is_ship() and "Star Fort" not in u.abilities.get("Tags", [])] 
    if not boarders: return
    if current_distance > 5: return

    att_bonus = 0
    if doctrine == "CHARGE": att_bonus = 1

    for boarder in boarders:
        if get_stream("space").random() > 0.10: continue
        targets = [u for u in enemy_army if u.is_alive() and u.is_ship()]
        if not targets: break
        target = get_stream("space").choice(targets)
        
        # Uses resolve_boarding for the actual mechanic? 
        # No, the logic was inline in phases. I will make it use resolve_boarding from THIS file.
        resolve_boarding(boarder, target, detailed_log_file, round_num, tracker, **kwargs)

def resolve_boarding(attacker, defender, detailed_log_file=None, round_num=0, tracker=None, **kwargs):
    """
    Resolves a Boarding Action between two ships.
    Delegates to universe_rules if available, otherwise uses a generic default.
    """
    universe_rules = kwargs.get("universe_rules")
    if universe_rules and hasattr(universe_rules, "resolve_boarding"):
        return universe_rules.resolve_boarding(attacker, defender, detailed_log_file, round_num, tracker)

    # Generic Placeholder/Default logic
    from src.core import balance as bal
    hull_per_die = bal.BOARDING_HULL_PER_DIE
    boarding_dmg = bal.BOARDING_DAMAGE_PER_SUCCESS

    att_dice = max(1, attacker.max_hp // hull_per_die)
    def_dice = max(1, defender.max_hp // hull_per_die)
    
    att_score = sum(get_stream("space").randint(1, 6) for _ in range(att_dice))
    def_score = sum(get_stream("space").randint(1, 6) for _ in range(def_dice))
    
    if att_score > def_score:
        diff = att_score - def_score
        damage = diff * boarding_dmg
        defender.take_damage(damage)
        
        # Phase 250: Update Battle Stats for stalemate detection
        manager = kwargs.get("manager")
        if manager and hasattr(manager, 'battle_stats') and attacker.faction in manager.battle_stats:
            manager.battle_stats[attacker.faction]["total_damage_dealt"] += damage
            
        if tracker: tracker.log_event("boarding", attacker, defender, weapon_name="Generic Boarding", damage=damage)
    elif def_score > att_score:
        diff = def_score - att_score
        damage = diff * 50
        attacker.take_damage(damage)
        
        # Phase 250: Update Battle Stats for stalemate detection
        manager = kwargs.get("manager")
        if manager and hasattr(manager, 'battle_stats') and defender.faction in manager.battle_stats:
            manager.battle_stats[defender.faction]["total_damage_dealt"] += damage
            
        if tracker: tracker.log_event("boarding", defender, attacker, weapon_name="Generic Defense", damage=damage)
