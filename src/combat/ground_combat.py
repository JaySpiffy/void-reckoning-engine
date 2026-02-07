
import random
from typing import Optional

from src.utils.rng_manager import get_stream

# Legacy compatibility
def init_ground_rng(seed: Optional[int] = None):
    pass
from src.core import balance as bal
from src.combat.combat_utils import calculate_mitigation_v4, apply_doctrine_modifiers

def resolve_melee_phase(active_army, enemy_army, round_num, detailed_log_file=None, tracker=None, doctrine=None, faction_doctrines=None, faction_metadata=None, **kwargs):
    """
    Phase 18: Executes Melee Resolution for Ground Units.
    """
    meleers = [u for u in active_army if u.is_alive() and not u.is_ship()]
    if not meleers: return
    
    faction_metadata = faction_metadata or {}
    att_faction = meleers[0].faction if meleers else "Unknown"
    att_meta = faction_metadata.get(att_faction, {})
    att_f_doc = att_meta.get("faction_doctrine", "STANDARD")
    att_inten = att_meta.get("intensity", 1.0)
    
    universe_rules = kwargs.get("universe_rules")
    if universe_rules and hasattr(universe_rules, "apply_doctrine_modifiers"):
        att_mods = universe_rules.apply_doctrine_modifiers(None, doctrine, "MELEE", att_f_doc, att_inten)
    else:
        att_mods = apply_doctrine_modifiers(None, doctrine, "MELEE", att_f_doc, att_inten)
    dmg_mult = att_mods.get("dmg_mult", 1.0)
    
    # [PHASE 2 Integration] Add Mechanic Hook to Melee
    manager = kwargs.get("manager")

    for attacker in meleers:
        if manager and hasattr(manager, 'mechanics_engine') and manager.mechanics_engine:
             manager.mechanics_engine.apply_mechanic_modifiers(att_faction, [attacker])
             
        for defender in enemy_army:
            if not defender.is_alive(): continue
            hit_chance = attacker.ma

            # Robust attribute access
            charge_bonus = getattr(attacker, 'charge_bonus', 0)
            if round_num == 1 and charge_bonus > 0:
                hit_chance += charge_bonus
            
            roll = get_stream("ground").randint(1, 100)
            if roll <= hit_chance:
                # Use current damage (modifiers applied via apply_mechanic_modifiers)
                s_val = attacker.damage
                
                # Apply Global Multiplier (just in case it wasn't captured in melee_damage_mult)
                global_dmg = getattr(attacker, 'active_mods', {}).get("global_damage_mult", 1.0)
                
                # Calculate Mitigation
                ap_val = getattr(attacker, "ap", 0)
                mit = calculate_mitigation_v4(defender, s_val, ap_val)
                
                # [Lethality] Apply Ground Scalar
                lethality_scalar = bal.GROUND_LETHALITY_SCALAR if not attacker.is_ship() else 1.0
                
                final_dmg = max(1, s_val * (1.0 - mit) * dmg_mult * global_dmg * lethality_scalar)
                
                # Component Targeting
                target_comp = None
                if getattr(defender, 'components', None):
                    target_comp = defender.components[0]

                s_dmg, h_dmg, _, _ = defender.take_damage(final_dmg, target_component=target_comp)
                
                # Phase 250: Update Battle Stats for stalemate detection
                if manager and hasattr(manager, 'battle_stats') and attacker.faction in manager.battle_stats:
                    manager.battle_stats[attacker.faction]["total_damage_dealt"] += final_dmg

                is_kill = not defender.is_alive()
                if tracker: 
                    tracker.log_event("melee_attack", attacker, defender, weapon_name="Combat Blade", damage=final_dmg, h_dmg=h_dmg, destroyed=is_kill)
                
                if detailed_log_file:
                    with open(detailed_log_file, "a", encoding='utf-8') as f:
                        f.write(f"Melee Round {round_num}: {attacker.name} strikes {defender.name} -> {int(final_dmg)} dmg\n")
