from src.models.starbase import Starbase
from src.models.unit import Component
from src.services.ship_design_service import ShipDesignService

class MockEngine:
    def __init__(self):
        self.factions = {}
        self.turn_counter = 1
    def get_faction(self, name):
        return self.factions.get(name)

class MockFaction:
    def __init__(self, name):
        self.name = name
        self.unlocked_techs = ["Void Shields"]
        self.weapon_registry = {
            "flux_lance": {"Name": "Flux Lance", "Range": 60, "S": 10, "AP": 4, "D": 5, "cost": 100}
        }
        self.design_preference = "BALANCED"

def test_starbase_ai_design():
    engine = MockEngine()
    f_name = "Templars_of_the_Flux"
    engine.factions[f_name] = MockFaction(f_name)
    
    ai_manager = type('MockAI', (), {'engine': engine})
    designer = ShipDesignService(ai_manager)
    
    print("\n--- Testing AI Starbase Design ---")
    design = designer.generate_starbase_design(f_name, tier=3)
    print(f"Generated Design: {design['name']}")
    print(f"Cost: {design['cost']}")
    
    # Create Starbase with design
    class MockSystem:
        def __init__(self): self.name = "Test System"; self.planets = []; self.starbases = []
        def get_primary_node(self): return None
        
    sb = Starbase("Templar Fortress", f_name, MockSystem(), tier=3, design_data=design)
    
    print("Components in AI-Designed Starbase:")
    for c in sb.components:
        # Robust name/type check for mixed component model
        c_name = getattr(c, 'name', type(c).__name__)
        c_type = getattr(c, 'type', 'Native')
        print(f"  - {c_name} ({c_type})")

def test_starbase_buffs():
    system = type('MockSystem', (), {'name': "Test System", 'planets': [], 'starbases': [], 'get_primary_node': lambda: None})()
    f_name = "Templars_of_the_Flux"
    
    print("\n--- Tier 5 Starbase Buff Verification ---")
    sb5 = Starbase("T5 Fortress", f_name, system, tier=5)
    print(f"HP: {sb5.max_hp} (Expected: 15000)")
    print(f"Shield: {sb5.shield_max} (Expected: 10000)")
    print(f"Armor: {sb5.armor} (Expected: 75)")
    
    print("Components:")
    for c in sb5.components:
        c_name = getattr(c, 'name', type(c).__name__)
        c_type = getattr(c, 'type', 'Native')
        print(f"  - {c_name} ({c_type})")

if __name__ == "__main__":
    test_starbase_buffs()
    test_starbase_ai_design()

