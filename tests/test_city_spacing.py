import pytest
from unittest.mock import MagicMock, patch
from src.services.construction_service import ConstructionService
from src.models.planet import Planet
from src.models.hex_node import HexNode
from src.core.hex_lib import Hex

from src.core.universe_data import UniverseDataManager

class MockFaction:
    def __init__(self):
        self.name = "TestFaction"
        self.requisition = 10000
        self.tech_tree = MagicMock()
        self.tech_tree.unlocked_techs = set()
        self.modifiers = {}
        
    def can_afford(self, cost):
        return self.requisition >= cost
        
    def get_modifier(self, name, default=1.0):
        return default
        
    def has_tech(self, tech):
        return True

    def construct_building(self, planet, building_id):
        # Mock success and append to queue
        planet.construction_queue.append({"building_id": building_id, "turns_left": 5})
        return True
        
    def deduct_cost(self, cost):
        self.requisition -= cost
        
    def track_construction(self, cost):
        pass

@pytest.fixture
def service():
    # Mock UniverseDataManager for Planet creation
    with patch("src.models.planet.UniverseDataManager") as MockUDM:
        mock_instance = MagicMock()
        mock_instance.get_planet_classes.return_value = {
            "Terran": {
                "req_mod": 1.0, 
                "def_mod": 10, 
                "slots": 10,
                "desc": "A habitable world."
            }
        }
        MockUDM.get_instance.return_value = mock_instance
        
        engine = MagicMock()
        engine.telemetry = MagicMock()
        
        # Mock Economy Manager
        engine.economy_manager = MagicMock()
        engine.economy_manager.faction_econ_cache = {
            "TestFaction": {"income": 1000, "total_upkeep": 500}
        }
        
        service = ConstructionService(engine)
        yield service

def test_city_spacing_rule_valid(service):
    """Test that building is allowed when distance >= 4"""
    # Setup Planet with 2 nodes far apart
    p = Planet("TestPlanet", "System", "TestFaction")
    p.building_slots = 5
    
    # Node A: (0,0) - Has a building (City). FULL.
    node_a = HexNode("node_a", 0, 0, "TestPlanet")
    node_a.buildings = ["CityCenter"]
    node_a.building_slots = 1 # Full, forcing it to look elsewhere
    
    # Node B: (0,4) - Empty. Distance 4. Should be VALID.
    node_b = HexNode("node_b", 0, 4, "TestPlanet")
    node_b.buildings = []
    node_b.building_slots = 5
    
    p.provinces = [node_a, node_b]
    
    faction = MockFaction()
    
    # Call process logic
    # We expect cost > 0, meaning it found a valid target (node_b)
    # Note: We need to mock get_building_database to return valid candidates
    with patch("src.services.construction_service.get_building_database") as mock_db:
        mock_db.return_value = {
            "TestBuilding": {
                "id": "TestBuilding", "cost": 100, "tier": 1, 
                "faction": "TestFaction", "effects": {"description": "test"}
            }
        }
        
        # We also need to patch get_stream to pick predictable results
        with patch("src.services.construction_service.get_stream") as mock_stream:
            mock_stream.return_value.choice.return_value = "TestBuilding"
            
            cost, _ = service._process_planet_construction(p, "TestFaction", faction, 1000, "EXPANSION")
            
            # Assert checks
            assert cost > 0
            # Ensure it picked node_b (checked by side effect or inspecting queue)
            # Since construct_building is mocked on faction, we check if queue was appended
            # The service appends to queue if node_id logic aligns
            assert p.construction_queue[-1]["node_id"] == "node_b"

def test_city_spacing_rule_invalid(service):
    """Test that building is BLOCKED when distance < 4"""
    p = Planet("TestPlanet", "System", "TestFaction")
    
    # Node A: (0,0) - City. FULL.
    node_a = HexNode("node_a", 0, 0, "TestPlanet")
    node_a.buildings = ["CityCenter"]
    node_a.building_slots = 1 # Full, force search for new location
    
    # Node C: (0,3) - Empty. Distance 3. Should be INVALID.
    node_c = HexNode("node_c", 0, 3, "TestPlanet")
    node_c.buildings = []
    node_c.building_slots = 5
    
    p.provinces = [node_a, node_c]
    faction = MockFaction()
    
    with patch("src.services.construction_service.get_building_database") as mock_db:
        mock_db.return_value = {
             "TestBuilding": {
                "id": "TestBuilding", "cost": 100, "tier": 1, 
                "faction": "TestFaction", "effects": {"description": "test"}
            }
        }
        
        cost, _ = service._process_planet_construction(p, "TestFaction", faction, 1000, "EXPANSION")
        
        # Should return 0 cost because no valid node found
        assert cost == 0

