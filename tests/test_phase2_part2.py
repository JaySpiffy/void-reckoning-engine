import sys
import os
sys.path.append(os.getcwd())

from src.combat.ability_manager import AbilityManager
from src.combat.tactical_grid import TacticalGrid

def verify_part2():
    print("--- Verifying Iron Vanguard & Cyber Synod ---")
    
    registry = {
        "Ability_Entrench": {
            "id": "Ability_Entrench",
            "payload_type": "buff",
            "effects": {"armor_mult": 1.25, "duration": 2}
        },
        "Ability_Artillery_Barrage": {
            "id": "Ability_Artillery_Barrage",
            "payload_type": "aoe_damage",
            "damage": 50,
            "radius": 2
        },
        "Ability_Logic_Override": {
            "id": "Ability_Logic_Override",
            "payload_type": "stun"
        },
        "Ability_Repair_Nanites": {
            "id": "Ability_Repair_Nanites",
            "payload_type": "heal",
            "heal": 30
        }
    }
    
    am = AbilityManager(registry)
    
    class MockUnit:
        def __init__(self, name, x, y, hp=100):
            self.name = name
            self.grid_x = x
            self.grid_y = y
            self.current_hp = hp
            self.max_hp = 100
            self.temp_modifiers = {}
            self.type = "infantry"
            self.stunned = False
            
        def take_damage(self, amt):
            self.current_hp -= amt
            return False
            
        def heal(self, amt):
            self.current_hp += amt
            return amt
            
        def apply_temporary_modifiers(self, mods):
            if "stunned" in mods:
                self.stunned = True
            self.temp_modifiers.update(mods)

    # Test 1: Iron Vanguard - Entrench
    print("\n[Test 1] Entrench (Buff)")
    grenadier = MockUnit("Grenadier", 0, 0)
    am.execute_ability(grenadier, grenadier, "Ability_Entrench")
    print(f"Mods: {grenadier.temp_modifiers}")
    if grenadier.temp_modifiers.get("armor_mult") == 1.25:
        print("PASS: Entrenched.")
    else:
        print("FAIL: Buff not applied.")

    # Test 2: Iron Vanguard - Artillery (AoE)
    print("\n[Test 2] Artillery Barrage (AoE)")
    # Need grid context
    grid = TacticalGrid(10, 10)
    center = MockUnit("TargetCenter", 5, 5)
    side = MockUnit("TargetSide", 6, 5) # Dist 1
    far = MockUnit("TargetFar", 9, 9) # Dist > 2
    
    # Grid usually needs units registered?
    # AbilityManager uses grid.get_distance_coords but iterates over 'enemies' list passed in context.
    
    enemies = [center, side, far]
    context = {"grid": grid, "enemies": enemies}
    
    res = am.execute_ability(grenadier, center, "Ability_Artillery_Barrage", context)
    print(f"Result: {res}")
    
    if res["affected_count"] == 2 and center.current_hp == 50 and side.current_hp == 50 and far.current_hp == 100:
        print("PASS: AoE hit 2 units correctly.")
    else:
        print(f"FAIL: AoE logic. Hits: {res.get('affected_count')}")

    # Test 3: Cyber Synod - Logic Override (Stun)
    print("\n[Test 3] Logic Override (Stun)")
    titan = MockUnit("Titan", 0, 0)
    victim = MockUnit("Victim", 0, 0)
    am.execute_ability(titan, victim, "Ability_Logic_Override")
    
    # MockUnit handles apply_temporary_modifiers -> stunned=True
    if victim.stunned:
        print("PASS: Target stunned.")
    else:
        print("FAIL: Stun not applied.")
        
    # Test 4: Cyber Synod - Repair Nanites (Heal)
    print("\n[Test 4] Repair Nanites (Heal)")
    calculator = MockUnit("Prime", 0, 0)
    damaged = MockUnit("Damaged", 0, 0, hp=50)
    
    am.execute_ability(calculator, damaged, "Ability_Repair_Nanites")
    print(f"HP: {damaged.current_hp}")
    
    if damaged.current_hp == 80:
        print("PASS: Healed 30 HP.")
    else:
        print("FAIL: Heal value mismatch.")

if __name__ == "__main__":
    verify_part2()
