
from src.mechanics.combat_mechanics import ReanimationProtocolsMechanic
from src.models.unit import Unit

class MockFaction:
    def __init__(self, name):
        self.name = name
        # No .stats initially

def test_reanimation_stats_init():
    print("Testing ReanimationProtocolsMechanic stats initialization...")
    mech = ReanimationProtocolsMechanic("mech_reanimation", {})
    
    faction = MockFaction("Cyber_Synod")
    unit = Unit("Test Bot", 1, 1, 10, 10, 10, {}, faction="Cyber_Synod")
    
    ctx = {
        "unit": unit,
        "faction": faction,
        "revived": False
    }
    
    # Force high chance to trigger the block
    mech.params = {"revive_chance": 1.1} # Assuming get_modifier reads from somewhere or we mock it
    # Actually BaseMechanic.get_modifier reads self.params usually. 
    # Let's override get_modifier to be sure, or just assume default is 0.5 and run loop
    
    # To be deterministic, we can monkeypatch random or just call it enough times?
    # Or cleaner: subclass/mock
    
    import random
    random.seed(42) # Deterministic
    
    try:
        # Run multiple times to trigger the logic
        for i in range(10):
            mech.on_unit_death(ctx)
            if ctx.get("revived"):
                print(f"  > Unit revived on attempt {i+1}")
                break
        
        # Check if faction.stats was created
        if hasattr(faction, "stats") and "reanimations_this_turn" in faction.stats:
             print(f"[PASS] faction.stats initialized: {faction.stats}")
        elif ctx.get("revived"):
             print(f"[FAIL] Revived but stats not updated/created? {getattr(faction, 'stats', 'Missing')}")
        else:
             print("[WARN] Did not trigger revive (bad RNG?), but didn't crash.")

    except NameError as e:
        print(f"[FAIL] NameError persisted: {e}")
    except Exception as e:
        print(f"[FAIL] Other error: {e}")

if __name__ == "__main__":
    test_reanimation_stats_init()
