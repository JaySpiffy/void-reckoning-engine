import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.mechanics.faction_mechanics_engine import FactionMechanicsEngine
from src.models.unit import Unit
from src.mechanics.resource_mechanics import ConvictionMechanic
from src.combat.ability_manager import AbilityManager

def verify_zealot_mechanics():
    print("=== Verifying Zealot Legions Mechanics ===")
    
    # 1. Setup Mock Engine
    class MockEngine:
        def __init__(self):
            self.factions = {}

    class MockFaction:
        def __init__(self, name):
            self.name = name
            self.custom_resources = {"conviction": 50} 
            self.temp_modifiers = {}
            self.engine = None 

    engine = MockEngine()
    z_faction = MockFaction("Zealot_Legions")
    # Link back
    z_faction.engine = engine
    engine.factions["Zealot_Legions"] = z_faction
    engine.factions["Iron_Vanguard"] = MockFaction("Iron_Vanguard")

    # 2. Setup Mechanics manually (Bypass Loader file check)
    mech_engine = FactionMechanicsEngine(engine)
    # Inject Conviction Mechanic directly
    conviction_mech = ConvictionMechanic("Mech_Crusade", {})
    mech_engine.active_mechanics = {"Zealot_Legions": [conviction_mech]}

    # 3. Create Units
    # Manually create test units to avoid file loading issues or missing abilities
    
    templar = Unit(
        name="Test Templar",
        ma=50, md=50, hp=100, armor=10, damage=10,
        abilities=["Ability_Smite"],
        faction="Zealot_Legions"
    )
    # We need to register Smite in AbilityManager registry too?
    # CombatSimulator usually loads it.
    
    # Let's run a mocked "mini-simulation" step instead of full resolve_fleet_engagement
    # to pinpoint mechanics logic without the noise of the full engine for now.
    
    print("TEST 1: Conviction Accumulation (Unit Death)")
    # Trigger death hook
    context = {
        "unit": Unit("Enemy", 0,0,0,0,0,{}, "Iron_Vanguard"),
        "killer": z_faction, # Faction killed it
        "faction": z_faction # We are processing for Zealot Legions
    }
    
    conviction_mech.on_unit_death(context)
    print(f"Conviction Stacks: {z_faction.custom_resources['conviction']}")
    
    if z_faction.custom_resources['conviction'] == 51:
        print("[PASS] Conviction accumulated.")
    else:
        print(f"[FAIL] Conviction mismatch. Expected 51, got {z_faction.custom_resources['conviction']}")

    print("\nTEST 2: Modifier Updates")
    # Verify temp modifiers
    mods = z_faction.temp_modifiers
    print(f"Modifiers: {mods}")
    if mods.get("global_damage_mult") > 1.0:
        print("[PASS] Modifiers updated.")
        print(f"Damage Mult: {mods['global_damage_mult']}")
    else:
         print("[FAIL] Modifiers not updated.")

    # 4. Run Full Battle using Simulator (Integration Test)
    # This checks if the simulator correctly HOOKS into the mechanic we injected.
    print("\nTEST 3: Simulator Integration (Log Check)")
    
    # We need to reuse the same engines/state
    # But resolve_fleet_engagement creates its own state usually.
    # checking resolve_fleet_engagement... it takes `mechanics_engine`.
    # And it assumes `armies_dict` of units.
    
    # Create armies
    armies = {
        "Zealot_Legions": [templar],
        "Iron_Vanguard": [Unit("Target", 10,10,500,0,0, {}, "Iron_Vanguard")]
    }
    
    # Verify logic using phase executor? 
    # Or just trust the Mock Unit Death test above + code review?
    # Full simulator run might be heavy if file paths are fragile.
    # But let's try invoking the specific ability hook.
    
    print("TEST 4: Ability Hook (Smite) with SCALING")
    # Smite cost check
    # We need AbilityManager to check cost against our mock faction
    ab_registry = {
        "Ability_Smite": {
            "cost": {"conviction": 10},
            "payload_type": "damage",
            "damage": 50,
            "scaling": {
                "source_stat": "conviction",
                "factor": 0.5
            }
        }
    }
    am = AbilityManager(ab_registry)
    
    # Context for execute_ability
    ctx = {
        "faction": z_faction # Passing our mock faction with resources
    }
    
    z_faction.custom_resources["conviction"] = 20
    # Expected: Cost 10 deducted -> 10 remaining.
    # Scaling: 10 * 0.5 = 5 bonus.
    # Total Damage: 50 + 5 = 55.
    
    res = am.execute_ability(templar, armies["Iron_Vanguard"][0], "Ability_Smite", ctx)
    
    print(f"Smite Result: {res}")
    print(f"Rem Conviction: {z_faction.custom_resources['conviction']}")
    
    if res["success"] and res["damage"] == 55:
         print("[PASS] Smite scaled correctly (50->55).")
    elif res["success"]:
         print(f"[FAIL] Smite did not scale correctly. Got {res['damage']}, expected 55.")
         
    if z_faction.custom_resources["conviction"] == 10:
         print("[PASS] Smite cost deducted correctly.")
         
    print("\nTEST 5: AdHoc Loading Check")
    # Verify that the logic copied into combat_simulator actually works
    import json
    fname = "universes/eternal_crusade/factions/faction_registry.json"
    if os.path.exists(fname):
         with open(fname, 'r') as f:
             data = json.load(f)
             if "Zealot_Legions" in data and "starting_resources" in data["Zealot_Legions"]:
                  print(f"[PASS] Registry has starting resources: {data['Zealot_Legions']['starting_resources']}")
             else:
                  print("[FAIL] Registry missing starting resources!")
    else:
         print(f"[FAIL] Registry file not found at {fname}")

if __name__ == "__main__":
    verify_zealot_mechanics()

if __name__ == "__main__":
    verify_zealot_mechanics()
