
import sys
import os
import random

# Adjust path to find src
sys.path.append(os.getcwd())

from src.combat.combat_simulator import resolve_fleet_engagement
from src.models.unit import Ship, Component, Unit

def create_sniper_ship(faction):
    s = Ship("Sniper", 1, 1, 20, 10, 0, {}, faction=faction, cost=100)
    # Add Long Range Weapon
    c = Component("Lance", 10, "Weapon", weapon_stats={"Range": 60, "S": 5, "AP": 2, "D": 2})
    s.components = [c]
    s.tactical_directive = "KITE"
    s.weapon_range_default = 60 # Ensure base stat matches
    return s

def create_brawler_ship(faction):
    s = Ship("Brawler", 1, 1, 20, 12, 0, {}, faction=faction, cost=100)
    # Add Short Range Weapon
    c = Component("Macro", 10, "Weapon", weapon_stats={"Range": 10, "S": 5, "AP": 1, "D": 1})
    s.components = [c]
    s.tactical_directive = "CLOSE_QUARTERS"
    s.weapon_range_default = 10
    return s

def test_kiting_behavior():
    print("--- Testing Sniper (KITE) vs Brawler (CHARGE) ---")
    
    snipers = [create_sniper_ship("Snipers_Fac") for _ in range(5)]
    brawlers = [create_brawler_ship("Brawlers_Fac") for _ in range(5)]
    
    armies = {"Snipers_Fac": snipers, "Brawlers_Fac": brawlers}
    
    log_file = "tactics_test_log.txt"
    if os.path.exists(log_file): os.remove(log_file)
    
    resolve_fleet_engagement(
        armies, 
        detailed_log_file=log_file,
        max_rounds=20, # Short run to check movement
        silent=False
    )
    
    print("Simulation Complete. analyzing log...")
    
    # Analyze Log
    with open(log_file, "r") as f:
        lines = f.readlines()
        
    moves = [l for l in lines if "MOVE:" in l]
    
    # Check average distance in late rounds
    # Format: MOVE: Sniper from (X, Y) to (X, Y). Nearest Dist: 45.0
    
    late_moves = moves[-20:] # Last moves
    kite_distances = []
    charge_distances = []
    
    for m in late_moves:
        if "Sniper" in m:
            # Extract Dist
            try:
                dist_str = m.split("Dist:")[1].strip()
                dist = float(dist_str)
                kite_distances.append(dist)
            except: pass
        if "Brawler" in m:
             try:
                dist_str = m.split("Dist:")[1].strip()
                dist = float(dist_str)
                charge_distances.append(dist)
             except: pass
             
    avg_kite_dist = sum(kite_distances)/len(kite_distances) if kite_distances else 0
    print(f"Average Sniper Engagement Dist: {avg_kite_dist:.1f}")
    
    if avg_kite_dist > 30:
        print("SUCCESS: Snipers maintained range (>30).")
    else:
        print("FAILURE: Snipers got caught (<30).")

if __name__ == "__main__":
    test_kiting_behavior()
