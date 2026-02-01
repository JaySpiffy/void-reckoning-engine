import pytest
from src.core.elemental_signature import (
    get_default_elemental_signature,
    validate_elemental_signature,
    VALID_ATOMS,
    ATOM_MASS,
    ATOM_ENERGY,
    ATOM_COHESION,
    ATOM_INFORMATION,
    ATOM_AETHER,
    ATOM_WILL,
    ATOM_VOLATILITY,
    ATOM_FREQUENCY,
    ATOM_STABILITY,
    ATOM_FOCUS
)

class TestElementalSignature:
    
    def test_default_signature_generation(self):
        """Test Case 1: Verify default signature has 10 keys and all are 0.0."""
        sig = get_default_elemental_signature()
        assert len(sig) == 10
        for value in sig.values():
            assert value == 0.0
            
    def test_validation_valid_signature(self):
        """Test Case 2: Verify validation returns True for correct atoms."""
        sig = {atom: 0.5 for atom in VALID_ATOMS}
        assert validate_elemental_signature(sig)
        
    def test_validation_invalid_keys(self):
        """Test Case 3: Verify validation returns False for unknown keys."""
        sig = {"invalid_atom": 1.0}
        assert not validate_elemental_signature(sig)
        
    def test_validation_non_dict_input(self):
        """Test Case 4: Verify validation handles non-dict inputs."""
        assert not validate_elemental_signature(["not", "a", "dict"])
        assert not validate_elemental_signature("string")
        assert not validate_elemental_signature(None)
        
    def test_constant_integrity(self):
        """Test Case 5: Verify constants are unique strings and set matches."""
        constants = [
            ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_INFORMATION,
            ATOM_AETHER, ATOM_WILL, ATOM_VOLATILITY, ATOM_FREQUENCY,
            ATOM_STABILITY, ATOM_FOCUS
        ]
        # All strings
        for c in constants:
            assert isinstance(c, str)
            
        # All unique
        assert len(set(constants)) == 10
        
        # VALID_ATOMS set content
        assert VALID_ATOMS == set(constants)
