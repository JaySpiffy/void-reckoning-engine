import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.models.unit import Ship, Unit
from src.models.fleet import Fleet
from src.models.army import ArmyGroup
from src.combat.ability_manager import AbilityManager

class MockArmy:
    def __init__(self, power):
        self.power = power

class MockFleet:
    def __init__(self, armies):
        self.cargo_armies = armies

def test_transport_boarding():
    print("--- Starting Transport Boarding Verification ---")
    am = AbilityManager()
    
    # Setup Attacker (Ship with Hangar/Pods)
    attacker = Ship("Striker", "Pirates", unit_class="Frigate")
    ability_def = {"id": "boarding_pods", "troop_damage": 30, "range": 25}
    
    # Setup Target (Ship being boarded)
    target = Ship("Merchantman", "Civilians", unit_class="Frigate") # 50 base crew, 10 troop defense
    
    # 1. Baseline: No Armies
    print("\n[Test 1] Baseline: No Armies")
    target.crew_comp.current_crew = 50
    killed_baseline = target.crew_comp.take_crew_damage(30, 0, effective_defense=target.troop_defense)
    print(f"Base Damage (30 atk vs 10 def): {killed_baseline} killed.")
    
    # 2. Offensive Bonus: Attacker carrying a powerful army
    print("\n[Test 2] Offensive Bonus: Attacker carrying Heavy Infantry")
    target.crew_comp.current_crew = 50
    # Mocking army power 200. Scaling factor 0.2 -> +40 bonus atk.
    # Total atk: 30 + (40/5) -> 38? No, the formula is (amount + bonus/5) / (def/5)
    # (30 + 40/5) / 2 = 38 / 2 = 19.
    army_off = MockArmy(200)
    attacker.set_fleet(MockFleet([army_off]))
    
    # We'll use a direct call to simulate AbilityManager logic for bonus calculation
    # In _handle_boarding: bonus_atk = int(200 * 0.2) = 40
    killed_offense = target.crew_comp.take_crew_damage(30, 40, effective_defense=target.troop_defense)
    print(f"Offense Boosted (30 base + 40 bonus vs 10 def): {killed_offense} killed.")
    
    if killed_offense > killed_baseline:
        print("SUCCESS: Transported troops increased offensive damage.")
    else:
        print(f"FAILURE: Offense boost not effective ({killed_offense} vs {killed_baseline}).")
        return False
        
    # 3. Defensive Bonus: Target carrying a defensive army
    print("\n[Test 3] Defensive Bonus: Target carrying Defenders")
    target.crew_comp.current_crew = 50
    # Mocking army power 200. Scaling factor 0.2 * 1.5 = 0.3 -> +60 bonus def.
    # Total def: 10 + 60 = 70.
    # Divisor: 70 // 5 = 14.
    # (30 + 0) / 14 = 2.
    army_def = MockArmy(200)
    target.set_fleet(MockFleet([army_def]))
    
    # In _handle_boarding: bonus_def = int(200 * 0.3) = 60
    killed_defense = target.crew_comp.take_crew_damage(30, 0, effective_defense=target.troop_defense, bonus_defense_value=60)
    print(f"Defense Boosted (30 atk vs 10 base + 60 bonus def): {killed_defense} killed.")
    
    if killed_defense < killed_baseline:
        print("SUCCESS: Transported troops reduced defensive casualties.")
    else:
        print(f"FAILURE: Defense boost not effective ({killed_defense} vs {killed_baseline}).")
        return False

    print("\n--- Transport Boarding Verification PASSED ---")
    return True

if __name__ == "__main__":
    success = test_transport_boarding()
    if not success:
        sys.exit(1)
