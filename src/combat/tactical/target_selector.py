from typing import List, Optional, Tuple
from src.utils.profiler import profile_method

class TargetSelector:
    """
    Handles target selection logic based on tactical doctrines and unit roles.
    """
    
    @staticmethod
    @profile_method
    def select_target_by_doctrine(attacker, enemies: List, doctrine: str, grid, sim_time: float = 0.0) -> Tuple[Optional[object], Optional[object]]:
        """
        Selects the best target and specific hardpoint based on combat doctrine.
        Returns: (target_unit, target_component)
        """
        if not enemies: return None, None
        
        # [PERF] Target Caching
        # Only re-evaluate target every 5-10 ticks (approx 0.5s - 1.0s)
        # unless current target is dead or out of range.
        current_time = sim_time
        if not hasattr(attacker, '_target_cache'):
            attacker._target_cache = None
            attacker._target_ttl = 0
            
        if attacker._target_cache and attacker._target_ttl > current_time:
            # Verify cached target is still valid
            t = attacker._target_cache
            # [RANGE ENFORCEMENT] Reduce cache range to be more realistic. 
            # If target is too far, we should re-evaluate.
            max_cache_dist = 600 if getattr(attacker, 'is_ship', lambda: False)() else 150
            if t.is_alive() and grid.get_distance(attacker, t) <= max_cache_dist:
                return t, getattr(attacker, '_target_comp_cache', None)
        
        # [PHASE 17.8] Deprioritize Routing Units
        active_enemies = [e for e in enemies if getattr(e, 'morale_state', 'Steady') != "Routing"]
        eligible_targets = active_enemies if active_enemies else enemies
        
        def get_target_score(e):
            dist = grid.get_distance(attacker, e)
            score = dist
            
            # Role Matching
            roles = getattr(attacker, 'tactical_roles', [])
            tags = e.abilities.get("Tags", [])
            
            # [ADVANCED AI] Focus Fire on Interdictors if Trapped
            if getattr(attacker, 'is_trapped', False):
                if "Interdictor" in tags or "Gravity_Well" in e.abilities:
                    score -= 100 # Extreme priority to break the trap
                    
            # [ADVANCED AI] Protect Friendly Interdictors
            faction = getattr(attacker, 'faction', 'Unknown')
            friendlies_near_target = grid.query_units_in_range(e.grid_x, e.grid_y, radius=10, faction_filter=faction)
            has_friendly_interdictor_near = any("Interdictor" in getattr(f, 'tags', []) or "Gravity_Well" in getattr(f, 'abilities', {}) for f in friendlies_near_target)
            
            if has_friendly_interdictor_near:
                score -= 10 # Protect the Interdictor!
            
            # Anti-Tank vs Vehicle/Monster
            if "Anti-Tank" in roles:
                if "Vehicle" in tags or "Monster" in tags or getattr(e, 'toughness', 4) >= 7:
                    score -= 15 
                    
            # Anti-Infantry vs Infantry
            elif "Anti-Infantry" in roles:
                if "Vehicle" not in tags and "Monster" not in tags and getattr(e, 'toughness', 4) <= 5:
                    score -= 10
                    
            # Titan Killer vs Titan/Vehicle
            elif "Titan-Killer" in roles:
                if "Titan" in tags: score -= 50
                elif "Vehicle" in tags: score -= 20
                
            return score
    
        # 3.2 Spatial Indexing for Target Selection
        candidates = []
        if hasattr(grid, 'spatial_index') and grid.spatial_index:
            if doctrine == "KITE":
                 candidates = grid.spatial_index.query_circle(attacker.grid_x, attacker.grid_y, radius=30)
            else:
                 candidates = grid.spatial_index.query_nearest(attacker.grid_x, attacker.grid_y, count=20)
                 candidates = [u for u, d in candidates]
        
        attacker_faction = getattr(attacker, 'faction', None)
        valid_enemies = []
        source_pool = candidates if candidates else enemies
        
        for u in source_pool:
             if u is attacker: continue
             if not u.is_alive(): continue
             if u.faction == attacker_faction: continue
             valid_enemies.append(u)
             
        if not valid_enemies and not candidates:
             valid_enemies = [e for e in enemies if e.is_alive()]

        target_unit = None
        if valid_enemies:
             if doctrine == "KITE":
                  target_unit = min(valid_enemies, key=lambda e: getattr(e, 'current_hp', 100))
             else:
                  target_unit = min(valid_enemies, key=get_target_score)
        
        if not target_unit:
            return None, None

        # [PHASE 17.5] Sub-Targeting (Hardpoint Sniping - EaW Style)
        target_component = None
        if hasattr(target_unit, 'components') and target_unit.components:
            # 1. If shields are up, target Shield Generator first (if it exists)
            shields_up = getattr(target_unit, 'shield_current', 0) > 0
            if shields_up:
                gen = next((c for c in target_unit.components 
                          if getattr(c, 'type', None) == "Shield" and not getattr(c, 'is_destroyed', False)), None)
                if gen: target_component = gen

            # 2. Prioritize FINISHING what we started (if already damaged)
            if not target_component:
                target_component = next((c for c in target_unit.components 
                                       if not getattr(c, 'is_destroyed', False) 
                                       and getattr(c, 'current_hp', 1) < getattr(c, 'max_hp', 1)), None)
            
            # 3. Otherwise, target Weapons or Engines if unit is healthy
            if not target_component and target_unit.current_hp > (target_unit.base_hp * 0.5):
                # Prioritize Weapons to reduce incoming damage
                weap = next((c for c in target_unit.components 
                           if (getattr(c, 'type', None) == "Weapon" or type(c).__name__ == "WeaponComponent") 
                           and not getattr(c, 'is_destroyed', False)), None)
                if weap: target_component = weap
        
        # [EaW Logic] If attacker is a fighter/bomber, and target hull is massive but shields are up, 
        # deprioritize hull damage significantly (harder to hurt capital hull with light guns)
        attacker_class = (getattr(attacker, 'unit_class', 'unknown') or 'unknown').lower()
        if attacker_class in ["fighter", "interceptor", "bomber"]:
            if target_unit.unit_class in ["cruiser", "battleship", "titan"] and shields_up and not target_component:
                 # Bombers usually have torps for hull, but let's assume headless light guns unless specialized
                 if "Anti-Ship" not in attacker_class:
                      # If we haven't found a component (like a hardpoint) to hit, we're essentially splash damaging shields
                      pass 

        # [PERF] Cache result
        attacker._target_cache = target_unit
        attacker._target_comp_cache = target_component
        attacker._target_ttl = sim_time + 1.0 # Cache for 1 second

        return target_unit, target_component
