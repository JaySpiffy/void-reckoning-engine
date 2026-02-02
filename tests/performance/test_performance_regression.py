import pytest
import time
import json
import os
import sys
# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from typing import Dict, Any

from src.core.game_config import GameConfig
from src.managers.campaign_manager import CampaignEngine

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'performance_config.json')
with open(CONFIG_PATH, 'r') as f:
    PERF_CONFIG = json.load(f)

BASELINE_TURN_TIME = PERF_CONFIG['baselines']['turn_processing_ms_medium'] / 1000.0 # Convert to seconds

@pytest.mark.performance
def create_test_config(num_systems: int = 20) -> GameConfig:
    return GameConfig(
        num_systems=num_systems,
        max_turns=10,
        min_planets_per_system=1,
        max_planets_per_system=5,
        starting_fleets=1,
        performance_logging_level="detailed",
        performance_profile_methods=True
    )

@pytest.mark.performance
def test_turn_processing_performance():
    """Measure average turn processing time over 10 turns."""
    config = create_test_config(num_systems=PERF_CONFIG['scenarios']['medium']['num_systems'])
    engine = CampaignEngine(game_config=config)
    engine.generate_galaxy(
        num_systems=config.num_systems,
        min_planets=1,
        max_planets=5
    )
    engine.spawn_start_fleets(1)
    
    timings = []
    # Run a few warmup turns
    for _ in range(2):
        engine.process_turn()
        
    # Measure
    for i in range(10):
        start = time.time()
        engine.process_turn()
        duration = time.time() - start
        timings.append(duration)
    
    avg_time = sum(timings) / len(timings)
    print(f"Average turn time: {avg_time*1000:.2f}ms (Baseline: {BASELINE_TURN_TIME*1000:.2f}ms)")
    
    # Allow some tolerance (e.g., 20% or strict check depending on requirements)
    # Using 50% here as initial loose constraint until robust baselines are established
    assert avg_time < BASELINE_TURN_TIME * 1.5

@pytest.mark.performance
def test_pathfinding_performance():
    """Measure pathfinding time."""
    config = create_test_config(num_systems=50)
    engine = CampaignEngine(game_config=config)
    engine.generate_galaxy(num_systems=50, min_planets=1, max_planets=5)
    
    # Pick two distant systems
    systems = list(engine.systems)
    start = systems[0]
    end = systems[-1]
    
    start_time = time.time()
    path, cost, meta = engine.pathfinder.find_path(start, end)
    duration = (time.time() - start_time) * 1000
    
    print(f"Pathfinding time: {duration:.2f}ms")
    assert duration < PERF_CONFIG['baselines']['pathfinding_ms_long'] * 2 # Tolerance

@pytest.mark.performance
def test_combat_resolution_performance():
    """Measure battle resolution time."""
    config = create_test_config(num_systems=10)
    engine = CampaignEngine(game_config=config)
    engine.generate_galaxy(num_systems=10)
    
    # Setup a mock battle
    # Find a planet
    planet = engine.all_planets[0]
    
    # Create two hostile fleets
    f1 = engine.create_fleet("Imperium", planet)
    f2 = engine.create_fleet("Orks", planet)
    # engine.diplomacy.set_relationship("Imperium", "Orks", -100) # Method might not exist
    if engine.diplomacy.relations.get("Imperium") is None:
        engine.diplomacy.relations["Imperium"] = {}
    engine.diplomacy.relations["Imperium"]["Orks"] = -100
    
    if engine.diplomacy.treaties.get("Imperium") is None:
        engine.diplomacy.treaties["Imperium"] = {}
    if engine.diplomacy.treaties.get("Orks") is None:
        engine.diplomacy.treaties["Orks"] = {}
        
    engine.diplomacy.treaties["Imperium"]["Orks"] = "War"
    engine.diplomacy.treaties["Orks"]["Imperium"] = "War"
    
    # Measure battle resolution
    # We call resolve_battles_at directly or trigger via turn
    start_time = time.time()
    engine.battle_manager.resolve_battles_at(planet)
    duration = (time.time() - start_time) * 1000
    
    print(f"Combat resolution time: {duration:.2f}ms")
    # Using a generous baseline since we don't have a specific scenario loaded
    assert duration < 50.0 # ms

@pytest.mark.performance
def test_economy_processing_performance():
    """Measure economy phase time."""
    config = create_test_config(num_systems=20)
    engine = CampaignEngine(game_config=config)
    engine.generate_galaxy(num_systems=20)
    engine.spawn_start_fleets()
    
    # Measure economy manager phase
    start_time = time.time()
    
    # Manually trigger economy steps for all factions
    for faction in engine.factions.values():
         if faction.name == "Neutral": continue
         engine.economy_manager.process_faction_economy(faction.name)
         
    duration = (time.time() - start_time) * 1000
    
    print(f"Economy processing time (all factions): {duration:.2f}ms")
    assert duration < PERF_CONFIG['baselines']['turn_processing_ms_medium'] * 0.5 # Should be a fraction of total turn
