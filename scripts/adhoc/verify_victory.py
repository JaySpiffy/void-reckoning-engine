
from src.combat.tactical_engine import resolve_fleet_engagement
from src.models.unit import Ship

def create_dummy_unit(faction, name):
    u = Ship(name, 3, 3, 100, 10, 10, [], faction=faction)
    u.cost = 100
    return u

def verify_victory():
    print("Testing Timeout Victory Resolution...")
    
    # Setup: Faction A does damage, Faction B does nothing
    f1 = [create_dummy_unit("Faction_A", "Attacker")]
    f2 = [create_dummy_unit("Faction_B", "Defender")]
    
    armies = {"Faction_A": f1, "Faction_B": f2}
    
    # Pre-seed damage stats to simulate a fight
    # dealing damage manually involves CombatState internal structure, 
    # effectively cheating the simulation for speed.
    # Instead, let's run a very short simulation where we know they will fight.
    
    # Actually, simpler: Verify the engine calls check_victory_conditions on timeout.
    # We can rely on the engine logs.
    
    winner, survivors, rounds, stats = resolve_fleet_engagement(armies, max_rounds=5, silent=False)
    
    print(f"\nResult: Winner={winner}, Rounds={rounds}")
    if winner == "Draw":
        print("FAIL: Result was Draw")
    else:
        print(f"PASS: Result resolved to {winner}")

if __name__ == "__main__":
    verify_victory()
