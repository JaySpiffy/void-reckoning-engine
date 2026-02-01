import os
import json
import pytest
import subprocess
import logging
from src.managers.campaign_manager import CampaignEngine
from src.reporting.organizer import ReportOrganizer
from src.core.game_config import GameConfig

# Enable logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def run_env(tmp_path):
    # Setup test report directory
    base_dir = tmp_path / "test_faction_reports"
    organizer = ReportOrganizer(str(base_dir), "test_batch", "test_run", universe_name="eternal_crusade")
    organizer.initialize_run()
    
    # Initialize Engine
    config = GameConfig.from_dict({
        "reporting": {"formats": ["json", "markdown"]},
        "mechanics": {"enable_diplomacy": False, "enable_weather": False}
    })
    # Use ACTIVE_UNIVERSE = "eternal_crusade"
    engine = CampaignEngine(report_organizer=organizer, game_config=config, universe_name="eternal_crusade")
    
    # Generate minimal galaxy
    engine.generate_galaxy(num_systems=3)
    
    return engine, organizer, base_dir

def test_faction_reports_generation(run_env):
    """Verify that faction reports are generated."""
    engine, organizer, base_dir = run_env
    
    # Ensure active factions
    active_factions = [f for f in engine.factions if f != "Neutral"]
    print(f"DEBUG: Active Factions: {active_factions}")
    assert active_factions, "No active factions found!"
    
    # Ensure reporter has generators
    assert engine.faction_reporter.generators, "No generators in reporter!"
    
    # Prepare turn folder
    turn = 1
    organizer.prepare_turn_folder(turn, factions=active_factions)
    
    # Start and Finalize
    engine.faction_reporter.start_turn(turn)
    
    # Inject one event to ensure it's not empty skip (though it shouldn't)
    f_name = active_factions[0]
    engine.faction_reporter.log_event(f_name, "test", "test message")
    
    engine.faction_reporter.finalize_turn()
    
    # Check reports
    f_dir = organizer.get_turn_path(turn, "factions", faction=f_name)
    json_path = os.path.join(f_dir, "summary.json")
    
    if not os.path.exists(json_path):
        print(f"DEBUG: Missing {json_path}")
        print(f"DEBUG: Run Path: {organizer.run_path}")
        subprocess.run(["tree", "/F", str(organizer.run_path)], shell=True)
        
    assert os.path.exists(json_path), f"Failed to generate report for {f_name}"
