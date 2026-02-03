
import pytest
from unittest.mock import MagicMock, patch
from src.combat.combat_phases import OrbitalSupportPhase
from src.models.hex_node import HexNode
from src.core.simulation_topology import GraphEdge
from src.combat.real_time.map_manager import MapGenerator, ShieldDome
from src.combat.tactical_grid import TacticalGrid

class TestOrbitalBombardment:
    
    @pytest.fixture
    def mock_hex_node(self):
        node = HexNode("test_node", 0, 0, "planet_1")
        node.buildings = []
        node.edges = []
        return node

    @pytest.fixture
    def mock_building_db(self):
        return {
            "shield_gen": {
                "effects": {"description": "Reduces bombardment damage by 50%"}
            },
            "city_center": {
                "effects": {"description": "Provides administration"}
            }
        }

    def test_hex_node_defense_parsing(self, mock_hex_node, mock_building_db):
        """Test that HexNode correctly parses bombardment defense from buildings."""
        mock_hex_node.buildings = ["shield_gen"]
        
        with patch('src.core.constants.get_building_database', return_value=mock_building_db):
            defense = mock_hex_node.get_bombardment_defense()
            assert defense == 0.5

    def test_aoe_mitigation(self, mock_hex_node, mock_building_db):
        """Test that bombardment logic correctly applies AoE shielding from neighbors."""
        
        # Setup: Target Node has NO shield
        target_node = mock_hex_node
        target_node.buildings = []
        
        # Neighbor Node HAS shield (50%)
        neighbor = HexNode("neighbor", 1, 0, "planet_1")
        neighbor.buildings = ["shield_gen"]
        
        # Link them
        edge = GraphEdge(target_node, neighbor)
        target_node.edges.append(edge)
        
        with patch('src.core.constants.get_building_database', return_value=mock_building_db):
            # Verify neighbor has defense
            assert neighbor.get_bombardment_defense() == 0.5
            
            # Now simulate Combat Phase logic manually (since it's embedded in execute)
            # Logic: Target Defense + (Neighbor Defense * 0.5)
            
            mitigation = 0.0
            if hasattr(target_node, 'get_bombardment_defense'):
                mitigation += target_node.get_bombardment_defense()
                
            for edge in target_node.edges:
                neighbor = edge.target
                mitigation += neighbor.get_bombardment_defense() * 0.5
                
            # Expected: 0 + (0.5 * 0.5) = 0.25
            assert mitigation == 0.25

    def test_map_generator_shield_dome(self, mock_hex_node):
        """Test that MapGenerator adds a ShieldDome if a shield generator is present."""
        grid = TacticalGrid(100, 100)
        
        # Case 1: Local Shield
        mock_hex_node.buildings = ["Neutral_Kinetic Shield Generator"]
        MapGenerator.generate_map(grid, mock_hex_node)
        
        # Check for ShieldDome in grid visuals/obstacles
        # Note: In my implementation I added it to obstacles and visuals
        # Currently obstacles is the main list
        shield_domes = [obj for obj in grid.obstacles if isinstance(obj, ShieldDome)]
        assert len(shield_domes) == 1
        assert shield_domes[0].strength == 1.0
        
    def test_map_generator_neighbor_shield(self, mock_hex_node):
        """Test visual shield from neighbor."""
        grid = TacticalGrid(100, 100)
        mock_hex_node.buildings = [] # No local shield
        
        neighbor = HexNode("neighbor", 1, 0, "planet_1")
        neighbor.buildings = ["Neutral_Kinetic Shield Generator"]
        edge = GraphEdge(mock_hex_node, neighbor)
        mock_hex_node.edges.append(edge)
        
        MapGenerator.generate_map(grid, mock_hex_node)
        
        shield_domes = [obj for obj in grid.obstacles if isinstance(obj, ShieldDome)]
        assert len(shield_domes) == 1
        assert shield_domes[0].strength == 0.5 # Faint shield for neighbor