def test_city_expansion_allowed(service):
    """Test that adding MORE buildings to an EXISTING city is allowed ignoring distance."""
    p = Planet("TestPlanet", "System", "TestFaction")
    
    # Node A: (0,0) - City (1 building). Distance to itself is 0, but it obeys "expansion" rule.
    node_a = HexNode("node_a", 0, 0, "TestPlanet")
    node_a.buildings = ["CityCenter"] # 1 used
    node_a.building_slots = 5 # 4 free
    
    p.provinces = [node_a]
    faction = MockFaction()
    
    with patch("src.services.construction_service.get_building_database") as mock_db:
         mock_db.return_value = {
             "TestBuilding": {
                "id": "TestBuilding", "cost": 100, "tier": 1, 
                "faction": "TestFaction", "effects": {"description": "test"}
            }
        }
         with patch("src.services.construction_service.get_stream") as mock_stream:
            mock_stream.return_value.choice.return_value = "TestBuilding"
            
            cost, _ = service._process_planet_construction(p, "TestFaction", faction, 1000, "EXPANSION")
            
            assert cost > 0
            assert p.construction_queue[-1]["node_id"] == "node_a"

def test_terrain_restriction_mountain(service):
    """Test that building is BLOCKED on Mountain terrain for new cities."""
    p = Planet("TestPlanet", "System", "TestFaction")
    
    # Node A: (0,0) - City. FULL.
    node_a = HexNode("node_a", 0, 0, "TestPlanet")
    node_a.buildings = ["CityCenter"]
    node_a.building_slots = 1
    
    # Node M: (0,4) - Empty Mountain. Distance is fine (4), but terrain is BLOCKED.
    node_m = HexNode("node_m", 0, 4, "TestPlanet")
    node_m.terrain_type = "Mountain"
    node_m.buildings = []
    node_m.building_slots = 5
    
    p.provinces = [node_a, node_m]
    faction = MockFaction()
    
    with patch("src.services.construction_service.get_building_database") as mock_db:
        mock_db.return_value = {
             "TestBuilding": {
                "id": "TestBuilding", "cost": 100, "tier": 1, 
                "faction": "TestFaction", "effects": {"description": "test"}
            }
        }
        cost, _ = service._process_planet_construction(p, "TestFaction", faction, 1000, "EXPANSION")
        
        # Should be blocked due to terrain
        assert cost == 0

def test_terrain_restriction_water(service):
    """Test that building is BLOCKED on Water terrain for new cities."""
    p = Planet("TestPlanet", "System", "TestFaction")
    
    # Node A: (0,0) - City. FULL.
    node_a = HexNode("node_a", 0, 0, "TestPlanet")
    node_a.buildings = ["CityCenter"]
    node_a.building_slots = 1
    
    # Node W: (0,4) - Empty Water. Distance fine, terrain BLOCKED.
    node_w = HexNode("node_w", 0, 4, "TestPlanet")
    node_w.terrain_type = "Water"
    node_w.buildings = []
    node_w.building_slots = 5
    
    p.provinces = [node_a, node_w]
    faction = MockFaction()
    
    with patch("src.services.construction_service.get_building_database") as mock_db:
        mock_db.return_value = {
             "TestBuilding": {
                "id": "TestBuilding", "cost": 100, "tier": 1, 
                "faction": "TestFaction", "effects": {"description": "test"}
            }
        }
        cost, _ = service._process_planet_construction(p, "TestFaction", faction, 1000, "EXPANSION")
        
        assert cost == 0

def test_terrain_restriction_expansion_allowed(service):
    """Test that expanding an EXISTING city is allowed EVEN IF it is on restricted terrain."""
    p = Planet("TestPlanet", "System", "TestFaction")
    
    # Node A: (0,0) - City on a Mountain. (Maybe from starter generation)
    node_a = HexNode("node_a", 0, 0, "TestPlanet")
    node_a.terrain_type = "Mountain"
    node_a.buildings = ["CityCenter"]
    node_a.building_slots = 5
    
    p.provinces = [node_a]
    faction = MockFaction()
    
    with patch("src.services.construction_service.get_building_database") as mock_db:
        mock_db.return_value = {
             "TestBuilding": {
                "id": "TestBuilding", "cost": 100, "tier": 1, 
                "faction": "TestFaction", "effects": {"description": "test"}
            }
        }
        with patch("src.services.construction_service.get_stream") as mock_stream:
            mock_stream.return_value.choice.return_value = "TestBuilding"
            
            cost, _ = service._process_planet_construction(p, "TestFaction", faction, 1000, "EXPANSION")
            
            # Should be ALLOWED because it's an expansion
            assert cost > 0
            assert p.construction_queue[-1]["node_id"] == "node_a"

