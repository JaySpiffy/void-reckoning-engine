import sys
import os
sys.path.append(os.getcwd())

from src.combat.ability_manager import AbilityManager
from src.combat.tactical_grid import TacticalGrid

def verify_part4():
    print("--- Verifying Rift Daemons & Ascended Order ---")
    
    registry = {
        "Ability_Warp_Rift": {
            "id": "Ability_Warp_Rift",
            "payload_type": "aoe_damage",
            "damage": 30,
            "radius": 2
        },
        "Ability_Terror_Scream": {
            "id": "Ability_Terror_Scream",
            "payload_type": "debuff",
            "effects": {"accuracy_mult": 0.5, "duration": 2}
        },
        "Ability_Psionic_Storm": {
            "id": "Ability_Psionic_Storm",
            "payload_type": "aoe_damage",
            "damage": 25,
            "radius": 3
        },
        "Ability_Mind_Control": {
            "id": "Ability_Mind_Control",
            "payload_type": "mind_control",
            "duration": 1
        }
    }
    
    am = AbilityManager(registry)
    grid = TacticalGrid(10, 10)
    
    class MockUnit:
        def __init__(self, name, x, y, hp=100):
            self.name = name
            self.grid_x = x
            self.grid_y = y
            self.current_hp = hp
            self.max_hp = 100
            self.temp_modifiers = {}
            self.type = "infantry"
            self.components = [MockComponent("Weapon")] # For Mind Control
            
        def take_damage(self, amt):
            self.current_hp -= amt
            return False
            
        def apply_temporary_modifiers(self, mods):
            self.temp_modifiers.update(mods)
            
    class MockComponent:
        def __init__(self, ctype):
            self.type = ctype

    # Test 1: Rift Daemons - Warp Rift (AoE)
    print("\n[Test 1] Warp Rift (AoE)")
    herald = MockUnit("Herald", 0, 0)
    # Targets
    t1 = MockUnit("T1", 2, 0) # Dist 2 (Hit)
    t2 = MockUnit("T2", 3, 0) # Dist 3 (Miss)
    enemies = [t1, t2]
    context = {"grid": grid, "enemies": enemies}
    
    res = am.execute_ability(herald, t1, "Ability_Warp_Rift", context)
    print(f"Result: {res}")
    
    if res["affected_count"] == 1 and t1.current_hp == 70:
        print("PASS: Warp Rift hit correctly.")
    else:
        print(f"FAIL: Targets hit: {res.get('affected_count')}")

    # Test 2: Rift Daemons - Terror Scream (Debuff)
    print("\n[Test 2] Terror Scream (Debuff)")
    screamer = MockUnit("Screamer", 0, 0)
    target = MockUnit("Coward", 0, 0)
    am.execute_ability(screamer, target, "Ability_Terror_Scream")
    
    if target.temp_modifiers.get("accuracy_mult") == 0.5:
        print("PASS: Terror applied.")
    else:
        print("FAIL: Debuff missing.")

    # Test 3: Ascended Order - Psionic Storm (AoE)
    print("\n[Test 3] Psionic Storm (AoE)")
    magus = MockUnit("Magus", 5, 5)
    # Targets in radius 3
    t3 = MockUnit("T3", 7, 5) # Dist 2
    t4 = MockUnit("T4", 8, 5) # Dist 3
    enemies = [t3, t4]
    context = {"grid": grid, "enemies": enemies}
    
    res = am.execute_ability(magus, magus, "Ability_Psionic_Storm", context) # Self-centered or target? Usually target centered. Let's assume target=center for now.
    
    if res["affected_count"] == 2:
        print("PASS: Psionic Storm hit all targets.")
    else:
        print(f"FAIL: Count {res.get('affected_count')}")

    # Test 4: Ascended Order - Mind Control
    print("\n[Test 4] Mind Control")
    weaver = MockUnit("Weaver", 0, 0)
    enemy1 = MockUnit("Enemy1", 0, 1) # Target
    enemy2 = MockUnit("Enemy2", 0, 2) # Friendly fire victim (dist 1)
    
    context = {"grid": grid, "enemies": [weaver, enemy1, enemy2]} 
    # Mind Control logic expects "enemies" to be the victim's allies (caster's enemies).
    
    # We need to ensure 'execute_weapon_fire' functionality is mocked or handled. 
    # _handle_mind_control imports execute_weapon_fire locally. 
    # This might fail in isolation without full mocks. 
    # I will patch execute_weapon_fire in the script.
    
    import src.combat.ability_manager as am_mod
    
    # Mock return
    def mock_fire(*args):
        return {"damage": 10}
        
    # We need to inject this into the module namespace used by _handle_mind_control
    # But _handle_mind_control does 'from src.combat.combat_utils import execute_weapon_fire'
    # So we must mock sys.modules or the function in that module.
    
    # Strategy: Just define the module if not exists or patch it.
    import types
    if "src.combat.combat_utils" not in sys.modules:
        m = types.ModuleType("src.combat.combat_utils")
        m.execute_weapon_fire = mock_fire
        sys.modules["src.combat.combat_utils"] = m
    else:
        sys.modules["src.combat.combat_utils"].execute_weapon_fire = mock_fire

    res = am.execute_ability(weaver, enemy1, "Ability_Mind_Control", context)
    print(f"Result: {res}")
    
    if res["applied"] and "Confused!" in res["description"]:
        print("PASS: Mind Control triggered friendly fire.")
    else:
        print("FAIL: Mind control logic.")

if __name__ == "__main__":
    verify_part4()
