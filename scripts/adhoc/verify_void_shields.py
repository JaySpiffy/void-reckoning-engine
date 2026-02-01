
import os
import sys
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.core.universe_data import UniverseDataManager
from src.services.ship_design_service import ShipDesignService
from src.managers.faction_manager import FactionManager
from src.models.faction import Faction
from src.models.unit import Ship


def verify_void_shields():
    print("Initalizing verification...")
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data("eternal_crusade")
    
    # Mock Engine
    class MockEngine:
        def __init__(self):
            self.factions = {}
            self.logger = None
    
    class MockAI:
        def __init__(self, engine):
            self.engine = engine

    engine = MockEngine()
    ai_mgr = MockAI(engine)

    # 1. Setup Faction
    f_name = "Iron_Vanguard"
    faction = Faction(f_name)
    engine.factions[f_name] = faction
    
    # 2. Unlock Tech
    tech_id = "Tech_Iron_Vanguard_Planetary Shielding"
    faction.unlocked_techs.append(tech_id)
    print(f"Unlocked {tech_id}")
    
    # 3. Test Design Service
    service = ShipDesignService(ai_mgr)
    defense = service._pick_defense(f_name, "Brawler")
    
    print(f"\n[Test 1] Pick Defense Result: {defense}")
    if defense["name"] == "Void Shield Generator" and defense["type"] == "Shield":
        print("PASS: ShipDesignService picked Void Shields correctly.")
    else:
        print("FAIL: ShipDesignService did NOT pick Void Shields.")
        return

    # 4. Test Unit Component Generation
    print("\n[Test 2] Unit Component Generation")
    
    # Mock Design Data (similar to what create_design produces)
    design = {
        "name": "Test Ship",
        "components": [
            {"slot": "defense", "component": "Void Shield Generator", "type": "Shield", "stats": {"shield": 200}},
            {"slot": "weapon", "component": "Macro-Cannon", "type": "Weapon", "stats": {"damage": 10}}
        ],
        "base_stats": {"hp": 1000, "shield": 200, "armor": 50, "ma": 60, "md": 40, "damage": 10}
    }
    
    ship = Ship(
        name="Test Void Ship",
        faction=f_name,
        hp=design["base_stats"]["hp"],
        shield=design["base_stats"]["shield"],
        components_data=design["components"],
        # dummy args
        ma=60, md=40, armor=50, damage=10, abilities={}
    )
    
    print(f"Initialized Ship: {ship.name} (Shield Max: {ship.shield_max})")
    print("Components:")
    has_void = False
    has_generic = False
    
    for c in ship.components:
        print(f" - {c.name} (Type: {c.type}, HP: {c.max_hp})")
        if c.name == "Void Shield Generator": has_void = True
        if c.name == "Shield Generator": has_generic = True
        
    if has_void and not has_generic:
        print("PASS: Only Void Shield Generator is present.")
    elif has_void and has_generic:
        print("FAIL: Duplicate Shield Generators found!")
    else:
        print("FAIL: Void Shield Generator missing!")

if __name__ == "__main__":
    verify_void_shields()
