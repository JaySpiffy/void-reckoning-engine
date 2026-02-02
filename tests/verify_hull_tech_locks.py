
import os
import sys
import random
import json

# Setup Logic
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Mock Configuration
class MockConfig:
    DATA_DIR = os.path.join(project_root, "data")
    TECH_DIR = os.path.join(project_root, "data", "technologies")

import src.core.config as config_module
config_module.game_config = MockConfig()
config_module.TECH_DIR = MockConfig.TECH_DIR

# ------------------------------------------------------------------

from src.managers.tech_manager import TechManager
from src.models.faction import Faction
from src.factories.tech_factory import ProceduralTechGenerator
from src.services.ship_design_service import ShipDesignService

# Mock AI Manager (Lightweight)
class MockAIManager:
    def __init__(self, engine):
        self.engine = engine

class MockEngine:
    def __init__(self):
        self.factions = {}
        self.ai_manager = MockAIManager(self)
        self.tech_manager = None
        self.design_service = None # Will assign later

    def get_faction(self, name):
        return self.factions.get(name)

# ------------------------------------------------------------------

def verify_hull_locks():
    print("=== Verifying Hull Tech Locks ===")
    
    # 1. Setup
    engine = MockEngine()
    faction = Faction("TestFaction", "Blue", "Aggressive")
    engine.factions["TestFaction"] = faction
    
    # 2. Generate Tech Tree (with Hull Techs)
    tech_gen = ProceduralTechGenerator("test_universe")
    base_tree = {"techs": {}, "prerequisites": {}, "units": {}} # Empty base
    
    # Helper to load existing base or just let generator do it?
    # Generator wraps base tree. Let's make a dummy base tree.
    # The generator loads 'universal_weaponry.json' and 'hulls.json' automatically in generate_procedural_tree.
    
    print("Generating Procedural Tree...")
    generated_tree = tech_gen.generate_procedural_tree("TestFaction", base_tree)
    
    # 3. Verify Hull Techs Exist
    techs = generated_tree["techs"]
    print(f"Total Techs Generated: {len(techs)}")
    
    expected_keys = [
        "Tech_Unlock_Destroyer_Hull", 
        "Tech_Unlock_Cruiser_Hull", 
        "Tech_Unlock_Battleship_Hull", 
        "Tech_Unlock_Titan_Hull"
    ]
    
    missing = [k for k in expected_keys if k not in techs]
    if missing:
        print(f"[FAIL] Missing Expected Hull Techs: {missing}")
    else:
        print("[PASS] All Hull Unlock Techs found.")
        
    # 4. Integrate into TechManager
    # TechManager(tech_dir=..., game_config=...)
    tm = TechManager(tech_dir=MockConfig.TECH_DIR, game_config=MockConfig)
    tm.faction_tech_trees["testfaction"] = generated_tree # Lowercase key
    engine.tech_manager = tm
    
    # 5. Check Availability (Locked)
    design_service = ShipDesignService(engine.ai_manager)
    engine.design_service = design_service
    
    available_1 = design_service.get_available_hulls("TestFaction")
    print(f"Initial Hulls: {available_1}")
    
    # Expect only Corvette 
    # (Assuming Corvette has no unlock_tech, or unlocked by default? In json I removed unlock_tech for Corvette)
    if "Destroyer" in available_1:
         print("[FAIL] Destroyer available too early!")
    else:
         print("[PASS] Destroyer correctly locked.")
         
    # 6. Unlock Tech
    print("Unlocking Destroyer Tech...")
    faction.unlocked_techs.append("Tech_Unlock_Destroyer_Hull")
    
    available_2 = design_service.get_available_hulls("TestFaction")
    print(f"Hulls after Unlock: {available_2}")
    
    if "Destroyer" in available_2:
        print("[PASS] Destroyer available after unlock.")
    else:
        print("[FAIL] Destroyer still locked!")
        
    # 7. Check Drawing Weights
    print("\n=== Verifying Tech Selection Weighting ===")
    
    # Reset faction techs to blank to simulate fresh start
    faction.unlocked_techs = []
    
    # Run Monte Carlo
    num_trials = 100
    unlock_seen = 0
    generic_seen = 0
    
    # We need to make sure prereqs are met or empty so techs are available to draw
    # Many techs generated might have prereqs.
    # Unlock techs rely on "candidates" from existing techs.
    # If tree was generated with empty base, mostly only new techs exist.
    # Hull Techs rely on "candidates" (lower cost techs).
    # If no candidates found during gen, prereqs list is empty -> Available immediately.
    
    print("Running 100 Draw Trials...")
    for _ in range(num_trials):
        cards = tm.draw_research_cards(faction, num_cards=3)
        for c in cards:
            if "Unlock" in c:
                unlock_seen += 1
            else:
                generic_seen += 1
                
    print(f"Unlock Techs Seen: {unlock_seen}")
    print(f"Generic/Other Techs Seen: {generic_seen}")
    
    if unlock_seen > (generic_seen * 2): # Very rough heuristic
       print("[PASS] Unlock techs seem highly favored.")
    elif unlock_seen > generic_seen:
       print("[PASS] Unlock techs are frequent.")
    else:
       print("[WARN] Unlock techs might be rare? (Or tree populated only with them?)")
       # If tree is 99% unlocks, this test is trivial.
       
    print("\nDone.")

if __name__ == "__main__":
    verify_hull_locks()
