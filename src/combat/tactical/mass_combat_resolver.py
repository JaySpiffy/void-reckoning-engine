
import random
from typing import Dict, List, Any
from src.combat.combat_state import CombatState
from src.combat.combat_tracker import CombatTracker

class MassCombatResolver:
    """
    Handles statistical resolution for large-scale battles (> 50 units).
    Uses Lanchester's Laws approximation to speed up simulation O(1) vs O(N^2).
    """
    
    @staticmethod
    def resolve_round(state: CombatState, threshold: int = 50) -> bool:
        """
        Executes a single round of mass combat.
        Returns True if battle should continue, False if ended.
        """
        tracker = state.tracker
        state.round_num += 1
        tracker.start_round(state.round_num)
        
        # 1. Calculate Aggregate Power per Faction
        # Structure: {faction: {'ap': float, 'hp': float, 'units': List[Unit]}}
        forces = {}
        
        unit_count = 0
        
        for faction, units in state.armies_dict.items():
            active_units = [u for u in units if u.is_alive() and getattr(u, 'is_deployed', True)]
            if not active_units: continue
            
            unit_count += len(active_units)
            
            total_ap = 0.0
            total_hp = 0.0
            
            for u in active_units:
                # Calculate Effective AP (Damage * Accuracy * FireRate)
                # Simplified: Base Damage * 0.5 (Avg Hit Rate)
                # We can refine this by checking weapons
                
                u_ap = u.base_damage
                # Check weapons for more accurate AP
                if hasattr(u, 'weapons'):
                    w_ap = 0
                    for w in u.weapons:
                         # dmg * shots * acc
                         d = w.get("damage", 1)
                         s = w.get("shots", 1)
                         a = w.get("accuracy", 50) / 100.0
                         w_ap += (d * s * a)
                    if w_ap > 0: u_ap = w_ap
                    
                total_ap += u_ap
                total_hp += u.current_hp
                
                # Log Snapshot (Light version to avoid spam)
                # tracker.log_snapshot(u) # Skip snapshot in Mass Mode for speed?
                
            forces[faction] = {
                'ap': total_ap,
                'hp': total_hp,
                'units': active_units,
                'count': len(active_units)
            }
        
        if len(forces) < 2:
            return False # Battle Over
            
        # Log Start
        if state.round_num == 1 or state.round_num % 5 == 0:
            print(f"[MASS COMBAT] Round {state.round_num} | {unit_count} Units Active")
            for f, data in forces.items():
                print(f"  > {f}: {data['count']} ships, {int(data['hp'])} HP, {int(data['ap'])} Dmg")

        # 2. Apply Damage (Lanchester Square Law Logic)
        # Each faction deals damage to all enemies proportionally? 
        # Multi-faction is tricky. Simplified: Everyone hits their "Primary Target" faction?
        # Or just split damage among all enemies.
        
        factions = list(forces.keys())
        
        damage_dealt = {f: 0.0 for f in factions}
        
        # Calculate Damage Output
        for attacker in factions:
            enemies = [f for f in factions if f != attacker]
            if not enemies: continue
            
            atk_power = forces[attacker]['ap']
            
            # Divide fire among enemies (Equal split for simplicity)
            split_dmg = atk_power / len(enemies)
            
            for defender in enemies:
                # Mitigation Factor (Avg Mitigation approx 30%?)
                # We could calculate avg mitigation of defender fleet
                # armor_mitigation = ...
                # Let's assume 20% baseline mitigation for mass battles to account for evasion/armor
                mitigated_dmg = split_dmg * 0.8 
                
                damage_dealt[defender] += mitigated_dmg
                tracker.log_damage(attacker, defender, mitigated_dmg, "MassFire")
                
        # 3. Apply Casualties
        for faction, dmg in damage_dealt.items():
            if dmg <= 0: continue
            
            force_data = forces[faction]
            units = force_data['units']
            
            # Distribute damage
            # We can pick random units to die (Concentrated Fire approximation)
            # or spread it out (Area Fire). 
            # Concentrated is more realistic for naval efficiency (kill ships = remove guns)
            
            # Lanchester Square Law implies concentrated fire efficiency.
            # We drain HP from a "pool" but need to map it to units to remove them.
            
            # Shuffle units to randomize casualties
            random.shuffle(units)
            
            remaining_dmg = dmg
            
            # Overkill protection? No, mass combat assumes efficiency.
            
            casualties = 0
            for u in units:
                if remaining_dmg <= 0: break
                
                # Calculate mitigation for this specific unit to affect incoming damage?
                # We applied generic mitigation earlier. 
                
                take = min(u.current_hp, remaining_dmg)
                u.current_hp -= take
                remaining_dmg -= take
                
                if u.current_hp <= 0:
                    u.is_destroyed = True
                    casualties += 1
                    state.track_unit_destruction(faction, u, "MassFire")
            
            # print(f"  > {faction} took {int(dmg)} dmg -> {casualties} lost.")
            
        return True

