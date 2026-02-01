import sys
import os

# Ensure src is in path
sys.path.append(os.getcwd())

from src.models.fleet import Fleet
from src.models.army import ArmyGroup
from src.models.unit import Unit, Ship

# Mock Planet
class MockPlanet:
    def __init__(self):
        self.name = "TestPlanet"
        self.armies = []
        self.type = "Planet"
        self.node_reference = None # Fix for Fleet init

# Setup
p = MockPlanet()
fleet = Fleet("F1", "Chaos", p)

# Create a ship with capacity 1
# Ship(name, ma, md, hp, armor, damage, abilities, faction, authentic_weapons, rank, shield, traits, cost, transport_capacity)
ship_template = Ship("Transport", 1, 1, 10, 10, 1, {}, "Chaos", None, 0, 0, [], 150, 1) # transport_capacity=1
fleet.units.append(ship_template)

print(f"Fleet Transport Capacity: {fleet.transport_capacity}")
print(f"Fleet Used Capacity (Initial): {fleet.used_capacity}")

# Create an Army with 2 units
u1 = Unit("Warrior", 1, 1, 1, 1, 1, {}, "Chaos")
u2 = Unit("Warrior", 1, 1, 1, 1, 1, {}, "Chaos")
army = ArmyGroup("A1", "Chaos", [u1, u2], p)
p.armies.append(army)

print(f"Army Size: {army.get_total_size()}")

# Simulate Campaign Logic (Split and Embark)
space = fleet.transport_capacity - fleet.used_capacity
print(f"Required Space: 1. Available Space: {space}")

if space < army.get_total_size():
    print("Attempting Split...")
    # Simulate CampaignManager logic
    detachment = army.split_off(space)
    
    if detachment:
        print(f"Detachment created with {len(detachment.units)} units.")
        print(f"Original Army size now: {len(army.units)}")
        
        # Simulate BattleManager.embark_army logic
        fleet.cargo_armies.append(detachment)
        print(f"Embarked Detachment. Used Capacity: {fleet.used_capacity}")
        
        if fleet.used_capacity == 0:
            print("BUG REPRODUCED: Used Capacity is 0 despite embark.")
        else:
            print(f"Success: Used Capacity is {fleet.used_capacity}")
            
    else:
        print("Split failed (returned None)")
else:
    print("No split needed (Logic Error in test setup)")
