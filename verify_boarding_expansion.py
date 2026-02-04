import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.models.unit import Unit
from src.combat.components.crew_component import CrewComponent
from src.combat.components.health_component import HealthComponent
from src.combat.components.weapon_component import WeaponComponent
from src.combat.ability_manager import AbilityManager
from src.combat.combat_tracker import CombatTracker

class MockBattleState:
    def __init__(self, tracker):
        self.tracker = tracker
        self.name = "Mock Battle"

def test_boarding_expansion():
    print("--- Starting Boarding Expansion Verification ---")
    
    # 1. Setup AbilityManager
    # Mock registry for testing
    registry = {
        "Boarding Pods": {"payload_type": "boarding"},
        "Lightning Strike": {"payload_type": "boarding"},
        "Assault Boats": {"payload_type": "boarding"}
    }
    ab_manager = AbilityManager(registry)
    
    # 2. Setup Source and Target Units
    source = Unit("Raider", "Pirates")
    source.add_component(CrewComponent(max_crew=100))
    source.add_component(HealthComponent(100))
    
    # Add a Boarding Pod component to the source
    pod_comp = WeaponComponent("MK1 Pods", {"troop_damage": 30, "range": 25, "pd_intercept_chance": 0.4}, tags=["boarding", "pods"])
    source.add_component(pod_comp)
    
    target = Unit("Merchantman", "Civilians")
    target.add_component(CrewComponent(max_crew=50))
    target.add_component(HealthComponent(200))
    
    # 3. Verify Dynamic Ability Detection
    print("\n[Test 1] Dynamic Ability Detection")
    abilities = source.abilities
    if "Boarding Pods" in abilities:
        print("SUCCESS: Boarding Pods ability detected from component tags.")
        print(f"Stats: {abilities['Boarding Pods']}")
    else:
        print("FAILURE: Boarding Pods ability not found.")
        return False

    # 4. Verify Hulk Capture Logic
    print("\n[Test 2] Hulk Capture Logic")
    # Reduce target crew to 0 to make it a hulk
    target.crew_comp.current_crew = 0
    print(f"Initial Target Faction: {target.faction}")
    print(f"Target is hulk: {target.crew_comp.is_hulk}")
    
    # Setup tracker and battle state
    tracker = CombatTracker()
    battle_state = MockBattleState(tracker)
    context = {"ability_manager": ab_manager, "battle_state": battle_state}
    result = {"applied": False}
    
    # Execute capture
    ab_manager._handle_boarding(source, target, abilities["Boarding Pods"], result, context)
    
    print(f"Result: {result.get('description', 'No description')}")
    
    # Verify Logging
    capture_events = [e for e in tracker.events if e["type"] == "capture"]
    if capture_events:
        print(f"SUCCESS: Capture event found in tracker: {capture_events[0]}")
    else:
        print("FAILURE: Capture event not found in tracker.")
        return False
    
    print(f"New Target Faction: {target.faction}")
    print(f"Target crew: {target.crew_comp.current_crew}")
    print(f"Source crew: {source.crew_comp.current_crew}")
    print(f"Target is hulk: {target.crew_comp.is_hulk}")
    
    if target.faction == "Pirates" and target.crew_comp.current_crew == 10 and not target.crew_comp.is_hulk:
        print("SUCCESS: Hulk captured and restored.")
    else:
        print("FAILURE: Capture logic did not work as expected.")
        return False

    # 5. Verify Lightning Strike Dynamic Detection
    print("\n[Test 3] Lightning Strike Detection")
    source.weapon_comps = [] # Clear components
    ls_comp = WeaponComponent("LS Teleporter", {"troop_damage": 20, "range": 15}, tags=["boarding", "teleportation"])
    source.add_component(ls_comp)
    
    abilities = source.abilities
    if "Lightning Strike" in abilities:
        print("SUCCESS: Lightning Strike detected.")
        print(f"Stats: {abilities['Lightning Strike']}")
    else:
        print("FAILURE: Lightning Strike not found.")
        return False

    print("\n--- Boarding Expansion Verification PASSED ---")
    return True

if __name__ == "__main__":
    success = test_boarding_expansion()
    if not success:
        sys.exit(1)
