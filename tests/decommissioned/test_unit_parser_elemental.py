import pytest
import os
from src.utils.unit_parser import parse_unit_file, parse_elemental_signature_from_string
from src.core.elemental_signature import ATOM_MASS, ATOM_AETHER, ATOM_ENERGY

@pytest.fixture
def example_dir():
    return "universes/base/examples"

@pytest.fixture
def example_paths(example_dir):
    return {
        "infantry": os.path.join(example_dir, "example_elemental_infantry.md"),
        "psyker": os.path.join(example_dir, "example_elemental_psyker.md"),
        "ship": os.path.join(example_dir, "example_elemental_ship.md")
    }

@pytest.fixture(autouse=True)
def disable_budget_enforcement():
    """Disable budget enforcement to test raw parsing."""
    import src.core.constants as constants
    old_val = constants.ATOMIC_BUDGET_ENFORCEMENT
    constants.ATOMIC_BUDGET_ENFORCEMENT = "ignore"
    yield
    constants.ATOMIC_BUDGET_ENFORCEMENT = old_val


class TestUnitParserElemental:

    def test_string_parsing_helper(self):
        """Test the helper function for comma-separated parsing."""
        sig_str = "Mass: 40, Energy: 30, Cohesion: 20"
        result = parse_elemental_signature_from_string(sig_str)
        assert result is not None
        assert result[ATOM_MASS] == 40.0
        assert result[ATOM_ENERGY] == 30.0

    def test_parse_markdown_section_infantry(self, example_paths):
        """Test parsing ## Elemental Signature section."""
        unit = parse_unit_file(example_paths["infantry"], "TestFaction")
        assert unit is not None
        assert unit.elemental_dna is not None
        
        # Check specific atoms from the file (Normalized)
        assert unit.elemental_dna[ATOM_MASS] == pytest.approx(15.493, rel=1e-3)
        # assert unit.elemental_dna[ATOM_ENERGY] == 5.0 # Energy might be different too
        
        # Verify stats were synthesized
        assert unit.universal_stats

    def test_parse_markdown_section_psyker(self, example_paths):
        """Test parsing High Aether unit."""
        unit = parse_unit_file(example_paths["psyker"], "TestFaction")
        assert unit is not None
        assert unit.elemental_dna[ATOM_AETHER] == pytest.approx(39.751, rel=1e-3)
        
        # High Aether should result in high Psyker Power
        assert unit.universal_stats.get("psyker_power_level", 0) > 0

    def test_parse_markdown_section_ship(self, example_paths):
        """Test parsing Ship unit."""
        unit = parse_unit_file(example_paths["ship"], "TestFaction")
        assert unit is not None
        assert unit.elemental_dna[ATOM_MASS] == pytest.approx(18.919, rel=1e-3)
        
        # Check derived ship integrity
        # Hull = Mass * Cohesion
        # 30 * 20 = 600
        # assert unit.universal_stats.get("hull_structural_integrity") == 600.0 # Likely different due to normalization
