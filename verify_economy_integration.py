
import sys
import os
import json
import random
from unittest.mock import MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from src.managers.economy_manager import EconomyManager
from src.core import balance as bal

def verify_economy():
    print("=== ECONOMY INTEGRATION VERIFICATION ===")
    
    # 1. Mock Campaign Engine
    mock_engine = MagicMock()
    mock_engine.game_config = {"simulation": {"random_seed": 42}}
    mock_engine.logger = MagicMock()
    mock_engine.telemetry = MagicMock()
    
    # 2. Mock Factions
    f1 = MagicMock()
    f1.name = "Empire"
    f1.get_modifier.return_value = 1.0
    
    f2 = MagicMock()
    f2.name = "Rebels"
    f2.get_modifier.return_value = 1.0
    
    mock_engine.get_all_factions.return_value = [f1, f2]
    mock_engine.get_faction.side_effect = lambda name: f1 if name == "Empire" else f2
    
    # 3. Mock Planets
    p1 = MagicMock()
    p1.name = "Terra"
    p1.owner = "Empire"
    p1.is_sieged = False
    p1._cached_econ_output = {"total_gross": 1000, "research_output": 100}
    p1._cached_maintenance = 200
    p1.garrison_capacity = 2
    p1.armies = []
    
    p2 = MagicMock()
    p2.name = "Hoth"
    p2.owner = "Rebels"
    p2.is_sieged = False
    p2._cached_econ_output = {"total_gross": 500, "research_output": 50}
    p2._cached_maintenance = 100
    p2.garrison_capacity = 1
    p2.armies = []
    
    mock_engine.planets_by_faction = {
        "Empire": [p1],
        "Rebels": [p2]
    }
    
    # 4. Mock Fleets
    fl1 = MagicMock()
    fl1.id = "F1"
    fl1.is_destroyed = False
    fl1.is_in_orbit = True
    fl1.upkeep = 600 # Base upkeep
    fl1.units = []
    
    mock_engine.fleets_by_faction = {
        "Empire": [fl1],
        "Rebels": []
    }
    
    # Initialize EconomyManager
    econ_mgr = EconomyManager(mock_engine)
    
    print("Step 1: Syncing Rust Economy...")
    econ_mgr._sync_rust_economy()
    
    print("Step 2: Processing All reports...")
    reports = econ_mgr.rust_econ.get_all_reports()
    
    emp_report = reports.get("Empire")
    reb_report = reports.get("Rebels")
    
    if not emp_report or not reb_report:
        print("FAILURE: Reports missing.")
        return
        
    print(f"\nEmpire Report: {json.dumps(emp_report, indent=2)}")
    print(f"Rebels Report: {json.dumps(reb_report, indent=2)}")
    
    # Verify Orbital Discount for Empire Fleet (F1)
    # F1 upkeep is 600. Orbit discount is 0.5. Fleet scalar is 0.5 (from balance.py).
    # Expected F1 upkeep in Rust: 600 * 0.5 (orbit) * 0.5 (scalar) = 150.
    # Total Empire upkeep: 200 (Planet) + 150 (Fleet) = 350.
    
    # Wait, let's check bal.FLEET_MAINTENANCE_SCALAR
    fleet_scalar = getattr(bal, 'FLEET_MAINTENANCE_SCALAR', 0.5)
    orbit_mult = getattr(bal, 'ORBIT_DISCOUNT_MULTIPLIER', 0.5)
    expected_f1_upkeep = 600 * orbit_mult * fleet_scalar
    expected_total_upkeep = 200 + expected_f1_upkeep
    
    actual_upkeep = emp_report["total_upkeep"]["credits"]
    
    print(f"\nVerification - Empire Upkeep:")
    print(f"  Expected: {expected_total_upkeep}")
    print(f"  Actual: {actual_upkeep}")
    
    if abs(actual_upkeep - expected_total_upkeep) < 0.01:
        print("SUCCESS: Upkeep match (including discounts/scalars).")
    else:
        print("FAILURE: Upkeep mismatch.")
        
    # Verify Income
    # Terra income: 1000 (gross) + 50 (min_planet_income).
    # Total: 1050.
    expected_income = 1000 + bal.MIN_PLANET_INCOME
    actual_income = emp_report["total_income"]["credits"]
    
    print(f"\nVerification - Empire Income:")
    print(f"  Expected: {expected_income}")
    print(f"  Actual: {actual_income}")
    
    if abs(actual_income - expected_income) < 0.01:
        print("SUCCESS: Income match.")
    else:
        print("FAILURE: Income mismatch.")
        
    # Verify categorization
    if "Tax" in emp_report["income_by_category"]:
        print("SUCCESS: Income categorized correctly (Planet -> Tax).")
    else:
        print("FAILURE: Categorization missing.")

if __name__ == "__main__":
    verify_economy()
