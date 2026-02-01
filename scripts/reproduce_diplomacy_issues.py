import sys
import os
from unittest.mock import Mock, patch

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.managers.diplomacy_manager import DiplomacyManager
from src.managers.battle_manager import BattleManager
from src.models.fleet import Fleet
from src.models.unit import Unit

class MockUnit:
    def __init__(self, faction):
        self.faction = faction
        self.name = f"Unit_{faction}"
        self.grid_x = 0
        self.grid_y = 0
        self.base_hp = 100
        self.current_hp = 100
        self.components = []
        self.evasion_rating = 0
    def is_alive(self):
        return self.current_hp > 0

class MockLocation:
    def __init__(self, name, owner="Neutral"):
        self.name = name
        self.id = name
        self.owner = owner
        self.id = name
        self.owner = owner
        self.type = "Planet"
        self.edges = []
        self.metadata = {}

    def is_portal(self):
        return False

class MockEdge:
    def __init__(self, target, distance=1):
        self.target = target
        self.distance = distance
    
    def is_traversable(self):
        return True

class MockEngine:
    def __init__(self, factions):
        self.factions = {}
        for f in factions:
            m = Mock()
            m.evasion_rating = 0
            m.name = f
            m.stats = {"turn_diplomacy_actions": 0}
            self.factions[f] = m
        self.fleets = []
        self.all_planets = []
        self.turn_counter = 1
        self.coalitions = {}
        
        # [FIX] Robust Logging
        self.logger = Mock()
        self.logger.combat = lambda x: print(f"  [LOG] {x}")
        self.logger.campaign = lambda x: print(f"  [LOG] {x}")
        
        self.telemetry = Mock()
        self.report_organizer = Mock()
        self.report_organizer.run_path = "test_reports"
        self.faction_reporter = Mock()
        self.faction_manager = Mock()
        self.faction_manager.get_faction_names = lambda: factions
        self.strategic_ai = Mock()
        self.strategic_ai.predict_enemy_threats.return_value = []
        self.strategic_ai.coalition_builder.coalitions = {}
        self.economy_manager = Mock()
        self.economy_manager.get_faction_economic_report.return_value = {"margin": 1.5, "requisition": 5000}
        self.mechanics_engine = Mock()
        
        # [FIX] Use correctly named attribute
        self.diplomacy = DiplomacyManager(factions, self)

    def get_faction(self, name):
        return self.factions.get(name)
    
    def get_all_fleets(self):
        return self.fleets
    
    def get_all_armies(self):
        return []
    
    def get_all_planets(self):
        return self.all_planets
    
    def get_all_factions(self):
        return list(self.factions.values())

def test_peaceful_coexistence():
    """Verify that factions at Peace can share a location."""
    print("\n--- Testing Peaceful Coexistence ---")
    factions = ["Solar_Hegemony", "Ancient_Guardians"]
    engine = MockEngine(factions)
    battle_manager = BattleManager(engine)
    
    loc = MockLocation("Thoarnax 9", owner="Ancient_Guardians")
    
    # Create peaceful units
    f1 = Fleet("F1", factions[0], loc)
    f1.units = [MockUnit(factions[0])]
    f1.evasion_rating = 0
    f2 = Fleet("F2", factions[1], loc)
    f2.units = [MockUnit(factions[1])]
    f2.evasion_rating = 0
    
    engine.fleets = [f1, f2]
    
    # Ensure they are at Peace (default)
    print(f"Treaty: {engine.diplomacy.get_treaty(factions[0], factions[1])}")
    
    # Try to resolve battles
    # We pass fleets_present etc normally
    battle_manager.resolve_battles_at(loc, [f1, f2], [], loc.owner)
    
    if len(battle_manager.active_battles) == 0:
        print("SUCCESS: No battle triggered for peaceful factions.")
    else:
        print("FAILURE: Battle triggered for peaceful factions!")
        sys.exit(1)

