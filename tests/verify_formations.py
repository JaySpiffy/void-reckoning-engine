
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet
from src.models.unit import Ship
from src.combat.combat_state import CombatState
from src.ai.formation_designer import FormationDesigner

def test_formation_system():
    print("=== Testing Dynamic AI Formations ===")
    
    # 1. Setup Fleet
    print("1. Creating Fleet...")
    fleet = Fleet("F-Test", "Hegemony", None)
    
    # Add units
    for i in range(5):
        # Ship(name, faction, **kwargs)
        u = Ship(f"Ship-{i}", "Hegemony", hp=100, ma=10, md=10, damage=10, armor=10)
        u.id = f"unit-{i}"
        u.ship_class = "Escort" if i < 3 else "Cruiser"
        fleet.units.append(u)
        u.set_fleet(fleet) # Manual link
        
    # 2. Design Formation
    print("2. Running FormationDesigner...")
    designer = FormationDesigner()
    offsets = designer.design_formation(fleet)
    
    if not offsets:
        print("FAIL: No offsets generated.")
        return
        
    print(f"   Generated {len(offsets)} offsets.")
    print(f"   Formation Settings: {fleet.formation_settings.get('template')}")
    print(f"   Groups: {fleet.formation_settings.get('groups').keys()}")
    
    # 3. Verify Persistence
    print("3. Verifying Persistence...")
    if not fleet.saved_formation:
        print("FAIL: saved_formation not set on fleet.")
        return
        
    # 4. Mock Combat Init
    print("4. Testing Battle Placement...")
    # We mock a CombatState initialization
    
    # We need to manually trigger the placement logic logic normally found in CombatState
    # But since we can't easily instantiate a full CombatState without args, 
    # Let's just manually verify the logic we inserted.
    
    # Actually, we can instantiate CombatState with minimal mocks
    armies = {"Hegemony": fleet.units}
    
    # Mock mocks
    try:
        state = CombatState(armies, {}, {}, universe_rules=None)
        state.mechanics_engine = None # avoid issues
        # We need to mock grid_manager to capture placement calls? 
        # Or just check unit.grid_x / grid_y after initialize_battle?
        
        # initialize_battle calls grid_manager.
        # Let's mock grid_manager
        class MockGridManager:
            def __init__(self, w, h, map_type): 
                self.grid = None
            def place_unit(self, u, x, y):
                pass
                
        # Patch internals
        # We can't easily patch inside info unless we subclass or just run it and hope dependencies verify.
        # initialize_battle requires 'config' sometimes?
        # Let's run it.
        
        # Debug Fleet Ref
        print(f"DEBUG: Checking fleet refs for {len(fleet.units)} units...")
        for u in fleet.units:
            f = u.fleet
            if f is None:
                print(f"ERROR: Unit {u.name} has no fleet ref!")
            elif not f.saved_formation:
                print(f"ERROR: Unit {u.name} fleet has no saved_formation!")
            else:
                 pass # Good
                 
        state.initialize_battle()
        
        # Check Unit Positions
        print("   Checking Unit Positions...")
        
        # Get actual grid size
        grid_w = state.grid_manager.width if hasattr(state, 'grid_manager') and state.grid_manager else 100
        grid_h = state.grid_manager.height if hasattr(state, 'grid_manager') and state.grid_manager else 100
        
        # Recalculate Center based on actual grid
        # Faction B logic
        center_x = grid_w * 0.75 
        center_y = grid_h / 2
        
        for u in fleet.units:
            uid = str(u.id)
            if uid in offsets:
                ox, oy = offsets[uid]
                # B logic: x = cx + (-ox)
                expected_x = int(center_x + (-ox))
                expected_y = int(center_y + oy)
                
                # Allow clamping
                expected_x = max(0, min(grid_w - 1, expected_x))
                expected_y = max(0, min(grid_h - 1, expected_y))
                
                if u.grid_x == expected_x and u.grid_y == expected_y:
                    print(f"   [PASS] {u.name} at ({u.grid_x}, {u.grid_y}) matches formation.")
                else:
                    print(f"   [FAIL] {u.name} at ({u.grid_x}, {u.grid_y}). Expected ({expected_x}, {expected_y}). Offset: {ox},{oy}")
            else:
                print(f"   [WARN] {u.name} has no offset.")
                
    except Exception as e:
        print(f"FAIL: CombatState init crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_formation_system()
