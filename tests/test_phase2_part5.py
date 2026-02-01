import sys
import os
sys.path.append(os.getcwd())

from src.combat.ability_manager import AbilityManager
from src.combat.tactical_grid import TacticalGrid

def verify_part5():
    print("--- Verifying Scavenger Clans & Ancient Guardians ---")
    
    registry = {
        "Ability_Jury_Rig": {
            "id": "Ability_Jury_Rig",
            "payload_type": "heal",
            "heal": 40
        },
        "Ability_More_Dakka": {
            "id": "Ability_More_Dakka",
            "payload_type": "buff",
            "effects": {
                "damage_mult": 2.0,
                "accuracy_mult": 0.5,
                "duration": 1
            }
        },
        "Ability_Webway_Strike": {
            "id": "Ability_Webway_Strike",
            "payload_type": "teleport",
            "range": 6
        },
        "Ability_Prescience": {
            "id": "Ability_Prescience",
            "payload_type": "buff",
            "effects": {
                "evasion": 0.3,
                "accuracy_mult": 1.2,
                "duration": 2
            }
        }
    }
    
    am = AbilityManager(registry)
    grid = TacticalGrid(10, 10)
    
    class MockUnit:
        def __init__(self, name, x, y, hp=100):
            self.name = name
            self.grid_x = x
            self.grid_y = y
            self.current_hp = hp
            self.max_hp = 100
            self.temp_modifiers = {}
            self.type = "vehicle"
            self.grid_size = [1, 1]
            self.is_deployed = True
            
        def heal(self, amt):
            self.current_hp += amt
            return amt
            
        def apply_temporary_modifiers(self, mods):
            self.temp_modifiers.update(mods)

    # Test 1: Scavenger Clans - Jury Rig (Heal)
    print("\n[Test 1] Jury Rig (Heal)")
    mech = MockUnit("Big Mek", 0, 0, hp=50)
    am.execute_ability(mech, mech, "Ability_Jury_Rig")
    print(f"HP: {mech.current_hp}")
    if mech.current_hp == 90:
        print("PASS: Healed 40 HP.")
    else:
        print("FAIL: Heal value mismatch.")

    # Test 2: Scavenger Clans - More Dakka (Buff)
    print("\n[Test 2] More Dakka (Buff)")
    jet = MockUnit("Dakka Jet", 0, 0)
    am.execute_ability(jet, jet, "Ability_More_Dakka")
    mods = jet.temp_modifiers
    if mods.get("damage_mult") == 2.0 and mods.get("accuracy_mult") == 0.5:
        print("PASS: More Dakka applied.")
    else:
        print(f"FAIL: Mods {mods}")

    # Test 3: Ancient Guardians - Webway Strike (Teleport)
    print("\n[Test 3] Webway Strike (Teleport)")
    spider = MockUnit("Warp Spider", 5, 5)
    # Register in grid
    grid.place_unit(spider, 5, 5)
    
    context = {"grid": grid}
    res = am.execute_ability(spider, spider, "Ability_Webway_Strike", context)
    
    if res["applied"] and (spider.grid_x != 5 or spider.grid_y != 5):
        print(f"PASS: Teleported to ({spider.grid_x}, {spider.grid_y}).")
    else:
        print("FAIL: Did not move.")

    # Test 4: Ancient Guardians - Prescience (Buff)
    print("\n[Test 4] Prescience (Buff)")
    farseer = MockUnit("Farseer", 0, 0)
    am.execute_ability(farseer, farseer, "Ability_Prescience")
    mods = farseer.temp_modifiers
    if mods.get("evasion") == 0.3 and mods.get("accuracy_mult") == 1.2:
        print("PASS: Precognition granted.")
    else:
        print("FAIL: Buff checking.")

if __name__ == "__main__":
    verify_part5()
