import sys
import os
sys.path.append(os.getcwd())

from src.combat.ability_manager import AbilityManager

def verify_hive_mechanics():
    print("--- Verifying Hive Swarm Mechanics ---")
    
    registry = {
        "Ability_Consume": {
            "id": "Ability_Consume",
            "payload_type": "drain",
            "damage": 40,
            "heal_ratio": 0.5,
            "cost": {"biomass": 5}
        },
        "Ability_Rapid_Evolution": {
             "id": "Ability_Rapid_Evolution",
             "payload_type": "buff",
             "effects": {"armor_mult": 1.5, "duration": 2},
             "cost": {"biomass": 10}
        }
    }
    
    am = AbilityManager(registry)
    
    class MockFaction:
        def __init__(self):
             self.name = "Hive_Swarm"
             self.custom_resources = {"biomass": 20}
             
    class MockUnit:
        def __init__(self, name, hp, max_hp):
             self.name = name
             self.current_hp = hp
             self.max_hp = max_hp
             self.temp_modifiers = {}
             
        def take_damage(self, amt):
             self.current_hp -= amt
             return False
        def heal(self, amt):
             self.current_hp += amt
             return amt
        def apply_temporary_modifiers(self, mods):
             self.temp_modifiers.update(mods)

    # Test Consume
    print("\n[Test 1] Consume Ability (Drain)")
    source = MockUnit("Apex", 50, 100) # Injured
    target = MockUnit("Prey", 100, 100)
    faction = MockFaction()
    
    res = am.execute_ability(source, target, "Ability_Consume", {"faction": faction})
    
    print(f"Result: {res}")
    print(f"Source HP: {source.current_hp}")
    print(f"Biomass: {faction.custom_resources['biomass']}")
    
    if res["success"] and source.current_hp == 70 and faction.custom_resources['biomass'] == 15:
         print("PASS: Drained 40, Healed 20, Spent 5 Biomass.")
    else:
         print("FAIL: Consume logic error.")

    # Test Rapid Evolution
    print("\n[Test 2] Rapid Evolution (Buff)")
    res2 = am.execute_ability(source, source, "Ability_Rapid_Evolution", {"faction": faction})
    print(f"Buffs: {source.temp_modifiers}")
    
    if res2["success"] and source.temp_modifiers.get("armor_mult") == 1.5:
         print("PASS: Evolution applied.")
    else:
         print("FAIL: Evolution error.")

if __name__ == "__main__":
    verify_hive_mechanics()
