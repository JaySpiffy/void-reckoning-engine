
import sys
import os
sys.path.append(os.getcwd())

from src.models.unit import Unit, Component
import src.core.balance as bal

# Mock Balance constants if needed (though we import them)
print(f"SPILLOVER RATIO: {bal.COMPONENT_SPILLOVER_DMG_RATIO}")

def test_blowthrough():
    print("\n--- TEST: Blowthrough Damage ---")
    
    # Create Unit
    unit = Unit(
        name="Test Frigate",
        ma=50, md=50, hp=1000, armor=20, damage=100, abilities={},
        faction="Hive_Swarm",
        domain="space",
        tier=2
    )
    
    # Verify initial state
    print(f"Use created. HP: {unit.current_hp}/{unit.base_hp}")
    
    # Add a component (low HP)
    comp = Component("Weak Point", 10, "Weapon")
    unit.components = [comp]
    
    print(f"Component: {comp.name} HP: {comp.current_hp}")
    
    # Apply Massive Damage to Component
    damage_amount = 6000
    print(f"Applying {damage_amount} Damage to Component...")
    
    unit.take_damage(damage_amount, target_component=comp)
    
    print(f"Post-Damage Unit HP: {unit.current_hp}")
    print(f"Post-Damage Comp HP: {comp.current_hp}")
    print(f"Is Destroyed? {comp.is_destroyed}")
    
    if unit.current_hp <= 0:
        print("SUCCESS: Unit Died from Blowthrough!")
    else:
        print("FAILURE: Unit Survived!")

def test_invincible_zombie():
    print("\n--- TEST: Invincible Zombie Check ---")
    # Simulate a loop of hits
    unit = Unit(name="Zombie Target", ma=50, md=50, hp=1000, armor=20, damage=100, abilities={}, faction="Hive_Swarm")
    
    # Create valid component
    comp = Component("Shield Gen", 100, "Shield")
    unit.components = [comp]
    
    print(f"Starting HP: {unit.current_hp}")
    
    # Hit 1: Kill Component
    unit.take_damage(200, target_component=comp)
    print(f"Hit 1 (200 dmg to Comp): Unit HP: {unit.current_hp}, Comp HP: {comp.current_hp}, Destroyed: {comp.is_destroyed}")
    
    # Hit 2: Hit destroyed component again?
    # Logic in take_damage: elif target_component.is_destroyed: self.current_hp -= amount
    unit.take_damage(6000, target_component=comp)
    print(f"Hit 2 (6000 dmg to Dead Comp): Unit HP: {unit.current_hp}")

if __name__ == "__main__":
    test_blowthrough()
    test_invincible_zombie()
