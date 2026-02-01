
import pytest
from src.utils.rng_manager import RNGManager, get_stream

def test_rng_determinism_manager():
    print("=== Testing RNG Manager Determinism ===")
    
    seed = 42
    manager = RNGManager.get_instance()
    
    # 1. Reseed All
    manager.reseed_all(seed)
    
    # 2. Sample values
    combat_v1 = [get_stream("combat").random() for _ in range(5)]
    phases_v1 = [get_stream("phases").randint(1, 100) for _ in range(5)]
    
    # 3. Reseed Again
    manager.reseed_all(seed)
    
    # 4. Sample again
    combat_v2 = [get_stream("combat").random() for _ in range(5)]
    phases_v2 = [get_stream("phases").randint(1, 100) for _ in range(5)]
    
    # 5. Compare
    assert combat_v1 == combat_v2, "Combat RNG failure!"
    assert phases_v1 == phases_v2, "Phases RNG failure!"
    
    print("\nSUCCESS: All RNG instances are deterministic for seed 42.")

def test_rng_independence():
    seed = 123
    manager = RNGManager.get_instance()
    manager.reseed_all(seed)
    
    # Combat and Phases should derive different seeds from base seed
    val1 = get_stream("combat").random()
    # Reset just one stream to check? No, reseed_all resets all.
    # Let's check internal seeds match expectation of difference
    
    rng_combat = get_stream("combat")
    rng_phases = get_stream("phases")
    
    # They should yield different first values (highly probable)
    manager.reseed_all(seed)
    v_c = rng_combat.random()
    manager.reseed_all(seed)
    v_p = rng_phases.random()
    
    # Wait, if they are different streams, they have different derived seeds.
    # v_c from combat logic vs v_p from phases logic.
    assert v_c != v_p, "Different streams should produce different sequences from same base seed"
