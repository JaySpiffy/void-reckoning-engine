import pytest
from src.core.atomic_validator import (
    validate_atomic_budget, 
    normalize_to_budget, 
    get_budget_violations,
    validate_atomic_range,
    ATOMIC_BUDGET_TARGET
)
from src.core.elemental_signature import VALID_ATOMS

class TestAtomicValidator:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.valid_signature = {
            "atom_mass": 50.0,
            "atom_energy": 50.0
        }
        self.overbudget_signature = {
            "atom_mass": 60.0,
            "atom_energy": 60.0
        }
        self.underbudget_signature = {
            "atom_mass": 40.0,
            "atom_energy": 40.0
        }
        self.negative_signature = {
            "atom_mass": 110.0,
            "atom_energy": -10.0
        }
        self.zero_signature = {
            "atom_mass": 0.0,
            "atom_energy": 0.0
        }

    def test_valid_budget_exact_100(self):
        is_valid, msg = validate_atomic_budget(self.valid_signature)
        assert is_valid
        assert msg == ""

    def test_valid_budget_within_tolerance(self):
        # 100.005 is within 0.01 tolerance. 
        # Split across two atoms so neither exceeds 100.0 range limit.
        sig = {"atom_mass": 50.005, "atom_energy": 50.0}
        is_valid, msg = validate_atomic_budget(sig)
        assert is_valid

    def test_invalid_budget_overbudget(self):
        is_valid, msg = validate_atomic_budget(self.overbudget_signature)
        assert not is_valid
        assert "120.00" in msg

    def test_invalid_budget_underbudget(self):
        is_valid, msg = validate_atomic_budget(self.underbudget_signature)
        assert not is_valid
        assert "80.00" in msg

    def test_invalid_budget_negative(self):
        """Test that negative atoms fail budget validation even if sum is 100."""
        # negative_signature: Mass 110, Energy -10. Sum = 100.
        is_valid, msg = validate_atomic_budget(self.negative_signature)
        assert not is_valid
        assert "Atomic range violation" in msg
        assert "atom_energy: -10.0" in msg

    def test_invalid_budget_all_zeros(self):
        """Test that all-zeros signature fails budget validation."""
        is_valid, msg = validate_atomic_budget(self.zero_signature)
        assert not is_valid
        assert "0.00" in msg

    def test_normalize_to_budget_standard(self):
        # Input sum is 80, target 100. Scale factor 1.25
        normalized = normalize_to_budget(self.underbudget_signature)
        assert sum(normalized.values()) == pytest.approx(100.0)
        assert normalized["atom_mass"] == 50.0

    def test_normalize_to_budget_zero_sum(self):
        # Input sum 0. Should distribute equally.
        normalized = normalize_to_budget(self.zero_signature)
        assert sum(normalized.values()) == pytest.approx(100.0)
        assert normalized["atom_mass"] == 50.0
        assert normalized["atom_energy"] == 50.0

    def test_get_budget_violations_diagnostics(self):
        violations = get_budget_violations(self.negative_signature)
        assert violations["total"] == pytest.approx(100.0) # Sum is 100 still
        assert "atom_energy" in violations["negative_atoms"]
        
        violations_over = get_budget_violations(self.overbudget_signature)
        assert violations_over["delta"] == 20.0
        assert violations_over["pct_error"] == pytest.approx(20.0)

    def test_validate_atomic_range_valid(self):
        is_valid, violations = validate_atomic_range(self.valid_signature)
        assert is_valid
        assert len(violations) == 0

    def test_validate_atomic_range_invalid(self):
        sig = {"atom_mass": 150.0, "atom_energy": -50.0}
        is_valid, violations = validate_atomic_range(sig)
        assert not is_valid
        assert len(violations) == 2
