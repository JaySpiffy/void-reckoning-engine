import pytest
import os
import json
from unittest.mock import MagicMock, patch
from src.managers.tech_manager import TechManager
from src.models.faction import Faction

class TestTechManager:
    @pytest.fixture
    def tech_dir(self, tmp_path):
        d = tmp_path / "technology"
        d.mkdir()
        return d

    @pytest.fixture
    def mock_config(self):
        conf = MagicMock()
        conf.tech_cost_multiplier = 1.0
        return conf

    @pytest.fixture
    def manager(self, tech_dir, mock_config):
        # Create dummy tech files
        registry = {
            "Lasers": {
                "faction": "Global",
                "cost": 100,
                "unlocks_ships": ["Laser_Frigate"]
            },
            "Shields": {
                "faction": "Global",
                "cost": 150
            },
            "Bolter_Tech": {
                "faction": "Imperium",
                "cost": 200,
                "unlocks_ships": ["Space_Marine"]
            }
        }
        with open(tech_dir / "technology_registry.json", "w") as f:
            json.dump(registry, f)

        # Create Faction MD (optional, not used for this test)
        md_content = """
# Imperium Tech Tree
"""
        with open(tech_dir / "imperium_tech_tree.md", "w") as f:
            f.write(md_content)

        return TechManager(tech_dir=str(tech_dir), game_config=mock_config)

    def test_load_tech_trees(self, manager):
        # Check Global
        assert "global" in manager.faction_tech_trees
        # Wait, implementation says: if "Global", adds to GENERIC_TECHS, then merges into ALL factions.
        # But initially creates "global" in generic_techs dict.
        # In load_tech_trees: 
        # generic_techs = ...
        # items add to generic_techs.
        # Then merged into self.faction_tech_trees items.
        
        # Check Imperium
        assert "imperium" in manager.faction_tech_trees
        tree = manager.faction_tech_trees["imperium"]
        
        # Verify Lasers (Global) merged in
        assert "Lasers" in tree["techs"]
        assert tree["techs"]["Lasers"] == 100
        
        # Verify Bolter_Tech (Faction Specific)
        assert "Bolter_Tech" in tree["techs"]
        
        # Verify Unlocks
        assert "Space_Marine" in tree["units"]
        assert tree["units"]["Space_Marine"] == "Bolter_Tech"

    def test_prerequisites_logic(self, manager):
        # Setup: Add a dependency manually to test logic
        # A -> B
        tree = manager.faction_tech_trees["imperium"]
        tree["techs"]["Tech_A"] = 100
        tree["techs"]["Tech_B"] = 200
        tree.setdefault("prerequisites", {})["Tech_B"] = ["Tech_A"]
        
        # Case 1: No Unlocks
        assert manager.can_research("imperium", "Tech_A", unlocked_techs=[]) is True
        assert manager.can_research("imperium", "Tech_B", unlocked_techs=[]) is False
        
        # Case 2: Prerequisites met
        assert manager.can_research("imperium", "Tech_B", unlocked_techs=["Tech_A"]) is True

    def test_infinite_research_generation(self, manager):
        tree = manager.faction_tech_trees["imperium"]
        tree["techs"]["Lasers I"] = 100
        
        # Generator
        new_id = manager.generate_next_tier_tech("imperium", "Lasers I")
        
        assert new_id == "Lasers 2"
        assert "Lasers 2" in tree["techs"]
        assert tree["techs"]["Lasers 2"] == 150 # 100 * 1.5
        assert tree["prerequisites"]["Lasers 2"] == ["Lasers I"]

    def test_get_available_research(self, manager):
        faction = MagicMock(spec=Faction)
        faction.name = "Imperium"
        faction.unlocked_techs = ["Lasers"] # Already have Lasers
        faction.research_queue = []
        
        # Setup tree:
        # Lasers (Unlocked)
        # Shields (Available)
        # Bolters (Available)
        
        available = manager.get_available_research(faction)
        ids = [item["id"] for item in available]
        
        assert "Shields" in ids
        assert "Bolter_Tech" in ids
        assert "Lasers" not in ids

    def test_upgrade_weapon(self, manager):
        arsenal = {
            "laser_mk1": {
                "name": "Laser Cannon Mk I",
                "stats": {"power": 100, "range": 50},
                "cost": 200
            }
        }
        
        new_weapon = manager.upgrade_weapon("imperium", "laser_mk1", arsenal)
        
        assert new_weapon is not None
        assert new_weapon["id"] == "laser_mk1_mk2"
        assert new_weapon["name"] == "Laser Cannon Mk I Mk II"
        assert new_weapon["stats"]["power"] == 110 # +10%
        assert new_weapon["stats"]["range"] == 52  # 50 * 1.05 = 52.5 -> 52 int
        
        # Verify it was added to arsenal
        assert "laser_mk1_mk2" in arsenal