def test_combat_at_war():
    """Verify that factions at War DO fight."""
    print("\n--- Testing Combat at War ---")
    factions = ["Solar_Hegemony", "Ancient_Guardians"]
    engine = MockEngine(factions)
    battle_manager = BattleManager(engine)
    
    loc = MockLocation("Thoarnax 9", owner="Ancient_Guardians")
    
    # Create units
    f1 = Fleet("F1", factions[0], loc)
    f1.units = [MockUnit(factions[0])]
    f1.evasion_rating = 0
    f2 = Fleet("F2", factions[1], loc)
    f2.units = [MockUnit(factions[1])]
    f2.evasion_rating = 0
    
    engine.fleets = [f1, f2]
    
    # Declare War
    engine.diplomacy.relation_service.modify_relation(factions[0], factions[1], -100)
    engine.diplomacy.process_turn() # Should trigger war check
    
    print(f"Treaty: {engine.diplomacy.get_treaty(factions[0], factions[1])}")
    
    # Try to resolve battles
    with patch.object(battle_manager, '_initialize_new_battle') as mock_init:
        battle_manager.resolve_battles_at(loc, [f1, f2], [], loc.owner)
        if mock_init.called:
            print("SUCCESS: Battle triggered for factions at War.")
        else:
            print("FAILURE: Battle NOT triggered for factions at War!")
            sys.exit(1)

def test_fleet_interception_at_peace():
    """Verify that fleets don't intercept each other at Peace."""
    print("\n--- Testing Interception at Peace ---")
    factions = ["Solar_Hegemony", "Ancient_Guardians"]
    engine = MockEngine(factions)
    
    # Setup: Mover arriving at 'Thoarnax 9' where Guard is.
    loc = MockLocation("Thoarnax 9") # Destination
    start_loc = MockLocation("Start") # Origin
    # Link
    start_loc.edges = [MockEdge(loc)]
    
    # Guard is at Destination
    f_guard = Fleet("Guard", factions[1], loc)
    f_guard.units = [MockUnit(factions[1])]
    engine.fleets = [f_guard]
    
    # Mover is arriving at Destination
    f_mover = Fleet("Mover", factions[0], start_loc) 
    f_mover.location = start_loc
    f_mover.destination = loc
    f_mover.route = [loc] # Must have route
    f_mover.travel_progress = 1 
    f_mover.units = [MockUnit(factions[0])]
    
    # Ensure guard and mover are in engine fleets? 
    # Mover calls update_movement, checks engine.fleets for hostiles.
    # Guard needs to be in engine.fleets.
    # Mover is passed 'engine'.
    
    print(f"DEBUG: Simulating arrival at {loc.name}. Guard faction: {factions[1]}")
    
    # Try to move
    # update_movement(engine)
    result = f_mover.update_movement(engine)
    
    if result != "INTERCEPTED":
        print("SUCCESS: Fleet was NOT intercepted by peaceful faction.")
    else:
        print("FAILURE: Fleet was intercepted by peaceful faction!")
        sys.exit(1)

def test_fleet_interception_at_war():
    """Verify that fleets DO intercept each other at War."""
    print("\n--- Testing Interception at War ---")
    factions = ["Solar_Hegemony", "Ancient_Guardians"]
    engine = MockEngine(factions)
    
    loc = MockLocation("Thoarnax 9")
    start_loc = MockLocation("Start")
    # Link
    start_loc.edges = [MockEdge(loc)]
    
    # Guard is at Destination
    f_guard = Fleet("Guard", factions[1], loc)
    f_guard.units = [MockUnit(factions[1])]
    engine.fleets = [f_guard] # Guard must be in engine fleets
    
    # Mover is arriving at Destination
    f_mover = Fleet("Mover", factions[0], start_loc)
    f_mover.location = start_loc
    f_mover.destination = loc
    f_mover.route = [loc]
    f_mover.travel_progress = 1
    f_mover.units = [MockUnit(factions[0])]
    
    # Declare War
    engine.diplomacy.relation_service.modify_relation(factions[0], factions[1], -100)
    engine.diplomacy.process_turn()
    
    print(f"DEBUG: Treaty after decl: {engine.diplomacy.get_treaty(factions[0], factions[1])}")
    
    # Try to move
    result = f_mover.update_movement(engine)
    
    if result == "INTERCEPTED":
        print("SUCCESS: Fleet WAS intercepted by enemy faction!")
    else:
        print(f"FAILURE: Fleet was NOT intercepted! Result: {result}")
        if result == "MOVING":
             print("Reason: Fleet continued moving without stopping.")
        sys.exit(1)

if __name__ == "__main__":
    test_peaceful_coexistence()
    test_combat_at_war()
    test_fleet_interception_at_peace()
    test_fleet_interception_at_war()
    print("\nALL DIPLOMACY TESTS PASSED!")
