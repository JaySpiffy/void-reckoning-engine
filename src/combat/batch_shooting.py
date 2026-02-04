from typing import List, Dict, Tuple, Any
from src.core import gpu_utils
from src.core.gpu_utils import log_backend_usage
from src.combat.combat_utils import check_keywords_attack
import logging

def resolve_shooting_batch(
    attackers: List[Any], 
    target_map: Dict[int, Any], 
    distance_map: Dict[int, float],
    active_units_dict: Dict[int, Any],
    formation_modifiers: Dict[int, Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Resolves shooting for a batch of attackers against their pre-assigned targets.
    
    Args:
        attackers: List of Unit objects firing.
        target_map: Dict {attacker_id: target_id} from GPUTracker.
        distance_map: Dict {attacker_id: distance} from GPUTracker.
        active_units_dict: Lookup dict {unit_id: UnitObject} for all active units.
        
    Returns:
        List of result dictionaries to be applied/logged.
        [{
            "attacker": Unit,
            "target": Unit,
            "damage": float,
            "is_hit": bool,
            "weapon_name": str,
            "logs": dict
        }]
    """
    results = []
    
    
    xp = gpu_utils.get_xp()
    log_backend_usage("BatchShooting", logging.getLogger(__name__))
    
    # 1. Prepare Data Vectors
    # We need aligned arrays for:
    # BS, HitMod, WeaponStr, WeaponAP, WeaponDmg, TargetToughness, TargetArmor, TargetInvuln
    
    # Since weapons differ per unit, and units might have multiple weapons, 
    # we either flat-map (Attacker-Weapon pairs) or process simply for primary weapon.
    # Architecture Limitation: Units have components.
    # SIMPLIFICATION: We will fire the PRIMARY ranged weapon for each attacker.
    
    valid_pairs = []
    
    for att in attackers:
        att_id = id(att)
        if att_id not in target_map: continue
        
        target_id = target_map[att_id]
        if target_id not in active_units_dict: continue
        
        target = active_units_dict[target_id]
        dist = distance_map.get(att_id, 9999.0)
        
        # Select Valid Weapons
        # Filter for ranged weapons that are in range
        weapons = [c for c in att.components if c.type == "Weapon" and not c.is_destroyed]
        
        valid_count = 0 
        for w in weapons:
             rng = w.weapon_stats.get("Range", 24)
             # Weapon Arc Check (Preliminary Filter)
             # We don't have vector arc logic yet, BUT we can check arc stats if we had geometry.
             # For now, blindly fire all in range (360 arcs assumed for batch)
             if dist <= rng:
                 valid_pairs.append((att, target, w, dist))
                 valid_count += 1

        
    if not valid_pairs:
        return []
        
    n = len(valid_pairs)
    
    # 2. Build Arrays
    # BS Array (Ballistic Skill)
    bs_arr = []
    modifiers_arr = []
    
    # Weapon Stats
    str_arr = []
    ap_arr = []
    dmg_mult_arr = []
    attacks_arr = []
    
    # Target Stats
    toughness_arr = [] # Toughness currently not used in simple math but good for future
    armor_arr = []
    invuln_arr = []
    cover_arr = []
    md_arr = []
    
    for att, tgt, wpn, dist in valid_pairs:
        # Attacker Stats
        bs = getattr(att, 'bs', 50)
        # Mods
        bs_mod = 0
        if dist > 50: bs_mod -= 10 
        if getattr(att, 'is_suppressed', False): bs_mod -= 10 
        
        # --- Formation Modifiers (Phase 30) ---
        att_form_mods = formation_modifiers.get(id(att), {}) if formation_modifiers else {}
        bs_mod += int((att_form_mods.get("accuracy_mult", 1.0) - 1.0) * 100)
        dmg_mult = att_form_mods.get("damage_mult", 1.0)
        ap_bonus = int(att_form_mods.get("ap_bonus", 0))
        
        # Phase 250: Accuracy Floor
        bs_total = max(15, bs + bs_mod + 5)
        bs_arr.append(bs_total)
        
        # Weapon Stats
        stats = wpn.weapon_stats
        combined_s = (stats.get("S", stats.get("Str", 4))) * 10 * stats.get("D", 1) * dmg_mult
        str_arr.append(combined_s)
        ap_arr.append(stats.get("AP", 0) + ap_bonus)
        attacks_arr.append(stats.get("Attacks", stats.get("A", 1)))
        
        # Target Stats
        armor_arr.append(getattr(tgt, 'armor', 0))
        invuln_arr.append(tgt.abilities.get("Invuln", 7))
        cover_arr.append(1.0 if "Cover" in tgt.abilities else 0.0)
        
        # Phase 32: Fortress Reduction (Static targets)
        is_fortress = "Fortress" in tgt.abilities.get("Tags", [])
        dmg_mult_arr.append(0.5 if is_fortress else 1.0)
        
        # [NEW] Evasion Stats (Melee Defense)
        md_arr.append(getattr(tgt, 'md', 50))
        
    # To GPU
    gpu_bs = gpu_utils.to_gpu(bs_arr)
    gpu_str = gpu_utils.to_gpu(str_arr)
    gpu_ap = gpu_utils.to_gpu(ap_arr)
    gpu_armor = gpu_utils.to_gpu(armor_arr)
    gpu_invuln = gpu_utils.to_gpu(invuln_arr)
    gpu_cover = gpu_utils.to_gpu(cover_arr)
    gpu_attacks = gpu_utils.to_gpu(attacks_arr)
    gpu_dmg_mult = gpu_utils.to_gpu(dmg_mult_arr)
    gpu_md = gpu_utils.to_gpu(md_arr)
    
    # 3. Vectorized Simulation

    
    # A. Hit Rolls
    # Integrate Evasion (MD) into Hit Probabilities
    # Prob = BS% * (1.0 - MD%)
    bs_probs = gpu_bs / 100.0
    md_penalty = gpu_md / 100.0
    probs = bs_probs * (1.0 - md_penalty)
    probs = xp.maximum(0.05, xp.minimum(0.95, probs)) # Safety clamp
    
    if hasattr(xp, 'random'):
        hit_counts = xp.random.binomial(gpu_attacks, probs)
        # Critical Hits: nat 1-5 is 5% of rolls. P(Crit|Hit) = 5/BS.
        crit_probs = xp.where(gpu_bs > 0, 5.0 / gpu_bs, 0.0)
        crit_probs = xp.minimum(1.0, crit_probs)
        crit_counts = xp.random.binomial(hit_counts, crit_probs)
    else:
        # Fallback to NumPy
        import numpy as np
        hit_counts_cpu = np.random.binomial(gpu_utils.to_cpu(gpu_attacks), gpu_utils.to_cpu(probs))
        c_probs_cpu = np.where(gpu_utils.to_cpu(gpu_bs) > 0, 5.0 / gpu_utils.to_cpu(gpu_bs), 0.0)
        c_probs_cpu = np.minimum(1.0, c_probs_cpu)
        crit_counts_cpu = np.random.binomial(hit_counts_cpu, c_probs_cpu)
        
        hit_counts = gpu_utils.to_gpu(hit_counts_cpu)
        crit_counts = gpu_utils.to_gpu(crit_counts_cpu)
    
    # Boolean mask for logging (at least one hit)
    hits = (hit_counts > 0)
    
    # Auto-Wound Logic (Lethal Hits)
    # If Lethal Hits trait exists (passed via flags?), auto-wound.
    # For now, just Crit -> ignore armor? Or extra damage?
    # Implementing Crit -> 1.5x Damage for now as generic rule
    
    # B. Damage Calculation
    # Mitigation V4 Port
    save_target = 7.0 - (gpu_armor // 10.0) + (gpu_ap // 10.0)
    save_target -= gpu_cover 
    
    # Clamp Save [2, 6]
    save_target = xp.maximum(2.0, xp.minimum(6.0, save_target))
    
    # Stop Chance
    stop_chance = (6.0 - save_target) / 6.0
    
    # Invuln Chance
    invuln_chance = (6.0 - gpu_invuln) / 6.0
    
    # Final Mitigation
    final_mit = xp.maximum(stop_chance, invuln_chance)
    final_mit = xp.minimum(0.95, final_mit) 
    
    # Raw Damage
    # Criticals might bypass mitigation or deal extra?
    # Let's say Crits reduce mitigation by half (placeholder precision rule)
    # actual_mit = xp.where(crits, final_mit * 0.5, final_mit)
    
    raw_damage = gpu_str * (1.0 - final_mit)
    final_damage = xp.maximum(1.0, raw_damage)
    
    # Apply Suppression Damage Reduction? 
    # If attacker is suppressed, damage might be reduced?
    # Logic in loop: `if getattr(att, 'is_suppressed', False): bs_mod -= 20`
    # Already handled in BS calc.
    
    # Mask with Hits and Multiply by Number of Hits
    # hit_counts already accounts for number of successful attacks.
    applied_damage = hit_counts * final_damage * gpu_dmg_mult
    
    # Apply Critical Bonus (50% extra for each critical hit)
    # Note: hit_counts includes crit_counts. Each crit is already in hit_counts once.
    # We add 0.5 * final_damage for each crit.
    applied_damage += crit_counts * (final_damage * 0.5)
    

    
    # [Synchronization] Ensure GPU is done before transfer
    gpu_utils.synchronize()
    
    # 4. Pack Results
    cpu_hits = gpu_utils.to_cpu(hits)
    cpu_dmg = gpu_utils.to_cpu(applied_damage)
    cpu_hit_counts = gpu_utils.to_cpu(hit_counts)
    cpu_crit_counts = gpu_utils.to_cpu(crit_counts)
    cpu_bs = gpu_utils.to_cpu(gpu_bs)
    
    for i in range(n):
        att, tgt, wpn, dist = valid_pairs[i]
        
        is_hit = bool(cpu_hits[i])
        dmg = float(cpu_dmg[i])
        hit_count = int(cpu_hit_counts[i])
        crit_count = int(cpu_crit_counts[i])
        threshold = int(cpu_bs[i])
        
        res = {
            "attacker": att,
            "target": tgt,
            "weapon": wpn,
            "is_hit": is_hit,
            "damage": dmg,
            "hit_count": hit_count,
            "crit_count": crit_count,
            "threshold": threshold,
            "dist": dist
        }
        results.append(res)
        
    return results
