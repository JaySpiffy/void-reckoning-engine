import os
import json
import sys

sys.path.append(os.getcwd())

from src.managers.tech_manager import TechManager
from src.managers.intelligence_manager import IntelligenceManager
# Mock Engine class
class MockEngine:
    pass

def verify_systems():
    print("=== Verifying Research & Espionage ===")
    
    # 1. Setup
    tech_mgr = TechManager()
    intel_mgr = IntelligenceManager(MockEngine())
    
    # Mock Arsenals
    faction_a = "Empire_A"
    faction_b = "Rebels_B"
    
    arsenal_a = {
        "legacy_laser": {
            "id": "legacy_laser",
            "name": "Legacy Laser",
            "category": "Energy",
            "stats": {"power": 100, "range": 50, "cost": 1000},
            "traits": []
        }
    }
    
    arsenal_b = {
        "rusty_cannon": {
            "id": "rusty_cannon",
            "name": "Rusty Cannon",
            "stats": {"power": 50, "range": 20},
            "traits": []
        }
    }
    
    # 2. Test Upgrade
    print("\n[Test 1] Weapon Upgrade")
    upgraded = tech_mgr.upgrade_weapon(faction_a, "legacy_laser", arsenal_a)
    
    if upgraded and "Mk II" in upgraded["name"]:
        print(f"SUCCESS: Upgraded to {upgraded['name']}")
        print(f"Old Power: 100 -> New Power: {upgraded['stats']['power']}")
        # Check Arsenal Update
        if "legacy_laser_mk2" in arsenal_a:
            print("SUCCESS: Arsenal updated property.")
    else:
        print("FAILED: Upgrade returned None or mismatched name.")
        
    # 3. Test Theft
    print("\n[Test 2] Weapon Theft")
    
    # Fixing the mock data to match the expected ID format
    if "legacy_laser" in arsenal_a:
        arsenal_a["legacy_laser"]["id"] = "legacy_laser_weapon"
        val = arsenal_a.pop("legacy_laser")
        arsenal_a["legacy_laser_weapon"] = val

    # Force success by looping until it hits 40% chance
    success = False
    for i in range(20):
        # Pass a mock logger or enable prints? The manager uses print()
        # Let's verify candidates first
        if intel_mgr.attempt_weapon_theft(faction_b, faction_a, arsenal_b, arsenal_a):
            success = True
            break
            
    if success:
        # Verify B has stolen weapon
        stolen_key = [k for k in arsenal_b.keys() if "stolen" in k]
        if stolen_key:
            stolen_item = arsenal_b[stolen_key[0]]
            print(f"SUCCESS: Stole {stolen_item['name']}")
            print(f"Traits: {stolen_item['traits']}")
            print(f"Power: {stolen_item['stats']['power']} (Reduced from 100/110)")
        else:
             print("FAILED: Function returned True but weapon not found in arsenal.")
    else:
        print("FAILED: Could not succeed theft after 10 tries.")
        
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_systems()
