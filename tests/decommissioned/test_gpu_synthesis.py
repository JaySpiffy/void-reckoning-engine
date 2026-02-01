import pytest
import random
import math
from src.core import gpu_utils
from src.core.elemental_signature import (
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_INFORMATION,
    ATOM_AETHER, ATOM_WILL, ATOM_VOLATILITY, ATOM_FREQUENCY,
    ATOM_STABILITY, ATOM_FOCUS
)
from src.core.synthesis_layer import synthesize_universal_stats, synthesize_batch

pytestmark = pytest.mark.skip(reason="CuPy compatibility issue")

class TestGPUSynthesis:
    
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_synthesis_correctness(self):
        print(f"\nTesting Synthesis Batch with Backend: {gpu_utils.get_xp().__name__}")
        
        # 1. Generate Input Data
        signatures = []
        atoms = [ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_INFORMATION, 
                 ATOM_AETHER, ATOM_WILL, ATOM_VOLATILITY, ATOM_FREQUENCY, 
                 ATOM_STABILITY, ATOM_FOCUS]
                 
        for _ in range(100):
            sig = {atom: random.uniform(0.1, 100.0) for atom in atoms}
            signatures.append(sig)
            
        # 2. Run Legacy (Golden Reference)
        legacy_results = [synthesize_universal_stats(s) for s in signatures]
        
        # 3. Run Batch (Vectorized)
        batch_results = synthesize_batch(signatures)
        
        # 4. Compare
        assert len(legacy_results) == len(batch_results)
        
        for i, legacy in enumerate(legacy_results):
            batch = batch_results[i]
            
            # Check keys match
            assert legacy.keys() == batch.keys()
            
            for k, val_l in legacy.items():
                val_b = batch[k]
                
                # Use close tolerance for floats
                # Due to potential float32 (GPU) vs float64 (Python) diffs, be generous?
                assert math.isclose(val_l, val_b, rel_tol=1e-4, abs_tol=1e-4), \
                    f"Mismatch for unit {i} key {k}: Legacy {val_l} != Batch {val_b}"
