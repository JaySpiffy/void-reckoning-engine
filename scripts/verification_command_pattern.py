import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from src.commands.command_bus import CommandBus
from src.commands.move_fleet_command import MoveFleetCommand
from src.commands.build_command import BuildCommand
from src.commands.attack_command import AttackCommand

# Mock Classes for Testing
class MockFleet:
    def __init__(self, fid):
        self.id = fid
        self.name = f"Fleet {fid}"
        self.location = None
        self.destination = None
        self.route = []
        self.tactical_directive = "HOLD"
        self.is_destroyed = False
        self.is_engaged = False
        self.units = ["Unit1"]
        self.cargo_armies = []
        
    def move_to(self, target, force=False, engine=None):
        print(f"DEBUG: Fleet {self.id} moving to {target}")
        self.destination = target
        return True

class MockPlanet:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
        self.construction_queue = []
        
class MockFaction:
    def __init__(self, name, req):
        self.name = name
        self.requisition = req
        
    def can_afford(self, cost):
        return self.requisition >= cost
        
    def construct_building(self, planet, building_id):
        print(f"DEBUG: Constructing {building_id} on {planet.name}")
        planet.construction_queue.append({"id": building_id})
        return True
        
    def deduct_cost(self, cost):
        self.requisition -= cost
        
    def track_construction(self, cost):
        pass

def verify_commands():
    print("Verifying Command Pattern (Phase 7)...")
    
    bus = CommandBus()
    
    # 1. Test Move Command
    print("\n--- Testing MoveFleetCommand ---")
    fleet = MockFleet(1)
    planet_a = MockPlanet("Planet A", "Imperium")
    engine = MagicMock()
    
    move_cmd = MoveFleetCommand(fleet, planet_a, engine)
    
    if bus.execute(move_cmd):
        print("[OK] MoveCommand executed.")
        if fleet.destination == planet_a:
            print("[OK] Fleet destination set correctly.")
        else:
            print(f"[FAIL] Fleet destination mismatch: {fleet.destination}")
    else:
        print("[FAIL] MoveCommand failed to execute.")
        
    # Test Undo (Move)
    print("Testing Undo (Move)...")
    if bus.undo():
        print("[OK] Undo executed.")
        if fleet.destination is None:
            print("[OK] Fleet destination reverted.")
        else:
            print(f"[FAIL] Fleet destination NOT reverted: {fleet.destination}")
    else:
        print("[FAIL] Undo failed.")

    # 2. Test Build Command
    print("\n--- Testing BuildCommand ---")
    faction = MockFaction("Imperium", 2000)
    planet_b = MockPlanet("Planet B", "Imperium")
    
    build_cmd = BuildCommand(faction, planet_b, "Bunker", 500, engine)
    
    if bus.execute(build_cmd):
        print("[OK] BuildCommand executed.")
        if len(planet_b.construction_queue) == 1:
            print("[OK] Building added to queue.")
        else:
            print("[FAIL] Queue empty.")
            
        if faction.requisition == 1500:
            print("[OK] Cost deducted correctly.")
        else:
            print(f"[FAIL] Cost mismatch: {faction.requisition}")
    else:
        print("[FAIL] BuildCommand execution failed.")
        
    # Test Undo (Build)
    print("Testing Undo (Build)...")
    if bus.undo():
        print("[OK] Build Undo executed.")
        if len(planet_b.construction_queue) == 0:
            print("[OK] Building removed from queue.")
        else:
             print("[FAIL] Queue not empty.")
             
        if faction.requisition == 2000:
            print("[OK] Cost refunded.")
        else:
            print(f"[FAIL] Refund mismatch: {faction.requisition}")

    # 3. Test Attack Command (Intercept)
    print("\n--- Testing AttackCommand (Intercept) ---")
    target_fleet = MockFleet(2)
    target_fleet.location = "System X" # Simple string for mock
    
    attack_cmd = AttackCommand(fleet, target_fleet, engine)
    
    if bus.execute(attack_cmd):
        print("[OK] AttackCommand executed.")
        if fleet.tactical_directive == "CHARGE":
             print("[OK] Stance set to CHARGE.")
        else:
             print(f"[FAIL] Stance mismatch: {fleet.tactical_directive}")
             
        if fleet.destination == "System X":
             print("[OK] Moving to target location.")
    else:
        print("[FAIL] AttackCommand failed.")
        
    print("\nCommand Pattern Verification Complete.")

if __name__ == "__main__":
    verify_commands()
