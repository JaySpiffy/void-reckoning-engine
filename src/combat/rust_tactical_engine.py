from typing import List, Dict, Any, Optional
import time
from src.combat.tactical_engine import CombatState
# Import the Rust module
try:
    from void_reckoning_bridge import RustCombatEngine
except ImportError:
    print("Warning: void_reckoning_bridge not found. Rust combat will be unavailable.")
    RustCombatEngine = None

class RustTacticalEngine:
    """
    Wrapper for the Rust-based High Performance Combat Engine.
    Delegates heavy calculation to the native module.
    """
    def __init__(self, width=100.0, height=100.0):
        self.width = width
        self.height = height
        self.rust_engine = None
        if RustCombatEngine:
            self.rust_engine = RustCombatEngine(width, height)
            
    def initialize_battle(self, armies_dict: Dict[str, List[Any]]):
        """
        Converts Python Unit objects to Rust CombatUnits and populates the engine.
        """
        if not self.rust_engine: return
        
        faction_map = {f: i for i, f in enumerate(armies_dict.keys())}
        self.faction_lookup = list(armies_dict.keys())
        
        unit_id_counter = 1
        
        for faction, units in armies_dict.items():
            f_idx = faction_map.get(faction, 0)
            
            # Simple grid placement
            # Attackers Left, Defenders Right
            base_x = 10.0 if f_idx == 0 else 90.0
            
            for i, unit in enumerate(units):
                # Unique ID management
                # We need to map python objects back? Or just use ID?
                # Ideally, unit.id is consistent. But unit.id might be string?
                # Let's generate a temporary battle ID.
                bid = unit_id_counter
                unit_id_counter += 1
                unit.battle_id = bid # Tag the python object
                
                # Extract Weapons
                weapons_data = []
                # Check weapon components
                if hasattr(unit, 'weapon_comps'):
                    for w in unit.weapon_comps:
                         # name, type, range, damage, accuracy, cooldown
                         # Map weapon type string to what Rust expects
                         w_type = "Kinetic"
                         if hasattr(w, 'weapon_stats'):
                             w_type = w.weapon_stats.get("type", "Kinetic")
                             
                         # Accuracy?
                         acc = 0.8 # Default
                         if hasattr(w, 'accuracy'): acc = w.accuracy
                         
                         weapons_data.append((
                             w.name,
                             w_type,
                             float(w.weapon_stats.get("range", 20.0)) if hasattr(w, 'weapon_stats') else 20.0,
                             float(w.weapon_stats.get("damage", 10.0)) if hasattr(w, 'weapon_stats') else 10.0,
                             acc,
                             float(w.weapon_stats.get("cooldown", 1.0)) if hasattr(w, 'weapon_stats') else 1.0
                         ))
                
                # If no weapons but has Unit stats
                if not weapons_data and hasattr(unit, 'damage'):
                    weapons_data.append(("Generic Battery", "Kinetic", 20.0, float(unit.damage), 0.8, 1.0))

                # Add to Rust
                # id, name, faction_idx, max_hp, x, y, weapons
                # Spread out y + jitter
                y_pos = (i % 20) * 5.0 + (i / 20) * 2.0
                
                self.rust_engine.add_unit(
                    bid,
                    unit.name or "Unknown",
                    f_idx,
                    float(unit.max_hp),
                    base_x,
                    y_pos,
                    weapons_data
                )
                
    def resolve_round(self) -> bool:
        """
        Steps the Rust engine one tick/round.
        Returns True if battle continues, False if finished.
        """
        if not self.rust_engine: return False
        return self.rust_engine.step()

    def get_state(self):
        """
        Returns a snapshot of the battle state.
        """
        if not self.rust_engine: return []
        return self.rust_engine.get_state()

    def sync_back_to_python(self, armies_dict):
        """
        Updates Python objects with Rust state (HP, Alive status).
        """
        if not self.rust_engine: return
        
        # Get flattened state: (id, x, y, hp, is_alive)
        raw_state = self.rust_engine.get_state()
        state_map = {row[0]: row for row in raw_state}
        
        for units in armies_dict.values():
            for unit in units:
                if hasattr(unit, 'battle_id'):
                    bid = unit.battle_id
                    if bid in state_map:
                        _, x, y, hp, is_alive = state_map[bid]
                        
                        # Update Python object
                        unit.current_hp = max(0.0, hp)
                        if not is_alive:
                            # Force kill
                            unit.is_destroyed = True
                            if unit.health_comp: 
                                unit.health_comp.current_hp = 0.0
                        
                        # Update position for visualization if needed
                        unit.grid_x = x
                        unit.grid_y = y
