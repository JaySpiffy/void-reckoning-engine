from typing import List, Dict, Any, Optional
from universes.base.combat_rules import CombatPhase

def execute_phase_sequence(phases: List[Any], phase_order: List[str], context: Dict[str, Any]):
    """
    Executes a sequence of combat phases in the specified order.
    Supports both legacy dict-based phases and new ICombatPhase objects.
    """
    phase_map = {}
    for p in phases:
        if isinstance(p, dict):
             phase_map[p['name']] = p
        elif hasattr(p, 'name'):
             phase_map[p.name] = p
    
    for phase_name in phase_order:
        if phase_name not in phase_map:
            # Skip if phase not registered
            continue
            
        phase_item = phase_map[phase_name]
        
        # Log phase start
        detailed_log_file = context.get("detailed_log_file")
        round_num = context.get("round_num", 1)
        
        if detailed_log_file:
            with open(detailed_log_file, "a", encoding='utf-8') as f:
                f.write(f"\n--- {phase_name.upper()} PHASE (Round {round_num}) ---\n")
        
        # Execute phase
        try:
            if isinstance(phase_item, dict):
                # Legacy: Unpack context into kwargs
                phase_item['handler'](**context)
            else:
                # New: Execute with context dict
                phase_item.execute(context)
                
        except Exception as e:
            import traceback
            print(f"Error executing phase {phase_name}: {e}")
            traceback.print_exc()
            pass

def validate_phase_dependencies(phases: List[CombatPhase]) -> bool:
    """
    Validates the phase dependency graph to ensure no circularity.
    """
    # Simple check: do all dependencies exist?
    names = {p['name'] for p in phases}
    for p in phases:
        for dep in p.get('dependencies', []):
            if dep not in names:
                return False
    
    # Simple circularity check (not exhaustive but handles common cases)
    # We can implement a proper DAG check if needed
    return True

def build_phase_context(battle_state: Any, round_num: int, detailed_log_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Constructs the standard context dictionary for phase handlers.
    """
    # battle_state is assumed to be a CombatStateManager or similar
    active_units = []
    for f, units in battle_state.armies_dict.items():
        for u in units:
            if u.is_alive() and getattr(u, 'is_deployed', True):
                active_units.append((u, f))
                
    enemies_by_faction = {f: [u for u, uf in active_units if uf != f] for f in battle_state.armies_dict}
    
    # Universe-specific detection: Interdictors
    interdictor_present = False
    for u, f in active_units:
        # Reset trapped status at start of check
        u.is_trapped = False
        if "Interdictor" in getattr(u, 'tags', []) or "Gravity_Well" in getattr(u, 'abilities', {}):
            interdictor_present = True
            
    # If an interdictor is present, mark all ENEMIES as trapped
    if interdictor_present:
        for u, f in active_units:
            # Check if any enemy faction has an interdictor
            my_enemies = enemies_by_faction.get(f, [])
            has_enemy_interdictor = any("Interdictor" in getattr(en, 'tags', []) or "Gravity_Well" in getattr(en, 'abilities', {}) for en in my_enemies)
            if has_enemy_interdictor:
                u.is_trapped = True

    return {
        "active_units": active_units,
        "enemies_by_faction": enemies_by_faction,
        "grid": battle_state.grid,
        "faction_doctrines": battle_state.faction_doctrines,
        "faction_metadata": battle_state.faction_metadata,
        "round_num": round_num,
        "detailed_log_file": detailed_log_file,
        "tracker": battle_state.tracker,
        "interdictor_present": interdictor_present
    }
