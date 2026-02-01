import pytest
from src.factories.unit_factory import UnitFactory
from src.utils.unit_parser import parse_json_roster
from src.core.universe_data import UniverseDataManager
import os
import json

class TestComponentGeneration:
    
    @classmethod
    def setup_class(cls):
        # Ensure we are in the Eternal Crusade universe
        manager = UniverseDataManager.get_instance()
        manager.load_universe_data("eternal_crusade")
        
        # Manually trigger BlueprintRegistry load for the test environment
        from src.utils.blueprint_registry import BlueprintRegistry
        BlueprintRegistry.get_instance().load_blueprints(manager.universe_config.universe_root)

    def test_ship_component_extraction(self):
        # Use a real one from the registry if it exists
        u = UnitFactory.create_from_blueprint_id("ancient_guardians_watcher_class", "Ancient_Guardians")
        assert u is not None
        # Watcher Class Frigate should have weapons
        weapons = [c for c in u.components if c.type == "Weapon"]
        assert len(weapons) > 0
        
    def test_land_unit_with_prefixes(self):
        # Mock a roster entry with prefixes
        mock_roster = [
            {
                "name": "Test Tank",
                "blueprint_id": "test_tank",
                "faction": "Cyber_Synod",
                "base_stats": {"hp": 100, "armor": 50, "damage": 20},
                "components": [
                    {"slot": "weapon_heavy", "component": "land_vehicle_test_gun"}
                ],
                "elemental_dna": {"atom_mass": 20, "atom_energy": 10}
            }
        ]
        
        # Create a temp file
        temp_file = "temp_test_roster_pref.json"
        with open(temp_file, "w") as f:
            json.dump(mock_roster, f)
            
        try:
            units = parse_json_roster(temp_file, "Cyber_Synod")
            u = units[0]
            weapons = [c for c in u.components if c.type == "Weapon"]
            assert len(weapons) == 1
            assert weapons[0].name == "land_vehicle_test_gun"
            # It should have synthesized stats because 'land_vehicle_test_gun' is not in registry
            assert "S" in weapons[0].weapon_stats
            assert weapons[0].weapon_stats["S"] > 0
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_dna_fallback_no_weapons(self):
        # Create a unit without any authentic weapons or components
        from src.models.unit import Regiment
        dna = {"atom_mass": 30, "atom_energy": 20, "atom_volatility": 10}
        u = Regiment("DNA Unit", 50, 50, 100, 10, 10, {}, "Neutral", elemental_dna=dna)
        
        weapons = [c for c in u.components if c.type == "Weapon"]
        assert len(weapons) == 1
        assert weapons[0].name == "Synthesized Armaments"
        assert weapons[0].weapon_stats["S"] > 0
        assert weapons[0].weapon_stats["Range"] > 0
