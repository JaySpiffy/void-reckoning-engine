import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.models.unit import Ship, Unit
from src.combat.components.crew_component import CrewComponent
from src.combat.components.weapon_component import WeaponComponent

def test_crew_scaling_and_config():
    print("--- Starting Crew Scaling & Config Verification ---")
    
    # 1. Test Base Scaling by Ship Class
    print("\n[Test 1] Base Scaling by Ship Class")
    corvette = Ship("Interceptor", "Pirates", unit_class="Corvette")
    cruiser = Ship("Monitor", "Pirates", unit_class="Cruiser")
    
    print(f"Corvette Max Crew: {corvette.crew_comp.max_crew}")
    print(f"Cruiser Max Crew: {cruiser.crew_comp.max_crew}")
    
    if corvette.crew_comp.max_crew == 20 and cruiser.crew_comp.max_crew == 150:
        print("SUCCESS: Base crew scales correctly with Ship Class.")
    else:
        print("FAILURE: Base crew scaling failed.")
        return False
        
    # 2. Test Hull Customization (Added Crew)
    print("\n[Test 2] Hull Customization (Added Crew)")
    # Add Standard Crew Quarters (+20)
    quarters = WeaponComponent("Crew Quarters", {"added_crew": 20}, tags=["hull", "crew"])
    corvette.add_component(quarters)
    
    print(f"Corvette Crew BEFORE recalc: {corvette.crew_comp.max_crew}")
    corvette.recalc_stats()
    print(f"Corvette Crew AFTER recalc: {corvette.crew_comp.max_crew}")
    
    if corvette.crew_comp.max_crew == 40: # 20 base + 20 bonus
        print("SUCCESS: Hull configuration expanded crew capacity.")
    else:
        print("FAILURE: Crew expansion failed.")
        return False
        
    # 3. Test Hull Customization (Barracks)
    print("\n[Test 3] Hull Customization (Barracks & Defense)")
    # Initial troop defense
    print(f"Corvette Troop Defense BEFORE: {corvette.crew_comp.troop_value}")
    
    # Add Barracks (+50 crew, +2 defense)
    barracks = WeaponComponent("Ship Barracks", {"added_crew": 50, "troop_defense_bonus": 2}, tags=["hull", "crew", "military"])
    corvette.weapon_comps = [quarters, barracks] # Replace/Append
    corvette.recalc_stats()
    
    print(f"Corvette Max Crew: {corvette.crew_comp.max_crew}")
    print(f"Corvette Troop Defense AFTER: {corvette.crew_comp.troop_value}")
    
    # Expected: 20 base + 20 (Quarters) + 50 (Barracks) = 90
    # Expected: 5 base + 2 (Barracks) = 7
    if corvette.crew_comp.max_crew == 90 and corvette.crew_comp.troop_value == 7:
        print("SUCCESS: Barracks correctly applied crew and troop defense bonuses.")
    else:
        print("FAILURE: Barracks stat application failed.")
        return False

    print("\n--- Crew Scaling & Config Verification PASSED ---")
    return True

if __name__ == "__main__":
    success = test_crew_scaling_and_config()
    if not success:
        sys.exit(1)
