
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from src.utils.rust_economy import RustEconomyWrapper
from void_reckoning_bridge import RustPathfinder

def test_economy_math():
    print("--- Testing Economy Math (Fixed-Point) ---")
    econ = RustEconomyWrapper()
    
    # Node 1: High income, zero upkeep
    econ.add_node(
        node_id="Planet_Prime",
        owner_faction="Hegemony",
        base_income={"credits": 1000.5, "minerals": 500.0, "energy": 200.0, "research": 50.0},
        base_upkeep={"credits": 0.0, "minerals": 0.0, "energy": 0.0, "research": 0.0},
        efficiency=1.0
    )
    
    # Node 2: Low income, high upkeep
    econ.add_node(
        node_id="Outpost_Alpha",
        owner_faction="Hegemony",
        base_income={"credits": 100.0, "minerals": 10.0, "energy": 5.0, "research": 0.0},
        base_upkeep={"credits": 500.25, "minerals": 50.0, "energy": 20.0, "research": 0.0},
        efficiency=0.85
    )
    
    report = econ.get_faction_report("Hegemony")
    print(f"Report for Hegemony: {json.dumps(report, indent=2)}")
    
    # Assertions
    # Gross Income: (1000.5 * 1.0) + (100.0 * 0.85) = 1000.5 + 85.0 = 1085.5
    # Total Upkeep: 0.0 + 500.25 = 500.25
    # Net: 1085.5 - 500.25 = 585.25
    
    expected_income = 1085.5
    expected_upkeep = 500.25
    
    assert abs(report["total_income"]["credits"] - expected_income) < 0.0001
    assert abs(report["total_upkeep"]["credits"] - expected_upkeep) < 0.0001
    assert report["is_insolvent"] is False
    print("[OK] Income/Upkeep Math Validated")

def test_insolvency():
    print("\n--- Testing Insolvency Detection ---")
    econ = RustEconomyWrapper()
    
    econ.add_node(
        node_id="Broke_Station",
        owner_faction="Exiles",
        base_income={"credits": 10.0, "minerals": 0.0, "energy": 0.0, "research": 0.0},
        base_upkeep={"credits": 1000.0, "minerals": 0.0, "energy": 0.0, "research": 0.0}
    )
    
    report = econ.get_faction_report("Exiles")
    print(f"Broke Faction Net: {report['net_profit']['credits']}")
    assert report["is_insolvent"] is True
    print("[OK] Insolvency Detection Validated")

def test_trade_routes():
    print("\n--- Testing Trade Routes with Pathfinder ---")
    pathfinder = RustPathfinder()
    pathfinder.add_node("System_A")
    pathfinder.add_node("System_B")
    pathfinder.add_node("System_C")
    
    # Safe path: A -> B -> C (weights 1.0)
    pathfinder.add_edge("System_A", "System_B", 1.0)
    pathfinder.add_edge("System_B", "System_C", 1.0)
    
    econ = RustEconomyWrapper()
    econ.add_trade_route("System_A", "System_C", {"credits": 500.0})
    
    # Calculate with safe path
    trade_income = econ.calculate_trade(pathfinder)
    print(f"Safe Trade Gain (A): {trade_income.get('System_A')}")
    # Expected: 250.0 (50% of 500 * 1.0 efficiency)
    assert abs(trade_income["System_A"]["credits"] - 250.0) < 0.0001
    
    # Hazard path: Increase weight to 2.5 (avg weight > 2.0 = severed)
    pathfinder.add_edge("System_A", "System_B", 5.0) # Path weight 6.0 / 2 hops = 3.0 avg
    trade_income_hazard = econ.calculate_trade(pathfinder)
    print(f"Hazard Trade Gain (A): {trade_income_hazard.get('System_A', {}).get('credits', 0)}")
    assert trade_income_hazard.get("System_A", {}).get("credits", 0) == 0
    
    print("[OK] Trade Route path-awareness Validated")

if __name__ == "__main__":
    try:
        test_economy_math()
        test_insolvency()
        test_trade_routes()
        print("\nALL ECONOMY VERIFICATION TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
