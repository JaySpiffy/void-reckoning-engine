import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.mechanics.resource_mechanics import ConvictionMechanic
from src.combat.ability_manager import AbilityManager

def verify_conviction_mechanic():
    print("--- Verifying Zealot Legions: Conviction Mechanics ---")
    
    # 1. Setup Environment
    class MockFaction:
        def __init__(self, name):
            self.name = name
            self.custom_resources = {"conviction": 0}
            self.temp_modifiers = {}
            
    class MockUnit:
        def __init__(self, name):
            self.name = name
            
    faction = MockFaction("Zealot_Legions")
    enemy_faction = MockFaction("Heathens")
    
    mech = ConvictionMechanic("Mech_Crusade", {})
    
    # 2. Test Gain on Kill
    print("\n[Test 1] Gain Conviction on Kill")
    # Context: killer is Zealot faction
    ctx = {"killer": faction, "faction": faction, "unit": MockUnit("Victim")}
    mech.on_unit_death(ctx)
    
    print(f"Conviction: {faction.custom_resources['conviction']}")
    if faction.custom_resources['conviction'] == 1:
        print("PASS: Gained 1 stack.")
    else:
        print("FAIL: Stack logic error.")
        
    # Gain more
    faction.custom_resources["conviction"] = 20
    
    # 3. Test Modifiers (Decay/Spend/Bonus)
    print("\n[Test 2] Modifier Application")
    mech.on_economy_phase({"faction": faction})
    dmg_mult = faction.temp_modifiers.get("global_damage_mult", 1.0)
    ab_mult = faction.temp_modifiers.get("ability_power_mult", 1.0)
    print(f"Stacks: 20 -> Damage Mult: {dmg_mult}, Ability Mult: {ab_mult}")
    
    if dmg_mult == 1.1 and ab_mult == 1.1:
        print("PASS: 10% bonus applied for 20 stacks.")
    else:
        print(f"FAIL: Bonus calcs wrong. {dmg_mult}")
        
    # 4. Test Spending via AbilityManager
    print("\n[Test 3] Spend Conviction")
    registry = {
        "Ability_Smite": {
            "id": "Ability_Smite", 
            "cost": {"conviction": 10},
            "payload_type": "damage"
        }
    }
    am = AbilityManager(registry)
    source = MockUnit("Caster")
    target = MockUnit("Target")
    # Mock target functionality for run
    target.take_damage = lambda x: 0
    target.name = "Target"
    source.name = "Caster"
    
    res = am.execute_ability(source, target, "Ability_Smite", {"faction": faction})
    
    print(f"Execution Result: {res['success']}")
    print(f"Remaining Stacks: {faction.custom_resources['conviction']}")
    
    if res["success"] and faction.custom_resources["conviction"] == 10:
        print("PASS: Smite cast, 10 stacks spent.")
    else:
        print("FAIL: Spend logic mismatch.")

if __name__ == "__main__":
    verify_conviction_mechanic()
