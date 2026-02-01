import pytest
from unittest.mock import MagicMock
from src.core.physics_calibrator import PhysicsCalibrator, AtomStats, GameArchetype
from src.core.universe_physics import PhysicsProfile
from src.core.elemental_signature import (
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_INFORMATION,
    ATOM_AETHER, ATOM_WILL, ATOM_VOLATILITY, ATOM_FREQUENCY,
    ATOM_STABILITY, ATOM_FOCUS
)

class MockUnit:
    def __init__(self, dna, universal_stats=None):
        self.elemental_dna = dna
        self.universal_stats = universal_stats

class TestPhysicsCalibrator:
    
    def test_calculate_atom_distributions(self):
        units = [
            MockUnit({ATOM_MASS: 10, ATOM_ENERGY: 20}),
            MockUnit({ATOM_MASS: 20, ATOM_ENERGY: 20}),
            MockUnit({ATOM_MASS: 30, ATOM_ENERGY: 20}),
        ]
        
        dists = PhysicsCalibrator.calculate_atom_distributions(units)
        
        assert dists[ATOM_MASS].mean == 20.0
        assert dists[ATOM_MASS].min == 10.0
        assert dists[ATOM_MASS].max == 30.0
        assert dists[ATOM_ENERGY].mean == 20.0
        assert dists[ATOM_ENERGY].std == 0.0
        
    def test_detect_game_archetype_magic(self):
        # Magic Heavy: Mean Aether > 15
        dists = {
            ATOM_AETHER: AtomStats(mean=20.0)
        }
        arch = PhysicsCalibrator.detect_game_archetype(dists)
        assert arch.is_magic_heavy
        assert not arch.is_fast_paced
        
    def test_detect_game_archetype_attrition(self):
        # Attrition: Mass > 20 and Cohesion > 20
        dists = {
            ATOM_MASS: AtomStats(mean=25.0),
            ATOM_COHESION: AtomStats(mean=22.0)
        }
        arch = PhysicsCalibrator.detect_game_archetype(dists)
        assert arch.is_attrition_based
        
    def test_generate_multipliers_normalization(self):
        # Mean Mass 20.0 -> Default 10.0 / 20.0 = 0.5
        dists = {
            ATOM_MASS: AtomStats(mean=20.0, std=5.0)
        }
        arch = GameArchetype() # Neutral
        mults = PhysicsCalibrator.generate_multipliers(dists, arch)
        
        assert mults[ATOM_MASS] == pytest.approx(0.5)
        
    def test_generate_multipliers_clamping_and_std(self):
        # Low Mean (1.0) -> Multiplier 1.0 (negligible)
        # High Mean (100.0) -> 0.1 -> Clamped to 0.3
        # High Std (>15) -> Penalty
        dists = {
            ATOM_ENERGY: AtomStats(mean=1.0),
            ATOM_COHESION: AtomStats(mean=100.0), # Expect clamp 0.3
            ATOM_MASS: AtomStats(mean=10.0, std=20.0) # Expect 1.0 * 0.8 = 0.8
        }
        arch = GameArchetype()
        mults = PhysicsCalibrator.generate_multipliers(dists, arch)
        
        assert mults[ATOM_ENERGY] == 1.0
        assert mults[ATOM_COHESION] == 0.3
        assert mults[ATOM_MASS] == pytest.approx(0.8)

    def test_generate_multipliers_archetype_boost(self):
        # Magic archetype boosts Aether * 1.2
        dists = {
            ATOM_AETHER: AtomStats(mean=10.0) # Base mult 1.0
        }
        arch = GameArchetype(is_magic_heavy=True)
        mults = PhysicsCalibrator.generate_multipliers(dists, arch)
        
        assert mults[ATOM_AETHER] == pytest.approx(1.2)

    def test_calibrate_integration(self):
        units = [MockUnit({ATOM_MASS: 10}) for _ in range(10)]
        profile, meta = PhysicsCalibrator.calibrate(units, "TestVerse")
        
        assert isinstance(profile, PhysicsProfile)
        assert meta["universe"] == "TestVerse"
        assert meta["units_analyzed"] == 10
        # Mean 10 -> mult 1.0. 
        assert profile.multipliers[ATOM_MASS] == 1.0
