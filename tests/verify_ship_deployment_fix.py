
import os
import sys
import json

# Setup Logic
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.managers.tech_manager import TechManager
from src.models.faction import Faction
from src.services.ship_design_service import ShipDesignService
from src.core.game_config import GameConfig

class MockEngine:
    def __init__(self):
        self.factions = {}
        self.tech_manager = None
        self.design_service = None

    def get_faction(self, name):
        return self.factions.get(name)

def verify_fix():
    print("=== Verifying Ship Deployment Fix ===")
    
    engine = MockEngine()
    faction_name = "Algorithmic_Hierarchy"
    faction = Faction(faction_name)
    engine.factions[faction_name] = faction
    
    # Init TechManager with real registry data
    tech_dir = os.path.join(project_root, "universes", "void_reckoning", "technology")
    tm = TechManager(tech_dir=tech_dir)
    engine.tech_manager = tm
    
    class MockAIManager:
        def __init__(self, engine):
            self.engine = engine
            
    engine.ai_manager = MockAIManager(engine)
    
    # Init ShipDesignService
    ds = ShipDesignService(engine.ai_manager)
    engine.design_service = ds
    
    # 1. Test Initial State (Locked)
    available = ds.get_available_hulls(faction_name)
    print(f"Initial available hulls: {available}")
    
    if "Cruiser" in available or "Battleship" in available:
        print("[FAIL] Cruiser/Battleship available before tech!")
    else:
        print("[PASS] Capital ships correctly locked.")
        
    # 2. Test Unlock (Algorithmic Hierarchy Battleship)
    tech_id = "Tech_Algorithmic_Hierarchy_Capital Ships"
    print(f"\nUnlocking {tech_id} for {faction_name}...")
    faction.unlocked_techs.append(tech_id)
    
    available = ds.get_available_hulls(faction_name)
    print(f"Available hulls: {available}")
    
    if "Battleship" in available:
        print("[PASS] Battleship unlocked correctly (Fuzzy match AI Battleships)!")
    else:
        print("[FAIL] Battleship still locked.")

    # 3. Test Aurelian Hegemony Cruisers
    faction_name_2 = "Aurelian_Hegemony"
    faction_2 = Faction(faction_name_2)
    engine.factions[faction_name_2] = faction_2
    
    # In registry: Tech_Aurelian_Hegemony_Mega Construction unlocks "Cruisers"
    tech_id_2 = "Tech_Aurelian_Hegemony_Mega Construction"
    print(f"\nUnlocking {tech_id_2} for {faction_name_2}...")
    faction_2.unlocked_techs.append(tech_id_2)
    
    available_2 = ds.get_available_hulls(faction_name_2)
    print(f"Available hulls: {available_2}")
    
    if "Cruiser" in available_2:
        print("[PASS] Cruiser unlocked correctly (Plural match)!")
    else:
        print("[FAIL] Cruiser still locked.")

if __name__ == "__main__":
    verify_fix()
