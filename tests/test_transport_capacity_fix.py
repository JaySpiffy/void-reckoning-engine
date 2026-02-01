
import pytest
from src.factories.unit_factory import UnitFactory
from src.models.unit import Ship

def test_transport_capacity_inheritance():
    # Mock blueprint
    class MockBlueprint:
        def __init__(self):
            self.name = "Test Ship"
            self.type = "ship"
            self.base_ma = 50
            self.base_md = 50
            self.base_hp = 1000
            self.armor = 50
            self.base_damage = 50
            self.cost = 1000
            self.shield_max = 500
            self.movement_points = 10
            self.blueprint_id = "test_ship_id"
            self.base_stats = {
                "ma": 50, "md": 50, "hp": 1000, "armor": 50, 
                "damage": 50, "shield": 500, "movement": 10,
                "transport_capacity": 5
            }
            self.universal_stats = {}
            self.default_traits = []
            self.source_universe = "test"

    bp = MockBlueprint()
    
    # We need to bypass the registry lookup in create_from_blueprint if we want to test create_from_blueprint_id logic directly
    # Or we can just mock the registry.
    
    # Actually, create_from_blueprint_id is what I modified.
    # It takes blueprint_id, faction_name, traits.
    # It internalizes BlueprintRegistry.get_instance().get_blueprint(blueprint_id)
    
    from src.utils.blueprint_registry import BlueprintRegistry
    reg = BlueprintRegistry.get_instance()
    reg.register_blueprint({
        "id": "test_ship_id",
        "name": "Test Ship",
        "type": "ship",
        "base_stats": {
            "ma": 10, "md": 10, "hp": 100, "armor": 10, "damage": 10, "transport_capacity": 5
        },
        "cost": 100
    }, source_universe="test")
    
    unit = UnitFactory.create_from_blueprint_id("test_ship_id", "Federation")
    
    assert isinstance(unit, Ship)
    assert unit.transport_capacity == 5
    print(f"SUCCESS: Transport capacity is {unit.transport_capacity}")

def test_generic_transport_factory():
    unit = UnitFactory.create_transport("Federation")
    assert isinstance(unit, Ship)
    assert unit.transport_capacity == 4
    assert "Transport" in unit.abilities.get("Tags", [])
    print(f"SUCCESS: Generic transport capacity is {unit.transport_capacity}")

if __name__ == "__main__":
    test_transport_capacity_inheritance()
    test_generic_transport_factory()
