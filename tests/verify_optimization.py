
import sys
import os
sys.path.append(os.getcwd())

from src.managers.diplomacy_manager import DiplomacyManager
from src.managers.battle_manager import BattleManager
from src.managers.campaign_manager import CampaignEngine

class MockFaction:
    def __init__(self, name):
        self.name = name
        self.stats = {"total_power": 100}
        self.requisition = 1000
        self.unlocked_techs = []
        self.quirks = {}

class MockEngine:
    def __init__(self):
        self.factions = {
             "F1": MockFaction("F1"), 
             "F2": MockFaction("F2"),
             "F3": MockFaction("F3")
        }
        self.turn_counter = 1
        self.logger = None
        self.telemetry = None
        self.game_config = {}
        self.fleets = []
        
    def get_faction(self, name):
        return self.factions.get(name)

    def get_all_fleets(self):
        return self.fleets
        
    def get_all_planets(self):
        return []

from unittest.mock import MagicMock, patch

def verify_diplomacy_cache():
    print("Verifying Diplomacy Cache...")
    engine = MockEngine()
    
    # Patch dependencies
    with patch('src.managers.diplomacy_manager.RelationService') as MockRel, \
         patch('src.managers.diplomacy_manager.TreatyCoordinator') as MockTC, \
         patch('src.managers.diplomacy_manager.DiplomaticActionHandler') as MockDAH:
         
        # Setup Mock Treaty Coordinator behavior
        mock_tc_instance = MockTC.return_value
        mock_tc_instance.get_treaty.return_value = "Peace" # Default
        mock_tc_instance.treaties = {}
        
        dm = DiplomacyManager(["F1", "F2", "F3"], engine)
        
        # 1. Test Initial Get (Cache Miss)
        t1 = dm.get_treaty("F1", "F2")
        print(f"Initial Treaty F1-F2: {t1}")
        assert t1 == "Peace"
        mock_tc_instance.get_treaty.assert_called_with("F1", "F2")
        
        # 2. Test Cache Hit (Should match)
        # Manually inject into cache to verify we don't call coordinator again
        dm._war_cache[tuple(sorted(("F1", "F2")))] = "War" 
        
        # Reset mock to ensure we don't see previous calls
        mock_tc_instance.get_treaty.reset_mock()
        
        t2 = dm.get_treaty("F1", "F2")
        if t2 == "War":
            print("SUCCESS: Cache hit returned forced value.")
        else:
            print(f"FAILURE: Cache hit returned {t2} instead of War.")
        
        # Check that coordinator was NOT called
        try:
             mock_tc_instance.get_treaty.assert_not_called()
             print("SUCCESS: Coordinator was not called (Cache Hit).")
        except AssertionError:
             print("FAILURE: Coordinator WAS called despite cache hit.")
            
        # 3. Test Set Treaty (Should invalidate)
        dm._set_treaty("F1", "F2", "Alliance")
        
        if tuple(sorted(("F1", "F2"))) not in dm._war_cache:
             print("SUCCESS: Cache invalidated after set_treaty.")
        else:
             print("FAILURE: Cache key remains after invalidation.")
        
        # 4. Verify Coordinator set_treaty called
        mock_tc_instance.set_treaty.assert_called_with("F1", "F2", "Alliance")

def verify_fleet_index():
    print("\nVerifying Fleet Index...")
    engine = MockEngine()
    
    # Mock Fleet
    class MockFleet:
        def __init__(self, fid, loc):
            self.id = fid
            self.location = loc
            self.is_destroyed = False
    
    f1 = MockFleet("fleet_1", "loc_A")
    f2 = MockFleet("fleet_2", "loc_B")
    engine.fleets = [f1, f2]
    
    # We might need to mock Context or attributes on BattleManager if it does heavy init
    # But checking source, BattleManager init is mostly safe except maybe InvasionManager?
    # InvasionManager might need engine.metrics/telemetry
    
    with patch('src.managers.battle_manager.InvasionManager'), \
         patch('src.managers.battle_manager.RetreatHandler'):
        
        bm = BattleManager(context=engine)
        bm._update_presence_indices()
        
        if "fleet_1" in bm._fleet_index:
            print("SUCCESS: Fleet 1 indexed.")
        else:
            print("FAILURE: Fleet 1 not found in index.")
            
        if bm._fleet_index.get("fleet_2") == f2:
            print("SUCCESS: Fleet 2 retrieval correct.")
        
if __name__ == "__main__":
    verify_diplomacy_cache()
    verify_fleet_index()
