import pytest
import unittest
from src.models.unit import Regiment, Ship
from src.core.elemental_signature import (
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_STABILITY, ATOM_INFORMATION
)
import src.core.constants as constants_module
import src.models.unit as unit_module

class TestUnitElementalIntegration:

    def test_elemental_initialization_regiment(self):
        """Test Case 1: Create a Regiment with elemental DNA and verify synthesis."""
        elemental_dna = {
            ATOM_MASS: 50.0,
            ATOM_COHESION: 40.0,
            ATOM_ENERGY: 50.0,
            ATOM_STABILITY: 20.0,
            ATOM_INFORMATION: 20.0
        }
        
        # Initialize with elemental DNA, legacy stats at 0
        unit = Regiment(
            "Elemental Golem", 0, 0, 0, 0, 0, {}, 
            elemental_dna=elemental_dna
        )
        
        # Map synthesized stats to legacy attributes
        unit.apply_dna_to_legacy()
        
        # Verify legacy stats were populated from synthesis
        # m*c = 50*40 = 2000. HP = 2000/10 = 200.
        assert unit.base_hp == 200
        assert unit.armor > 0
        assert unit.base_damage > 0

    def test_legacy_fallback(self):
        """Test Case 2: Verify unit still works with legacy stats only."""
        unit = Regiment(
            "Legacy Soldier", 40, 40, 100, 4, 10, {}
        )
        
        # Explicitly call population (usually called by subclass or recalc)
        unit._populate_universal_stats_from_legacy()
        
        assert unit._dna_populated
        assert unit.base_hp == 100
        assert unit.universal_stats["hull_structural_integrity"] > 0

    def test_serialization_roundtrip_with_elements(self):
        """Test Case 3: Verify serialization preserves elemental DNA."""
        elemental_dna = {ATOM_MASS: 10.0, ATOM_ENERGY: 5.0}
        unit = Ship(
            "Elemental Scout", 0, 0, 0, 0, 0, {}, 
            elemental_dna=elemental_dna
        )
        
        dna_packet = unit.serialize_dna()
        assert "elemental_dna" in dna_packet
        assert dna_packet["elemental_dna"][ATOM_MASS] == 10.0
        
        # Deserialize
        from src.models.unit import Unit
        new_unit = Unit.deserialize_dna(dna_packet)
        
        assert new_unit.name == "Elemental Scout"
        assert new_unit.elemental_dna[ATOM_MASS] == 10.0
        assert new_unit._dna_populated

    def test_trait_interaction_with_elements(self):
        """Test Case 4: Verify traits affect stats along with elemental DNA."""
        # Hull Integrity = Mass * Cohesion
        # Multiplier traits (starting at 1.0) should multiply synthesized values
        elemental_dna = {ATOM_MASS: 10.0, ATOM_COHESION: 10.0}
        
        # Trait that boosts Hull Integrity (multiplicative metric in universal_stats)
        unit = Regiment(
            "Nano-Enforced Knight", 0, 0, 0, 0, 0, {}, 
            traits=["Nano-Armor"],
            elemental_dna=elemental_dna
        )
        
        # Mock trait modifier: Nano-Armor doubles hull integrity
        trait_mods = {"Nano-Armor": {"hull_structural_integrity": 2.0}}
        unit.apply_traits(trait_mods)
        
        # Base hull = 10 * 10 = 100
        # Post trait = 100 * 2.0 = 200
        # Legacy HP = 200 / 10 = 20
        # Legacy HP = 200 / 10 = 20
        unit.apply_dna_to_legacy()
        assert unit.base_hp == 20

    def test_unit_creation_with_valid_budget(self):
        """Test Case 5: Ensure strict budget unit creation passes."""
        valid_dna = {ATOM_MASS: 50.0, ATOM_ENERGY: 50.0} # Sum 100
        unit = Regiment("Valid Unit", 0, 0, 0, 0, 0, {}, elemental_dna=valid_dna)
        assert unit.name == "Valid Unit"

    def test_unit_creation_with_invalid_budget_normalize(self):
        """Test Case 6: Verify normalization mode fixes budget."""
        # Patch config
        original_mode = constants_module.ATOMIC_BUDGET_ENFORCEMENT
        constants_module.ATOMIC_BUDGET_ENFORCEMENT = "normalize"
        
        try:
            invalid_dna = {ATOM_MASS: 40.0, ATOM_ENERGY: 40.0} # Sum 80
            unit = Regiment("Auto-Normal Unit", 0, 0, 0, 0, 0, {}, elemental_dna=invalid_dna)
            
            # Should scale to 100.0 (factor 1.25)
            assert unit.elemental_dna[ATOM_MASS] == pytest.approx(50.0)
            assert unit.elemental_dna[ATOM_ENERGY] == pytest.approx(50.0)
        finally:
            constants_module.ATOMIC_BUDGET_ENFORCEMENT = original_mode

    def test_unit_creation_with_invalid_budget_strict(self):
        """Test Case 7: Verify strict mode raises error."""
        original_mode = constants_module.ATOMIC_BUDGET_ENFORCEMENT
        constants_module.ATOMIC_BUDGET_ENFORCEMENT = "strict"
        
        try:
            invalid_dna = {ATOM_MASS: 150.0} # Sum 150
            with pytest.raises(ValueError):
                Regiment("Strict Fail", 0, 0, 0, 0, 0, {}, elemental_dna=invalid_dna)
        finally:
            constants_module.ATOMIC_BUDGET_ENFORCEMENT = original_mode
