import sys
import os
sys.path.append(os.getcwd())

from src.combat.ability_manager import AbilityManager
from src.combat.tactical_grid import TacticalGrid

def verify_part3():
    print("--- Verifying Void Corsairs & Solar Hegemony ---")
    
    registry = {
        "Ability_Afterburner": {
            "id": "Ability_Afterburner",
            "payload_type": "buff",
            "effects": {"speed_mult": 1.5, "duration": 1}
        },
        "Ability_Boarding_Action": {
            "id": "Ability_Boarding_Action",
            "payload_type": "capture",
            "capture_threshold": 0.5
        },
        "Ability_Plasma_Overcharge": {
            "id": "Ability_Plasma_Overcharge",
            "payload_type": "buff",
            "effects": {"damage_mult": 1.35, "duration": 1}
        }
    }
    
    am = AbilityManager(registry)
    
    class MockUnit:
        def __init__(self, name, x, y, hp=100):
            self.name = name
            self.grid_x = x
            self.grid_y = y
            self.current_hp = hp
            self.max_hp = 100
            self.temp_modifiers = {}
            self.type = "vehicle"
            self.is_destroyed = False
            
        def apply_temporary_modifiers(self, mods):
            self.temp_modifiers.update(mods)

    # Test 1: Void Corsairs - Afterburner
    print("\n[Test 1] Afterburner (Buff)")
    bike = MockUnit("Jetbike", 0, 0)
    am.execute_ability(bike, bike, "Ability_Afterburner")
    print(f"Mods: {bike.temp_modifiers}")
    if bike.temp_modifiers.get("speed_mult") == 1.5:
        print("PASS: Afterburner applied.")
    else:
        print("FAIL: Speed not boosted.")

    # Test 2: Void Corsairs - Boarding Action (Capture)
    print("\n[Test 2] Boarding Action (Capture)")
    incubus = MockUnit("Incubus", 0, 0)
    target = MockUnit("EnemyShip", 0, 1, hp=40) # 40% HP < 50% threshold
    
    res = am.execute_ability(incubus, target, "Ability_Boarding_Action")
    print(f"Result: {res}")
    
    if res.get("captured") and target.is_destroyed:
        print("PASS: Ship captured.")
    else:
        print("FAIL: Capture failed.")

    # Test 3: Solar Hegemony - Plasma Overcharge
    print("\n[Test 3] Plasma Overcharge")
    suit = MockUnit("Battlesuit", 0, 0)
    am.execute_ability(suit, suit, "Ability_Plasma_Overcharge")
    print(f"Mods: {suit.temp_modifiers}")
    
    if suit.temp_modifiers.get("damage_mult") == 1.35:
        print("PASS: Plasma Overcharge applied.")
    else:
        print("FAIL: Damage buff not applied.")

if __name__ == "__main__":
    verify_part3()
