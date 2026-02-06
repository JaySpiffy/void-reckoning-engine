import pytest
from unittest.mock import MagicMock
from src.combat.combat_state import CombatState
from src.combat.real_time.formation_manager import Formation
from src.models.unit import Unit
from src.combat.tactical_grid import TacticalGrid
from src.combat.realtime.realtime_manager import RealTimeManager
from src.combat.components.movement_component import MovementComponent

@pytest.fixture
def combat_setup():
    grid = TacticalGrid()
    
    # Test Units
    mov_comp_wedge = MovementComponent(movement_points=5)
    wedge_unit = Unit(name="Wedge_Unit", faction="Wedge_Faction", hp=100, armor=0, ma=100, md=5, damage=10, abilities={}, components=[mov_comp_wedge])
    
    mov_comp_wall = MovementComponent(movement_points=5)
    wall_unit = Unit(name="Wall_Unit", faction="Wall_Faction", hp=100, armor=0, ma=100, md=5, damage=10, abilities={}, components=[mov_comp_wall])
    
    mov_comp_rect = MovementComponent(movement_points=5)
    rect_unit = Unit(name="Rect_Unit", faction="Rect_Faction", hp=100, armor=0, ma=100, md=5, damage=10, abilities={}, components=[mov_comp_rect])
    
    armies = {
        "Wedge_Faction": [wedge_unit],
        "Wall_Faction": [wall_unit],
        "Rect_Faction": [rect_unit],
        "Attacker_Faction": []
    }
    doctrines = {f: "Standard" for f in armies}
    metadata = {f: {} for f in armies}
    
    state = CombatState(armies, doctrines, metadata)
    state.grid = grid
    state.realtime_manager = RealTimeManager()
    
    return {
        "grid": grid,
        "state": state,
        "wedge_unit": wedge_unit,
        "wall_unit": wall_unit,
        "rect_unit": rect_unit
    }

def test_wedge_speed_bonus(combat_setup):
    # Wedge has 1.2x speed mult
    state = combat_setup["state"]
    wedge_unit = combat_setup["wedge_unit"]
    
    form = Formation([wedge_unit], formation_type="Wedge")
    state.formations = [form]
    
    # Add an enemy far away to trigger movement
    enemy = Unit(name="Enemy", faction="Enemy_Faction", hp=100, armor=0, ma=100, md=0, damage=0, abilities={})
    enemy.grid_x = 100
    enemy.grid_y = 0
    state.armies_dict["Enemy_Faction"] = [enemy]
    state.active_factions.append("Enemy_Faction")
    
    wedge_unit.grid_x = 0
    wedge_unit.grid_y = 0
    
    # Simulation Step
    state.real_time_update(0.1)
    
    # Base speed 5. 5 * 0.1s * 1.2 = 0.6.
    assert wedge_unit.grid_x > 0.1

def test_wall_defense_bonus(combat_setup):
    # Wall has 1.3x defense mult -> dmg / 1.3
    state = combat_setup["state"]
    wall_unit = combat_setup["wall_unit"]
    
    form = Formation([wall_unit], formation_type="Wall")
    attacker = Unit(name="Attacker", faction="Attacker_Faction", hp=100, armor=0, ma=100, md=5, damage=1, abilities={}, components=[])
    attacker.bs = 100
    
    # Setup state
    state.formations = [form]
    state.armies_dict = {
        "Wall_Faction": [wall_unit],
        "Attacker_Faction": [attacker]
    }
    state.active_factions = ["Wall_Faction", "Attacker_Faction"]
    
    wall_unit.grid_x = 10
    wall_unit.grid_y = 10
    wall_unit.facing = 0.0 # Facing North
    
    # Attacker at Front (North of defender)
    attacker.grid_x = 10
    attacker.grid_y = 0
    
    # Attacker fires (dmg=10)
    # Expected dmg: 10 / 1.3 = ~7.69
    state.real_time_update(0.1)
    
    # 100 - 7.69 = 92.31
    damage_taken = 100 - wall_unit.current_hp
    assert damage_taken < 8.0, "Wall unit should take reduced damage (no flanking)."
    assert damage_taken > 7.0
