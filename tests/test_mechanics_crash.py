
from src.mechanics.combat_mechanics import InstabilityMechanic, AetherOverloadMechanic
from src.models.unit import Unit

class MockFaction:
    def __init__(self, name):
        self.name = name

def test_instability_crash():
    print("Testing InstabilityMechanic with None DNA...")
    mech = InstabilityMechanic("mech_instability", {})
    
    # Unit with None DNA
    u = Unit("Test Unit", 1, 1, 10, 10, 10, {}, faction="Rift_Daemons", elemental_dna=None)
    
    try:
        mech.process_unit_instability(u)
        print("[PASS] InstabilityMechanic did not crash.")
    except AttributeError as e:
        print(f"[FAIL] InstabilityMechanic crashed: {e}")
    except Exception as e:
        print(f"[FAIL] InstabilityMechanic crashed with unrelated error: {e}")

def test_aether_overload_crash():
    print("\nTesting AetherOverloadMechanic with None DNA...")
    mech = AetherOverloadMechanic("mech_aether", {})
    
    # Caster with None DNA
    caster = Unit("Caster", 1, 1, 10, 10, 10, {}, faction="Ascended_Order", elemental_dna=None)
    
    # Ability with High Aether requirement
    ctx = {
        "caster": caster,
        "ability": {
            "elemental_dna": {"atom_aether": 30},
            "payload": {"damage": 10}
        }
    }
    
    try:
        mech.on_ability_use(ctx)
        print("[PASS] AetherOverloadMechanic did not crash.")
    except AttributeError as e:
        print(f"[FAIL] AetherOverloadMechanic crashed: {e}")
    except Exception as e:
        print(f"[FAIL] AetherOverloadMechanic crashed with unrelated error: {e}")

if __name__ == "__main__":
    test_instability_crash()
    test_aether_overload_crash()
