import pytest
from src.managers.campaign_manager import CampaignEngine
from src.managers.combat.invasion_manager import InvasionManager
from src.core.service_locator import ServiceLocator

def test_planet_conquest_sync_index():
    # 1. Setup Engine with mock config
    engine = CampaignEngine(game_config={
        "simulation": {"num_runs": 1, "random_seed": 42},
        "campaign": {"num_systems": 2, "min_planets": 1, "max_planets": 1},
        "economy": {"starting_requisition": 10000}
    })
    engine.generate_galaxy(num_systems=2, min_planets=1, max_planets=1)
    
    # Identify factions
    factions = list(engine.faction_manager.factions.keys())
    if len(factions) < 2:
        pytest.skip("Need at least 2 factions for conquest test")
    
    attacker = factions[0]
    defender = factions[1]
    
    # Find a planet owned by defender
    planet = None
    for p in engine.all_planets:
        if p.owner == defender:
            planet = p
            break
            
    if not planet:
        # Force ownership for testing
        planet = engine.all_planets[0]
        engine.update_planet_ownership(planet, defender)
    
    assert planet.owner == defender
    
    # Check Repo Index BEFORE
    planet_repo = ServiceLocator.get("PlanetRepository")
    defender_planets_before = planet_repo.get_by_owner(defender)
    attacker_planets_before = planet_repo.get_by_owner(attacker)
    
    assert planet in defender_planets_before
    assert planet not in attacker_planets_before
    
    # 2. Trigger Conquest via InvasionManager
    # InvasionManager depends on a context (engine)
    invasion_mgr = InvasionManager(engine)
    invasion_mgr.handle_conquest(planet, attacker, method="test_conquest")
    
    # 3. Verify POST-CONQUEST State
    assert planet.owner == attacker
    
    # Check Repo Index AFTER
    defender_planets_after = planet_repo.get_by_owner(defender)
    attacker_planets_after = planet_repo.get_by_owner(attacker)
    
    # CRITICAL: Planet must be removed from defender and added to attacker
    assert planet not in defender_planets_after, f"Planet {planet.name} still in {defender} index after conquest!"
    assert planet in attacker_planets_after, f"Planet {planet.name} missing from {attacker} index after conquest!"
    
    # Verify summary consistency
    engine.report_organizer = None # Prevent actual file writing
    # Mock summary path to avoid IO errors in test
    import os
    from unittest.mock import MagicMock
    engine.report_organizer = MagicMock()
    engine.report_organizer.run_path = "tmp_test_reports"
    
    # Ensure worker stats are correct
    from src.engine.runner.simulation_worker import SimulationWorker
    stats = SimulationWorker._collect_stats(engine)
    
    assert stats[attacker]["P"] >= 1
    # Defender should have lost the planet
    assert planet.name not in [p.name for p in defender_planets_after]

if __name__ == "__main__":
    test_planet_conquest_sync_index()
