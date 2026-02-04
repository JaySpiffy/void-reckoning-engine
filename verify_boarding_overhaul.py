import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.getcwd())

from src.models.unit import Ship
from src.combat.ability_manager import AbilityManager
from src.combat.tactical_grid import TacticalGrid
from src.combat.components.crew_component import CrewComponent
from src.combat.components.health_component import HealthComponent

def test_boarding():
    print("--- STARTING BOARDING OVERHAUL VERIFICATION ---")
    
    # 1. Setup
    am = AbilityManager()
    am.registry = {
        "lightning_strike_v1": {
            "payload_type": "boarding",
            "boarding_type": "lightning_strike",
            "troop_damage": 20,
            "cooldown": 0
        },
        "boarding_pods_v1": {
            "payload_type": "boarding",
            "boarding_type": "pods",
            "troop_damage": 30,
            "cooldown": 0
        }
    }
    
    grid = TacticalGrid(100, 100)
    
    source = Ship("Attacker", "Empire")
    target = Ship("Defender", "Orks")
    
    # Ensure they have crew components (initialized via Ship -> Unit fallback in my earlier fix)
    # But for explicit test focus, we can replace them
    target.crew_comp = CrewComponent(max_crew=100, current_crew=100, troop_value=10)
    target.health_comp = HealthComponent(max_hp=500, max_shield=100)
    
    source.grid_x, source.grid_y = 0, 0
    target.grid_x, target.grid_y = 10, 0 # Distance 10
    
    context = {"grid": grid, "battle_state": MagicMock(total_sim_time=0.0)}
    
    # 2. Test Lightning Strike (Shields Up)
    print("\n[Test 1] Lightning Strike vs Shields Up")
    target.health_comp.current_shield = 100
    res = am.execute_ability(source, target, "lightning_strike_v1", context)
    print(f"Result: {res.get('reason')} (Success: {res['success']})")
    assert res["success"] is False
    
    # 3. Test Lightning Strike (Shields Down)
    print("\n[Test 2] Lightning Strike vs Shields Down")
    target.health_comp.current_shield = 0
    res = am.execute_ability(source, target, "lightning_strike_v1", context)
    print(f"Result: {res.get('description')} (Success: {res['success']})")
    assert res["success"] is True
    print(f"Target Crew: {target.crew_comp.current_crew}/100")
    
    # 4. Test Boarding Pods Range
    print("\n[Test 3] Boarding Pods Out of Range")
    target.grid_x = 50 # Distance 50 (Range for pods is 25)
    res = am.execute_ability(source, target, "boarding_pods_v1", context)
    print(f"Result: {res.get('reason')} (Success: {res['success']})")
    assert res["success"] is False
    
    # 5. Test Boarding Pods Successful Attrition
    print("\n[Test 4] Boarding Pods Success & Drifting Hulk")
    target.grid_x = 5
    target.crew_comp.current_crew = 10 # Low crew
    res = am.execute_ability(source, target, "boarding_pods_v1", context)
    print(f"Result: {res.get('description')}")
    print(f"Target Crew: {target.crew_comp.current_crew}/100")
    print(f"Is Target Alive? {target.is_alive()}")
    assert target.is_alive() is False
    assert target.crew_comp.is_hulk is True
    
    # 6. Test Call to Arms Defense
    print("\n[Test 5] Call to Arms Bonus")
    target.crew_comp = CrewComponent(max_crew=100, current_crew=100, troop_value=10)
    target.current_stance = "STANCE_CALL_TO_ARMS"
    print(f"Stance: {target.current_stance}")
    print(f"Effective Troop Defense: {target.troop_defense}")
    
    # Reset target and attacker for controlled attrition test
    target.crew_comp.current_crew = 100
    # Pods do 30 troop damage. Def 10 -> divisor 2. Killed = 15.
    # With Stance Call to Arms (+5) -> Def 15 -> divisor 3. Killed = 10.
    res = am.execute_ability(source, target, "boarding_pods_v1", context)
    print(f"Crew Killed with Call to Arms: {res.get('crew_killed')}")
    assert res.get('crew_killed') <= 10
    
    # 7. Test Embarked Armies Bonus
    print("\n[Test 6] Embarked Armies Bonus")
    target.crew_comp = CrewComponent(max_crew=100, current_crew=100, troop_value=10)
    target.current_stance = "STANCE_BALANCED"
    
    # Mock a fleet with an army
    mock_fleet = MagicMock()
    mock_army = MagicMock()
    mock_army.power = 200 # Should add 20 to bonus_atk
    mock_fleet.cargo_armies = [mock_army]
    source.set_fleet(mock_fleet)
    
    # Pods (30) + Army Bonus (200 // 5 = 40) = 70 Attack.
    # Def 10 -> divisor 2. Killed = 35.
    res = am.execute_ability(source, target, "boarding_pods_v1", context)
    print(f"Crew Killed with Embarked Army: {res.get('crew_killed')}")
    assert res.get('crew_killed') == 35
    
    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    test_boarding()
