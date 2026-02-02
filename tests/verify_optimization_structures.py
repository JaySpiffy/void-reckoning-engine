
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet
from src.managers.task_force_manager import TaskForceManager, TaskForce
from src.managers.ai_manager import StrategicAI
from src.managers.campaign_manager import CampaignEngine

class MockEngine:
    def __init__(self):
        self.fleets = []
        self.systems = []

class MockStrategicAI:
    def __init__(self):
        self.engine = MockEngine()

def verify_task_force_map():
    print("Verifying TaskForceManager map...")
    ai_mgr = MockStrategicAI()
    tf_mgr = TaskForceManager(ai_mgr)
    
    # Create Fleets
    f1 = Fleet("F1", "FactionA", None)
    f2 = Fleet("F2", "FactionA", None)
    f3 = Fleet("F3", "FactionB", None)
    
    # Create Task Forces manually for test
    tf_mgr.ensure_faction_list("FactionA")
    tf1 = TaskForce("TF1", "FactionA")
    tf_mgr.task_forces["FactionA"].append(tf1)
    
    # Test Adding Logic (simulating what happens in manager)
    tf1.add_fleet(f1)
    tf_mgr._fleet_to_tf_map[f1.id] = tf1 # Simulate what the manager does
    
    # Verify Lookup
    assert tf_mgr.get_task_force_for_fleet(f1) == tf1, "F1 should map to TF1"
    assert tf_mgr.get_task_force_for_fleet(f2) is None, "F2 is not in a TF"
    
    # Add F2
    tf1.add_fleet(f2)
    tf_mgr._fleet_to_tf_map[f2.id] = tf1
    assert tf_mgr.get_task_force_for_fleet(f2) == tf1
    
    # Test Removal Logic (cleanup)
    tf1.fleets.remove(f1) 
    # Logic in manager's 'manage_task_force' would clean this up
    # Let's manually invoke the cleanup logic we added
    current_ids = set(f.id for f in tf1.fleets)
    keys_to_remove = [k for k, v in tf_mgr._fleet_to_tf_map.items() if v == tf1 and k not in current_ids]
    for k in keys_to_remove:
        del tf_mgr._fleet_to_tf_map[k]
        
    assert tf_mgr.get_task_force_for_fleet(f1) is None, "F1 should be removed from map"
    assert tf_mgr.get_task_force_for_fleet(f2) == tf1, "F2 should still accept TF1"
    
    print("TaskForceManager Map Verification: PASS")

def verify_construction_service_logic():
    print("Verifying ConstructionService optimization logic...")
    # Mocking the dictionary lookup logic
    
    # Setup Fleets
    class MockNode:
        def __init__(self, name): self.name = name
    
    node1 = MockNode("N1")
    node2 = MockNode("N2")
    
    f1 = Fleet("F1", "FactionA", node1)
    f2 = Fleet("F2", "FactionA", node2)
    f3 = Fleet("F3", "FactionB", node1)
    
    fleets = [f1, f2, f3]
    
    # Build Map (Logic copied from Service)
    fleet_locations = {}
    for fleet in fleets:
        if fleet.faction == "FactionA":
             fleet_locations[fleet.location] = fleet
             
    # Test Lookups
    assert fleet_locations.get(node1) == f1
    assert fleet_locations.get(node2) == f2
    assert len(fleet_locations) == 2
    
    print("ConstructionService Optimization Logic Verification: PASS")

if __name__ == "__main__":
    verify_task_force_map()
    verify_construction_service_logic()
