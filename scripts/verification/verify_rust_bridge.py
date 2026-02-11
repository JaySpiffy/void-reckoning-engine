import void_reckoning_bridge
import json
import math
import time

def test_pathfinder():
    print("\n--- Testing RustPathfinder ---")
    pf = void_reckoning_bridge.RustPathfinder()
    pf.add_node("Sol")
    pf.add_node("Alpha Centauri")
    pf.add_edge("Sol", "Alpha Centauri", 4.3)
    
    path, cost = pf.find_path("Sol", "Alpha Centauri")
    print(f"Path: {path}, Cost: {cost}")
    assert path == ["Sol", "Alpha Centauri"]
    assert math.isclose(cost, 4.3, rel_tol=1e-5)
    
    # Test Ground Pathfinding (Terrain Costs)
    print("  Testing Ground Profile (Mountain 2x cost)...")
    pf.add_node("Base", None)
    pf.add_node("MountainPass", "Mountain") # High Cost
    pf.add_node("Outpost", None)
    
    # A -> Mountain -> B (Dist 10 + 10)
    pf.add_edge("Base", "MountainPass", 10.0)
    pf.add_edge("MountainPass", "Outpost", 10.0)
    
    # Space Profile (Should be 20.0)
    _, cost_space = pf.find_path("Base", "Outpost", "Space")
    print(f"  Space Cost: {cost_space}")
    assert math.isclose(cost_space, 20.0, rel_tol=1e-5)
    
    # Ground Profile (Mountain * 2.0 = 20.0 + 10.0 = 30.0)
    # Target node is MountainPass (cost * 2) and Outpost (cost * 1)
    # Edge Base->MountainPass: Target is MountainPass. Cost = 10 * 2 = 20.
    # Edge MountainPass->Outpost: Target is Outpost. Cost = 10 * 1 = 10.
    # Total = 30.
    _, cost_ground = pf.find_path("Base", "Outpost", "Ground")
    print(f"  Ground Cost: {cost_ground}")
    assert math.isclose(cost_ground, 30.0, rel_tol=1e-5)
    
    print("  Pathfinder PASSED")

def test_combat():
    print("\n--- Testing RustCombatEngine ---")
    combat = void_reckoning_bridge.RustCombatEngine(1000.0, 1000.0)
    
    # Add Unit A (Faction 1)
    # Weapons: (Name, Type, Range, Damage, Accuracy, Cooldown)
    weapons_a = [("Laser", "Energy", 100.0, 10.0, 0.9, 2.0)]
    # Updated signature: id, name, faction, hp, x, y, weapons, speed, evasion, shields, armor, cover
    combat.add_unit(1, "Hero Ship", 1, 100.0, 500.0, 500.0, weapons_a, 10.0, 0.1, 100.0, 10.0, None)
    
    # Add Unit B (Faction 2)
    weapons_b = [("Missile", "Missile", 200.0, 20.0, 0.7, 5.0)]
    combat.add_unit(2, "Enemy Ship", 2, 50.0, 550.0, 500.0, weapons_b, 10.0, 0.1, 100.0, 10.0, None) # Within range
    
    # Enable logging
    print("Enabling combat event logging...")
    event_log = combat.enable_event_logging()
    
    print("Stepping combat...")
    for _ in range(10):
        combat.step()
        
    status_a = combat.get_unit_status(1)
    status_b = combat.get_unit_status(2)
    print(f"Unit 1 Status: {status_a}")
    print(f"Unit 2 Status: {status_b}")
    
    assert status_a is not None
    assert status_b is not None
    
    # Check logs
    events = event_log.get_all()
    print(f"Captured {len(events)} events")
    for evt in events:
        print(f"  [{evt.timestamp}] {evt.severity}: {evt.message}")
        
    if status_b[2] == False: # If unit 2 died
        assert len(events) > 0
        print("  Combat Event Logging VERIFIED")
    
    print("  Combat PASSED")

def test_auditor():
    print("\n--- Testing RustAuditor ---")
    auditor = void_reckoning_bridge.RustAuditor()
    
    # Load mock registry
    buildings_reg = {
        "factory": {"tier": 1, "cost": 100},
        "lab": {"tier": 2, "cost": 200}
    }
    auditor.load_registry("buildings", json.dumps(buildings_reg))
    auditor.initialize()
    print("Enabling auditor event logging...")
    event_log = auditor.enable_event_logging()
    
    # Validate valid unit
    valid_unit = {
        "name": "Tank",
        "tier": 1,
        "armor": 5,
        "speed": 10,
        "required_building": "factory"
    }
    result_json = auditor.validate_entity("unit_1", "unit", json.dumps(valid_unit), "universe_1", 1)
    results = json.loads(result_json)
    print(f"Valid Unit Results: {len(results)} issues found")
    assert len(results) == 0
    
    # Validate invalid unit (missing field + bad ref)
    invalid_unit = {
        "name": "Broken Tank",
        # Missing tier, armor, speed
        "required_building": "missing_building" 
    }
    result_json = auditor.validate_entity("unit_2", "unit", json.dumps(invalid_unit), "universe_1", 1)
    results = json.loads(result_json)
    print(f"Invalid Unit Results: {len(results)} issues found")
    
    # Expect FieldExistenceRule (Critical) + ReferenceIntegrityRule (Error)
    assert len(results) >= 1
    
    # Verify Logs
    events = event_log.get_all()
    print(f"Captured {len(events)} auditor events")
    for evt in events:
        print(f"  [{evt.category}] {evt.severity}: {evt.message}")
        
    assert len(events) >= 1
    print("  Auditor Observability VERIFIED")
    print("  Auditor PASSED")

def test_economy():
    print("\n--- Testing RustEconomyEngine ---")
    econ = void_reckoning_bridge.RustEconomyEngine()
    
    # Enable Logging
    print("Enabling economy event logging...")
    event_log = econ.enable_event_logging()
    
    # Add Planet Node
    planet_node = {
        "id": "planet_1",
        "owner_faction": "Terran",
        "node_type": "Planet",
        "base_income": {"credits": 10, "minerals": 50, "energy": 0, "research": 0}, # Low income
        "base_upkeep": {"credits": 100, "minerals": 0, "energy": 5, "research": 0}, # High upkeep
        "efficiency_scaled": 1000000,
        "modifiers": []
    }
    econ.add_node(json.dumps(planet_node))
    
    # Process
    report_json = econ.process_faction("Terran")
    report = json.loads(report_json)
    
    print(f"Faction Income: {report['total_income']['credits']}")
    print(f"Faction Profit: {report['net_profit']['credits']}")
    
    assert report['is_insolvent'] == True
    
    # Verify Logs
    events = event_log.get_all()
    print(f"Captured {len(events)} economy events")
    for evt in events:
        print(f"  [{evt.category}] {evt.severity}: {evt.message}")
        
    assert len(events) > 0
    print("  Economy Observability VERIFIED")
    print("  Economy PASSED")

if __name__ == "__main__":
    try:
        test_pathfinder()
        test_combat()
        test_auditor()
        test_economy()
        print("\n  ALL RUST MODULES VERIFIED")
    except Exception as e:
        print(f"\n  VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
