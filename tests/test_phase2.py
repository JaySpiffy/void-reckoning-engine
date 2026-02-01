import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.combat.ability_manager import AbilityManager
from src.combat.tactical_engine import initialize_battle_state
from src.combat.combat_utils import Unit

def verify_ability_execution():
    print("--- Verifying Phase 2 Ability Integration (with Costs) ---")
    
    # 1. Setup Registry
    registry = {
        "Ability_Smite": {
            "id": "Ability_Smite",
            "name": "Holy Smite",
            "payload_type": "damage",
            "damage": 50,
            "range": 50,
            "cost": {"conviction": 10}
        },
        "Ability_Free": {
            "id": "Ability_Free",
            "payload_type": "heal",
            "heal": 10,
            "cost": {}
        }
    }
    
    manager = AbilityManager(registry)
    
    class MockFaction:
        def __init__(self, name):
            self.name = name
            self.custom_resources = {"conviction": 0}

    class MockUnit:
        def __init__(self, name, hp):
            self.name = name
            self.current_hp = hp
            self.max_hp = hp
            self.is_destroyed = False
            
        def is_alive(self): return not self.is_destroyed
        def take_damage(self, amount):
            self.current_hp -= amount
            return False
        def heal(self, amount):
            self.current_hp += amount
            return amount

    source = MockUnit("Caster", 100)
    target = MockUnit("Target", 100)
    faction = MockFaction("Zealots")
    
    # Context with faction
    context = {"faction": faction}
    
    # Test 3: Insufficient Resources
    print("\n[Test 3] Cost Check Fail")
    res = manager.execute_ability(source, target, "Ability_Smite", context)
    print(f"Result: {res}")
    if not res["success"] and "Insufficient" in res["reason"]:
        print("PASS: Ability blocked due to cost.")
    else:
        print("FAIL: Ability should have been blocked.")
        
    # Test 4: Sufficient Resources
    print("\n[Test 4] Cost Check Pass")
    faction.custom_resources["conviction"] = 20
    res2 = manager.execute_ability(source, target, "Ability_Smite", context)
    print(f"Result: {res2}")
    if res2["success"] and faction.custom_resources["conviction"] == 10:
        print("PASS: Ability executed and resources deducted.")
    else:
        print(f"FAIL: Logic error. Res: {faction.custom_resources['conviction']}")

if __name__ == "__main__":
    verify_ability_execution()
