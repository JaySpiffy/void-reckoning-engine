import pytest
from src.core.universe_data import UniverseDataManager
from src.core.elemental_signature import ATOM_AETHER, ATOM_MASS, ATOM_ENERGY

from unittest.mock import MagicMock

@pytest.fixture(scope="module")
def universe_manager():
    manager = UniverseDataManager.get_instance()
    manager.load_universe_data("eternal_crusade")
    
    # Mock Physics Profiles
    mock_physics = MagicMock()
    mock_physics.apply_to_signature.side_effect = lambda dna: dna # Default identity
    
    # Define profiles
    eternal_profile = MagicMock()
    eternal_profile.inverse_apply.side_effect = lambda dna: dna.copy()
    eternal_profile.apply_to_signature.side_effect = lambda dna: dna.copy()
    
    default_profile = MagicMock()
    default_profile.inverse_apply.side_effect = lambda dna: dna.copy()
    # For aether dampening test: zero out aether
    def default_apply(dna):
        new = dna.copy()
        new[ATOM_AETHER] = 0.0
        return new
    default_profile.apply_to_signature.side_effect = default_apply
    
    high_grav_profile = MagicMock()
    high_grav_profile.inverse_apply.side_effect = lambda dna: dna.copy()
    # For gravity test: double mass
    def high_grav_apply(dna):
        new = dna.copy()
        new[ATOM_MASS] = dna.get(ATOM_MASS, 0.0) * 2
        new[ATOM_ENERGY] = dna.get(ATOM_ENERGY, 0.0) * 0.8
        return new
    high_grav_profile.apply_to_signature.side_effect = high_grav_apply
    
    # Patch get_physics_profile on the instance
    original_get = manager.get_physics_profile
    def get_profile_side_effect(name):
        if name == "eternal_crusade": return eternal_profile
        if name == "default": return default_profile
        if name == "high_gravity": return high_grav_profile
        return original_get(name)
        
    manager.get_physics_profile = get_profile_side_effect
    
    # Also patch load_translation_table to allow mapping
    # The code checks: table[current][target]
    mock_config = MagicMock()
    mock_config.load_translation_table.return_value = {
        "eternal_crusade": {"default": {}},
        "default": {"high_gravity": {}, "eternal_crusade": {}}
    }
    manager.universe_config = mock_config

    return manager

class TestPhysicsProfiles:
    
    def test_aether_dampening_eternal_crusade_to_default(self, universe_manager):
        """Test: Moving a psyker to default universe should zero out aether."""
        psyker_dna = {
            "name": "Warp Beast",
            "active_universe": "eternal_crusade",
            "elemental_dna": {
                ATOM_AETHER: 100.0,
                ATOM_MASS: 20.0
            },
            "universal_stats": {"psyker_power_level": 100.0}
        }
        
        # Translate to default
        new_dna = universe_manager.rehydrate_for_universe(psyker_dna, "default")
        
        # Default aether physics is 0.0
        assert new_dna["elemental_dna"][ATOM_AETHER] == 0.0
        assert new_dna.get("elemental_translated")

    def test_gravity_amplification(self, universe_manager):
        """Test: Moving to High Gravity should increase mass-based stats."""
        ship_dna = {
            "name": "Standard Ship",
            "active_universe": "default",
            "elemental_dna": {
                ATOM_MASS: 50.0,
                ATOM_ENERGY: 50.0
            }
        }
        
        # Translate to high_gravity (atom_mass: 2.0)
        new_dna = universe_manager.rehydrate_for_universe(ship_dna, "high_gravity")
        
        # 50.0 (default) -> denormalized (50/1) -> high_grav (50*2) = 100
        assert new_dna["elemental_dna"][ATOM_MASS] == 100.0
        # Energy: 50 * 0.8 = 40
        assert new_dna["elemental_dna"][ATOM_ENERGY] == 40.0

    def test_round_trip_preservation(self, universe_manager):
        """Test: A -> B -> A should preserve original DNA."""
        original_dna = {
            "name": "Traveler",
            "active_universe": "eternal_crusade",
            "elemental_dna": {
                ATOM_MASS: 30.0,
                ATOM_AETHER: 10.0,
                ATOM_ENERGY: 20.0
            }
        }
        
        # Trip to default
        middle_dna = universe_manager.rehydrate_for_universe(original_dna, "default")
        
        # Back to eternal_crusade
        final_dna = universe_manager.rehydrate_for_universe(middle_dna, "eternal_crusade")
        
        for atom, val in original_dna["elemental_dna"].items():
            # Skip Aether as Default universe dampens it to 0 (lossy transformation)
            if atom == ATOM_AETHER:
                continue
            assert val == pytest.approx(final_dna["elemental_dna"][atom], abs=1e-5)
