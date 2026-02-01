import pytest
from src.utils.dna_generator import normalize_dna, _init_dna_accumulators, ATOM_MASS, ATOM_ENERGY

def test_normalization_sum_precision():
    """Test if normalization sum is exactly 100.0 (within epsilon)."""
    raw_dna = _init_dna_accumulators()
    raw_dna[ATOM_MASS] = 33.333333 # Repeating decimal
    raw_dna[ATOM_ENERGY] = 33.333333
    
    normalized = normalize_dna(raw_dna, precision=4)
    total = sum(normalized.values())
    
    assert abs(total - 100.0) < 0.0001

def test_micro_value_preservation():
    """Test if micro-values survive normalization."""
    raw_dna = _init_dna_accumulators()
    # Add a tiny micro-trait
    raw_dna["atom_micro_trait"] = 0.0005 
    
    normalized = normalize_dna(raw_dna, precision=4)
    
    # Check if it survived normalization (should be > 0 if precision works)
    assert normalized.get('atom_micro_trait', 0) > 0
