
import os
import sys
import json
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.models.unit import Unit, Component
from src.combat.combat_state import CombatState
from src.combat.tactical_engine import resolve_real_time_combat

def test_logging():
    print("Initializing Mock Battle...")
    
    u1 = Unit(name="Attacker", ma=50, md=50, hp=100, armor=10, damage=20, abilities={}, faction="Faction A")
    u1.unit_class = "Infantry"
    u1.grid_x = 0
    u1.grid_y = 0
    u1.components = [Component("Hull", 100, "Hull")]
    u1.tactical_directive = "STANDARD"

    u2 = Unit(name="Defender", ma=50, md=50, hp=50, armor=0, damage=5, abilities={}, faction="Faction B")
    u2.unit_class = "Infantry"
    u2.grid_x = 0
    u2.grid_y = 0
    u2.components = [Component("Hull", 50, "Hull")]
    u2.tactical_directive = "STANDARD"

    armies = {
        "Faction A": [u1],
        "Faction B": [u2]
    }
    
    # Mock Rules
    class MockRules:
        def register_phases(self): return []
        def get_phase_order(self): return []
        
    log_file = "test_combat_log.json"
    if os.path.exists(log_file): os.remove(log_file)
    
    print("Resolving Real-Time Combat...")
    winner, survivors, sim_time, stats = resolve_real_time_combat(
        armies,
        silent=False,
        max_time=10.0, # Short time limit
        json_log_file=log_file,
        universe_rules=MockRules()
    )
    
    print(f"Winner: {winner}, Time: {sim_time}s")
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            data = json.load(f)
            events = data.get("events", [])
            print(f"Events Logged: {len(events)}")
            for e in events:
                print(f" - [{e['timestamp']}s] {e['type']}: {e['description']}")
                
            if len(events) == 0:
                print("FAIL: No events logged despite combat resolving.")
            else:
                print("PASS: Events logged.")
    else:
        print("FAIL: Log file not created.")

if __name__ == "__main__":
    test_logging()
