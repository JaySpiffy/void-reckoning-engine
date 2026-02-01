import pytest
from unittest.mock import MagicMock, patch
from src.factories.unit_factory import UnitFactory
from src.models.unit import Ship, Regiment, Unit

class TestUnitFactory:
    
    def test_create_transport(self):
        u = UnitFactory.create_transport("Imperium")
        assert isinstance(u, Ship)
        assert u.name == "Generic Transport"
        assert u.faction == "Imperium"
        assert u.transport_capacity == 4

    def test_create_pdf(self):
        u1 = UnitFactory.create_pdf("Conscript", "Imperium")
        assert u1.name == "PDF Conscript"
        assert u1.ma == 30
        
        u2 = UnitFactory.create_pdf("Elite", "Imperium")
        assert u2.name == "PDF Elite"
        assert u2.ma == 40

    @patch("src.core.universe_data.UniverseDataManager")
    @patch("src.utils.blueprint_registry.BlueprintRegistry")
    @patch("src.core.atomic_validator.validate_atomic_budget")
    def test_create_from_blueprint_id_ship(self, mock_validator, MockRegistry, MockUDM):
        # Setup Mocks
        mock_validator.return_value = (True, "") # Always valid
        
        mock_registry_instance = MockRegistry.get_instance.return_value
        mock_registry_instance.get_blueprint.return_value = {
            "name": "Cruiser",
            "type": "ship",
            "base_stats": {"ma": 60, "md": 60, "hp": 500, "shield": 100},
            "default_traits": ["VoidShield"],
            "elemental_signature": None # Ensure None so synthesis doesn't override HP
        }
        
        mock_udm_instance = MockUDM.get_instance.return_value
        mock_udm_instance.active_universe = "base"
        mock_udm_instance.get_trait_registry.return_value = {} 
        
        # Test
        unit = UnitFactory.create_from_blueprint_id("cruiser_blueprint", "Imperium")
        
        assert isinstance(unit, Ship)
        assert unit.name == "Cruiser"
        assert unit.base_hp == 500
        assert unit.shield_max == 100
        assert "VoidShield" in unit.traits

    @patch("src.core.universe_data.UniverseDataManager")
    @patch("src.utils.blueprint_registry.BlueprintRegistry")
    def test_create_from_blueprint_id_regiment(self, MockRegistry, MockUDM):
        # Setup Mocks
        mock_registry_instance = MockRegistry.get_instance.return_value
        mock_registry_instance.get_blueprint.return_value = {
            "name": "Guardsmen",
            "type": "infantry",
            "base_stats": {"ma": 40, "md": 40, "hp": 50},
            "default_traits": ["Lasgun"],
            "unit_class": "Infantry",
            "elemental_signature": None
        }
        
        mock_udm_instance = MockUDM.get_instance.return_value
        mock_udm_instance.active_universe = "base"
        mock_udm_instance.get_trait_registry.return_value = {}
        
        # Test
        unit = UnitFactory.create_from_blueprint_id("guardsmen_blueprint", "Imperium", traits=["Veteran"])
        
        assert isinstance(unit, Regiment)
        assert unit.name == "Guardsmen"
        assert unit.unit_class == "Infantry"
        assert "Lasgun" in unit.traits
        assert "Veteran" in unit.traits

    @patch("src.core.universe_data.UniverseDataManager")
    def test_finalize_unit_applies_traits(self, MockUDM):
        # Setup Trait Registry
        mock_udm_instance = MockUDM.get_instance.return_value
        mock_udm_instance.get_trait_registry.return_value = {
            "Veteran": {
                "modifiers": {"integrity_hull_structure": 1.1}
            }
        }
        
        unit = Unit(name="TestUnit", faction="Imperium", ma=50, md=50, hp=100, armor=0, damage=10, abilities={}, traits=["Veteran"])
        
        # Mock apply_traits on the unit instance to verify Factory calls it
        with patch.object(unit, 'apply_traits') as mock_apply:
             UnitFactory._finalize_unit(unit)
             
             # Verify call with expected modifiers
             mock_apply.assert_called_once()
             args, _ = mock_apply.call_args
             assert args[0] == {"Veteran": {"integrity_hull_structure": 1.1}}
             
             # Also verify recalc_stats called?
             # But recalc_stats is harder to spy on unless we mock it too.
             # Assume apply_traits call proves Factory logic.

