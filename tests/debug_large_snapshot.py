
import os
import sys
import gzip
import pickle
from unittest.mock import MagicMock

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

# Mock some dependencies that might be imported during Faction/AI initialization
import sys
from unittest.mock import MagicMock

# Mock void_reckoning_bridge if it's missing
try:
    import void_reckoning_bridge
except ImportError:
    sys.modules["void_reckoning_bridge"] = MagicMock()

class SimpleManager:
    def __getstate__(self): return {}
    def __setstate__(self, state): pass

class MockObj:
    def __init__(self, id): self.id = id
    def __repr__(self): return f"MockObj({self.id})"

from src.models.faction import Faction
from src.managers.ai_manager import StrategicAI
from src.observability.snapshot_manager import SnapshotManager

class SimpleEngine:
    def __init__(self):
        self.turn_counter = 0
        self.factions = {}
        self.systems = {}
        self.fleets = []
        self.all_planets = []
        self.economy_manager = None
        self.tech_manager = None
        self.diplomacy_manager = None
        self.flux_storm_manager = None
        self.strategic_ai = None
        self.logger = MagicMock()

def test_large_snapshot():
    print("Initializing Mock Engine...")
    engine = SimpleEngine()
    engine.turn_counter = 500
    
    # Setup Logger to print to console
    def log_error(msg, *args, **kwargs): print(f"ERROR: {msg}")
    def log_info(msg, *args, **kwargs): print(f"INFO: {msg}")
    engine.logger.error = log_error
    engine.logger.info = log_info
    
    # Setup Faction with Deep History
    print("Setting up Faction with deep history...")
    faction = Faction("DeepState")
    # Manually fill learning_history
    faction.learning_history = {
        'plan_outcomes': [],
        'target_outcomes': [],
        'battle_outcomes': [],
        'personality_mutations': [],
        'intel_events': [],
        'performance_window': []
    }
    for i in range(1000): # Well over the 50 limit
        faction.learning_history['plan_outcomes'].append({
            'plan_id': f"plan_{i}",
            'goal': "DOMINATION",
            'success': True,
            'turns_taken': i % 10
        })
    engine.factions = {"DeepState": faction}
    engine.systems = {}
    engine.fleets = []
    engine.all_planets = []
    
    engine.economy_manager = SimpleManager()
    engine.tech_manager = SimpleManager()
    engine.diplomacy_manager = SimpleManager()
    engine.flux_storm_manager = SimpleManager()
    
    # Setup AI with Deep Cache
    print("Setting up AI with deep cache...")
    ai = StrategicAI(engine)
    engine.strategic_ai = ai
    
    for i in range(1000):
        ai.turn_cache[f"fleet_{i}"] = MockObj(i)
    
    ai._last_cache_turn = engine.turn_counter
    
    # Attempt Snapshot
    print("Attempting Snapshot...")
    sm = SnapshotManager(engine)
    
    # We need to make sure _capture_rng_state doesn't crash
    sm._capture_rng_state = MagicMock(return_value={})
    
    snapshot_id = sm.create_snapshot(label="STRESS_TEST")
    
    if snapshot_id:
        print(f"SUCCESS: Snapshot created: {snapshot_id}")
        
        # Verify Truncation
        print("Verifying history truncation...")
        if len(faction.learning_history['plan_outcomes']) <= 50:
            print(f"SUCCESS: History truncated to {len(faction.learning_history['plan_outcomes'])}")
        else:
            print(f"FAILURE: History NOT truncated (size: {len(faction.learning_history['plan_outcomes'])})")
            
        print("Stress test COMPLETED.")
    else:
        print("FAILURE: Snapshot creation failed.")

if __name__ == "__main__":
    test_large_snapshot()
