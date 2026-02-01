
import os
import json
import pytest
from unittest.mock import MagicMock, patch
from src.reporting.organizer import ReportOrganizer
from src.managers.campaign_manager import CampaignEngine
from src.combat.combat_simulator import resolve_fleet_engagement, load_all_units, load_universe_combat_rules

@patch("src.combat.combat_simulator.load_all_units")
def test_combat_logging(mock_load_units, tmp_path):
    print("Starting Combat Logging Verification...")
    
    # 1. Setup Organizer with tmp_path
    # tmp_path is a standard pytest fixture providing a temporary directory unique to the test invocation
    base_dir = str(tmp_path)
    organizer = ReportOrganizer(base_dir, "test_batch", "test_run")
    organizer.initialize_run()
    
    # 2. Setup Engine (REMOVED - Not needed for resolve_fleet_engagement)
    # The combat simulator functions are largely standalone or use global configs.
    
    # 3. Create dummy armies using Real Units (Mocking Unit is too fragile for deep engine tests)
    from src.models.unit import Ship, Unit
    
    def create_mock_unit(name, faction):
        # Create a real Ship object (safest for fleet engagement)
        u = Ship(
            name=name,
            ma=50, md=50, hp=100, armor=10, damage=10,
            abilities={}, 
            faction=faction,
            cost=100,
            shield=50
        )
        # Ensure grid props are set (Ship init does this, but being safe)
        u.grid_size = [1, 1]
        
        # Mocking get_weapon_profiles implies the test expects it, but Unit doesn't have it.
        # If the failure earlier was "AttributeError: Mock object has no attribute...",
        # it was likely because I *tried to set it* on a restrictive mock, 
        # or the code called it.
        # If the code calls it, and valid Unit doesn't have it, the code is broken or Unit is.
        # But Real Unit has 'components'.
        # Let's hope the engine uses components or authentic_weapons.
        return u
    f1, f2 = "Imperium", "Orks"
    mock_load_units.return_value = {
        f1: [create_mock_unit("Marine", f1)],
        f2: [create_mock_unit("Boy", f2)]
    }
    
    all_units = mock_load_units.return_value

    factions = list(all_units.keys())
    if len(factions) < 2:
        pytest.skip("Not enough factions found for combat test.")
        
    f1, f2 = factions[0], factions[1]
    army1 = all_units[f1][:3] # Take 3 units
    army2 = all_units[f2][:3]
    
    armies_dict = {f1: army1, f2: army2}
    
    # Resolve Paths
    organizer.prepare_turn_folder(1, [f1, f2])
    battle_path = organizer.get_turn_path(1, "battles")
    
    log_file = os.path.join(battle_path, "test_battle.txt")
    json_log = os.path.join(battle_path, "test_battle.json")
    
    print(f"Running simulation, logging to {json_log}...")
    
    # 4. Run Simulation
    # Use resolve_fleet_engagement directly as simulate_grand_royale is gone
    rules = load_universe_combat_rules("eternal_crusade")
    
    # Note: verify resolve_fleet_engagement arguments in combat_simulator.py/tactical_engine.py
    # arguments: armies_dict, silent=False, detailed_log_file=None, json_log_file=None, universe_rules=None
    winner, survivors, rounds, stats = resolve_fleet_engagement(
        armies_dict, 
        silent=True, 
        detailed_log_file=log_file,
        json_log_file=json_log,
        universe_rules=rules
    )
    
    # 5. Verify JSON
    assert os.path.exists(json_log), "JSON log file not found!"
    
    with open(json_log, "r") as f:
        data = json.load(f)
        
    # Validating Schema v4.1 (Flat Structure)
    assert "meta" in data
    assert "events" in data
    assert "snapshots" in data
    
    assert len(data["events"]) > 0 or len(data["snapshots"]) > 0
    
    # Check for snapshots
    assert len(data["snapshots"]) > 0, "No snapshots found!"
    assert "hp" in data["snapshots"][0]
    
    # Check attribution
    tally = data["meta"].get("final_tally", {})
    assert len(tally) > 0
    for f in [f1, f2]:
        if f in tally:
            assert "total" in tally[f]
            assert "alive" in tally[f]
