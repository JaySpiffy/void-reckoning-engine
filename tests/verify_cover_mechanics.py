import sys
import os
import math

# Ensure src path is available
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Correct import based on grep results
from src.combat.tactical_grid import TacticalGrid
from src.models.unit import Unit

def test_cover_mechanics():
    print(">>> Verifying Cover Mechanics...")
    
    # 1. Setup Grid
    grid = TacticalGrid(width=10, height=10, map_type="Ground")
    
    # 2. Define Locations
    loc_open = (5, 5)
    loc_light = (2, 2)
    loc_heavy = (8, 8)
    
    # Manually Inject Terrain
    # Open
    if loc_open in grid.terrain_map: del grid.terrain_map[loc_open]
    
    # Light
    grid.terrain_map[loc_light] = {"type": "Light", "hp": 50, "max_hp": 50}
    
    # Heavy
    grid.terrain_map[loc_heavy] = {"type": "Heavy", "hp": 100, "max_hp": 100}
    
    print("Terrain configured via TacticalGrid.")
    
    # 3. Define Mock Logic matching RealTimeManager
    def calculate_mitigation(target_loc, target_facing=0, attacker_loc=(0,0)):
        # Replicating RealTimeManager logic (lines 182-202)
        # Simplified for Cover testing
        
        # Base Save
        t_armor = 40 # 4+ equivalent?
        sv = 7.0 - (t_armor/10.0)
        # sv = 3.0
        
        # Cover Check
        cover = grid.get_cover_at(target_loc[0], target_loc[1])
        
        # Calculate flanking
        # Mocking bearing logic
        # If target faces Attacker (0 relative), then NOT flanked.
        # Let's assume attacker is at (0,0).
        # We need a mock target unit to use grid.get_relative_bearing
        class MockUnit:
            def __init__(self, x, y, f):
                self.grid_x = x
                self.grid_y = y
                self.facing = f
                self.abilities = {}
                self.armor = 40
        
        attacker = MockUnit(attacker_loc[0], attacker_loc[1], 0)
        target = MockUnit(target_loc[0], target_loc[1], target_facing)
        
        if cover != "None":
            bearing = grid.get_relative_bearing(target, attacker) 
            is_flanked = not (bearing <= 45 or bearing >= 315)
            print(f"DEBUG: Loc {target_loc} Cover: {cover} Bearing: {bearing:.1f} Flanked: {is_flanked}")
            
            if not is_flanked:
                if cover == "Heavy": sv -= 0.5
                elif cover == "Light": sv -= 0.25
                
        # Calculate Mitigation %
        # pass_chance = (7.0 - sv)/6.0
        pass_chance = max(0.0, min(1.0, (7.0 - sv)/6.0))
        return pass_chance

    # 4. Scenario A: Head-on Fire
    # For each, place attacker directly "North" (lower Y index is Up in standard grid usually, wait grid is Y grows Down)
    # 0,0 is Top-Left. 
    # If Target is at (2,2), facing 270 (North/Up). Attacker at (2,0).
    # dx=0, dy=-2. atan2(-2,0) = -90 -> +90 = 0 deg bearing? 
    # Wait, my logic for bearing_geo: (angle + 90) % 360.
    # atan2(-2,0) is -90. (-90+90)=0. So (2,0) is "0 degrees" absolute?
    # No, usually 0 is East. Up is 270? 
    # Let's trust the log: 
    # If Target facing 270 wants "Front", it wants absolute bearing 270.
    # If Attacker at (2,0) relative to (2,2) is bearing 0, that's North?
    # Let's adjust Attacker to be (5,0) for (5,5), (2,0) for (2,2), etc. 
    # AND verify 270 facing works.
    
    # Update mock to accept attacker loc per call isn't enough, we need to pass the "Ideal" attacker loc
    
    # Open
    mit_open = calculate_mitigation(loc_open, target_facing=0, attacker_loc=(loc_open[0], 0))
    
    # Light
    mit_light = calculate_mitigation(loc_light, target_facing=0, attacker_loc=(loc_light[0], 0))
    
    # Heavy
    mit_heavy = calculate_mitigation(loc_heavy, target_facing=0, attacker_loc=(loc_heavy[0], 0))
    
    print(f"Mitigation (Open): {mit_open:.3f}")
    print(f"Mitigation (Light): {mit_light:.3f}")
    print(f"Mitigation (Heavy): {mit_heavy:.3f}")
    
    if mit_light <= mit_open:
        print("FAIL: Light cover calculation did not increase mitigation.")
        return False

    if mit_heavy <= mit_light:
        print("FAIL: Heavy cover did not provide superior mitigation.")
        return False
        
    # 5. Scenario B: Flanking Fire
    # Attacker stays Top. Target faces Right (East). Bearing to attacker is Left (Side/Rear).
    mit_flanked = calculate_mitigation(loc_heavy, target_facing=90, attacker_loc=(loc_heavy[0], 0))
    print(f"Mitigation (Heavy, Flanked): {mit_flanked:.3f}")
    
    if abs(mit_flanked - mit_open) > 0.001:
        print(f"FAIL: Flanking should negate cover. Got {mit_flanked}, expected open {mit_open}")
        return False
        
    print("PASS: Flanking correctly negates cover bonus.")
    
    print("\n>>> ALL TESTS PASSED <<<")
    return True

if __name__ == "__main__":
    if test_cover_mechanics():
        sys.exit(0)
    else:
        sys.exit(1)
