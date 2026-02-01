import pytest
from src.utils.validator import validate_parser_data

# --- Fixtures ---

@pytest.fixture
def registries():
    buildings = {
        "Barracks": {"tier": 1},
        "Factory": {"tier": 2}
    }
    techs = {"Lasers": {}, "Armor": {}}
    weapons = {"Bolter": {}}
    abilities = {"Charge": {}}
    return buildings, techs, weapons, abilities

@pytest.fixture
def valid_unit_data():
    return {
        "name": "Space Marine",
        "tier": "1",
        "hp": "20",
        "armor": "10",
        "leadership": "8",
        "speed": "4",
        "requisition_cost": "100",
        "control_cost": "1",
        "required_building": "Barracks",
        "required_tech": "['Lasers']",
        "melee_attack": "4",
        "melee_defense": "4",
        "weapon_skill": "4"
    }

# --- Tests ---

def test_valid_unit(registries, valid_unit_data):
    errors = []
    warnings = []
    b, t, w, a = registries
    
    validate_parser_data("test_file.md", valid_unit_data, b, t, w, a, errors, warnings)
    
    assert len(errors) == 0
    assert len(warnings) == 0

def test_missing_required_fields(registries):
    data = {"name": "Incomplete"} # Missing many fields
    errors = []
    warnings = []
    b, t, w, a = registries
    
    validate_parser_data("test_file.md", data, b, t, w, a, errors, warnings)
    
    assert len(errors) > 0
    assert any("Missing required field" in e for e in errors)

def test_invalid_types_integer(registries, valid_unit_data):
    valid_unit_data["hp"] = "NotANumber"
    errors = []
    warnings = []
    b, t, w, a = registries
    
    validate_parser_data("test_file.md", valid_unit_data, b, t, w, a, errors, warnings)
    
    assert len(errors) > 0
    assert any("are not numbers" in e for e in errors)

def test_invalid_building_reference(registries, valid_unit_data):
    valid_unit_data["required_building"] = "NonExistent"
    errors = []
    warnings = []
    b, t, w, a = registries
    
    validate_parser_data("test_file.md", valid_unit_data, b, t, w, a, errors, warnings)
    
    assert len(errors) > 0
    assert any("Invalid Building Reference" in e for e in errors)

def test_invalid_tech_reference(registries, valid_unit_data):
    valid_unit_data["required_tech"] = "['UnknownTech']"
    errors = []
    warnings = []
    b, t, w, a = registries
    
    validate_parser_data("test_file.md", valid_unit_data, b, t, w, a, errors, warnings)
    
    assert len(errors) > 0
    assert any("Invalid Tech Reference" in e for e in errors)

def test_tier_logic_error(registries, valid_unit_data):
    # Tier 1 unit requiring Tier 2 building
    valid_unit_data["tier"] = "1"
    valid_unit_data["required_building"] = "Factory" # Tier 2 in fixture
    
    errors = []
    warnings = []
    b, t, w, a = registries
    
    validate_parser_data("test_file.md", valid_unit_data, b, t, w, a, errors, warnings)
    
    # Validator currently logs this as error AND warning
    assert len(errors) > 0
    assert any("Logic Error" in e for e in errors)
    assert len(warnings) > 0
    assert warnings[0]["delta"] > 0
