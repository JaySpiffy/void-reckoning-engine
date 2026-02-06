import pytest
import math
from src.combat.combat_state import CombatState
from src.combat.real_time.simulation_loop import SimulationLoop
from src.models.unit import Ship
from src.combat.tactical_grid import TacticalGrid

@pytest.fixture
def morale_setup():
    # Iron Vanguard Conscripts (Target) vs Solar Hegemony Custodian (Attacker)
    conscript = Ship("Vanguard_Conscript", 100, 50, 100, 10, 5, {}, faction="Iron_Vanguard")
    conscript.grid_x = 10
    conscript.grid_y = 10
    
    # Massive damage dealer to break morale
    attacker = Ship("Solar_Executioner", 100, 50, 1000, 50, 40, {}, faction="Solar_Hegemony")
    attacker.grid_x = 0
    attacker.grid_y = 10
    
    armies_dict = {
        "Iron_Vanguard": [conscript],
        "Solar_Hegemony": [attacker]
    }
    
    state = CombatState(armies_dict, {}, {})
    state.grid = TacticalGrid(100, 100)
    state.grid.update_unit_position(conscript, 10, 10)
    state.grid.update_unit_position(attacker, 0, 0)
    
    return {
        "state": state,
        "conscript": conscript,
        "attacker": attacker
    }

def test_morale_routing_on_damage(morale_setup):
    state = morale_setup["state"]
    conscript = morale_setup["conscript"]
    
    loop = SimulationLoop(tick_rate=20)
    loop.on_update = state.real_time_update
    
    # Run for 3 seconds of combat
    loop.start(duration_seconds=3.0)
    
    # Verify Routing
    assert conscript.morale_state == "Routing", "Conscript should be routing after taking heavy damage."
    
    # Verify Movement (Should have moved further away from attacker at x=0)
    assert conscript.grid_x > 10.0, "Routing unit should move away from the threat."

def test_morale_rally(morale_setup):
    state = morale_setup["state"]
    conscript = morale_setup["conscript"]
    attacker = morale_setup["attacker"]
    
    # Force a unit to route, then move it away to see if it rallies
    conscript.morale_current = 45 # Start closer to rally threshold (50)
    conscript.morale_state = "Routing"
    
    loop = SimulationLoop(tick_rate=20)
    loop.on_update = state.real_time_update
    
    # Move attacker very far away (out of range)
    attacker.grid_x = 1000
    conscript.time_since_last_damage = 20.0 # Force recovery
    
    loop.start(duration_seconds=5.0) # 5s * 5/s = 25 recovery -> 45 + 25 = 70 (Rallied)
    
    # It should rally when morale > 50
    assert conscript.morale_state in ["Shaken", "Steady"]
