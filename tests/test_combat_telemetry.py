
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.combat.combat_state import CombatState
from src.models.unit import Regiment
from src.combat.combat_phases import ShootingPhase, AbilityPhase

class MockWeapon:
    def __init__(self, name="TestWeapon"):
        self.name = name
        self.type = "Weapon"
        self.is_destroyed = False
        self.weapon_stats = {"Range": 50, "Str": 5, "AP": 10}
    
    def to_dict(self):
        return {"name": self.name, "stats": self.weapon_stats}

def test_telemetry_reporting():
    print("Testing Combat Telemetry Reporting...")
    
    # 1. Setup mock units
    u1 = Regiment("Attacker", 100, 100, 50, 0, 10, {}, "Faction1", [])
    u2 = Regiment("Target", 100, 100, 50, 0, 10, {}, "Faction2", [])
    
    # Add weapon to u1
    u1.components = [MockWeapon()]
    u1.bs = 100  # Guarantee hit
    
    # Add ability to u1
    u1.abilities = ["test_damage_ability"]
    u1.atomic_abilities = {"test_damage_ability": {}}
    
    armies = {"Faction1": [u1], "Faction2": [u2]}
    state = CombatState(armies, {"Faction1": "STANDARD", "Faction2": "STANDARD"}, MagicMock())
    state.initialize_battle()
    
    # Mock Grid
    grid = MagicMock()
    grid.get_distance.return_value = 10
    grid.get_distance_coords.return_value = 10
    state.grid = grid
    
    # Context
    context = {
        "active_units": [(u1, "Faction1")],
        "enemies_by_faction": {"Faction1": [u2]},
        "grid": grid,
        "faction_doctrines": {"Faction1": "STANDARD"},
        "faction_metadata": {"Faction1": {}},
        "round_num": 1,
        "manager": state,
        "tracker": MagicMock()
    }
    
    # --- Test 1: Batch Shooting Telemetry ---
    print("Sub-test: Batch Shooting...")
    shooting_phase = ShootingPhase()
    
    # We need to mock batch_shooter to ensure it uses the batch path and returns damage
    mock_batch_results = [{
        "attacker": u1,
        "target": u2,
        "damage": 50.0,
        "is_hit": True,
        "weapon": u1.components[0],
        "dist": 10.0
    }]
    
    with patch("src.combat.batch_shooting.resolve_shooting_batch", return_value=mock_batch_results):
        # Trigger batch mode by giving tracker compute_nearest_enemies
        context["tracker"].compute_nearest_enemies.return_value = {id(u1): (id(u2), 10.0)}
        shooting_phase.execute(context)
        
    print(f"Faction1 damage after batch shooting: {state.battle_stats['Faction1']['total_damage_dealt']}")
    assert state.battle_stats['Faction1']['total_damage_dealt'] == 50.0
    print("SUCCESS: Batch shooting reported damage correctly.")
    
    # --- Test 2: Ability Telemetry ---
    print("Sub-test: Ability Damage...")
    u2.current_hp = 100 # Ensure target is alive
    state.battle_stats['Faction1']['total_damage_dealt'] = 0  # Reset
    ability_phase = AbilityPhase()
    
    print(f"Attacker faction: {u1.faction}, alive: {u1.is_alive()}, hp: {u1.current_hp}")
    print(f"Attacker abilities types: {type(u1.abilities)}, content: {u1.abilities}")
    print(f"Target alive: {u2.is_alive()}, hp: {u2.current_hp}, faction: {u2.faction}")
    print(f"Enemies for Faction1: {context['enemies_by_faction'].get('Faction1')}")
    
    # Real Ability Manager with mock registry
    from src.combat.ability_manager import AbilityManager
    ab_manager = AbilityManager({"test_damage_ability": {"payload_type": "damage", "range": 50, "damage": 25.0}})
    state.ability_manager = ab_manager
    
    # We need to ensure the faction is in the context for cost check (even if cost is free)
    # But for total_damage_dealt, we need the logic in _handle_damage to run.
    
    with patch("src.combat.tactical_engine.select_target_by_doctrine", return_value=u2):
        print(f"Executing AbilityPhase with active_units: {context['active_units']}")
        ability_phase.execute(context)
    
    print(f"Faction1 damage after ability: {state.battle_stats['Faction1']['total_damage_dealt']}")
    assert state.battle_stats['Faction1']['total_damage_dealt'] == 25.0
    print("SUCCESS: Ability reported damage correctly.")

if __name__ == "__main__":
    try:
        test_telemetry_reporting()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
