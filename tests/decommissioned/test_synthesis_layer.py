import pytest
from typing import Dict
from src.core.elemental_signature import (
    get_default_elemental_signature,
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_INFORMATION,
    ATOM_AETHER, ATOM_WILL, ATOM_VOLATILITY, ATOM_FREQUENCY,
    ATOM_STABILITY, ATOM_FOCUS
)
from src.core.universal_stats import (
    VALID_METRICS,
    PHYSICAL_KINETIC_FORCE, HULL_STRUCTURAL_INTEGRITY, WEAPON_ACCURACY_RATING,
    PSYKER_POWER_LEVEL, MOBILITY_SPEED_TACTICAL, PHYSICAL_MASS, ENERGY_THERMAL_OUTPUT
)
from src.core.synthesis_layer import synthesize_universal_stats
from src.models.unit import Unit
from unittest.mock import patch

class TestSynthesisLayer:

    def test_zero_signature(self):
        """Test Case 1: All atoms at 0.0 should produce baseline values."""
        sig = get_default_elemental_signature()
        stats = synthesize_universal_stats(sig)
        
        assert len(stats) == len(VALID_METRICS)
        # Accuracy baseline is now 0.0 (no offset)
        assert stats[WEAPON_ACCURACY_RATING] == 0.0
        # Morale baseline is 30
        assert stats["crew_morale_base"] == 30.0
        # Most others should be 0 or baselines
        for k, v in stats.items():
            assert v >= 0.0, f"Metric {k} produced negative value: {v}"

    def test_single_atom_dominance(self):
        """Test Case 2: High Mass should elevate mass-dependent stats."""
        sig = get_default_elemental_signature()
        sig[ATOM_MASS] = 100.0
        stats = synthesize_universal_stats(sig)
        
        assert stats["physical_mass"] == 10000.0 # 100 * 100
        # Energy is 0, so kinetic force should be 0
        assert stats[PHYSICAL_KINETIC_FORCE] == 0.0
        # Stealth should be low (100-100)*...
        assert stats["stealth_rating"] == 0.0

    def test_balanced_signature(self):
        """Test Case 3: All atoms at 10.0 (Balanced Budget)."""
        sig = {atom: 10.0 for atom in get_default_elemental_signature()}
        stats = synthesize_universal_stats(sig)
        
        for k, v in stats.items():
            assert v > 0.0, f"Metric {k} is zero in balanced signature"
            assert not (float('inf') == v or float('nan') == v)

    def test_white_paper_lasgun(self):
        """Test Case 4a: Lasgun (High Energy/Freq, Low Mass)."""
        sig = get_default_elemental_signature()
        sig[ATOM_ENERGY] = 40.0
        sig[ATOM_FREQUENCY] = 30.0
        sig[ATOM_MASS] = 2.0
        sig[ATOM_STABILITY] = 20.0
        sig[ATOM_INFORMATION] = 10.0
        
        stats = synthesize_universal_stats(sig)
        
        # Lasgun should have good range and energy damage
        assert stats["weapon_range_effective"] > 0
        assert stats["weapon_energy_damage"] > stats["weapon_kinetic_damage"]
        assert stats["shield_absorption_rate"] > 0

    def test_white_paper_knight(self):
        """Test Case 4b: Medieval Knight (High Mass/Cohesion, Zero Energy)."""
        sig = get_default_elemental_signature()
        sig[ATOM_MASS] = 30.0
        sig[ATOM_COHESION] = 40.0
        sig[ATOM_WILL] = 20.0
        
        stats = synthesize_universal_stats(sig)
        
        assert stats[HULL_STRUCTURAL_INTEGRITY] > 0
        assert stats["armor_kinetic_resistance"] > 0
        assert stats["weapon_energy_damage"] == 0
        assert stats["shield_absorption_rate"] == 0

    def test_white_paper_gandalf(self):
        """Test Case 4c: Gandalf's Staff (High Aether/Focus, Low Volatility)."""
        sig = get_default_elemental_signature()
        sig[ATOM_AETHER] = 50.0
        sig[ATOM_FOCUS] = 40.0
        sig[ATOM_WILL] = 30.0
        
        stats = synthesize_universal_stats(sig)
        
        assert stats[PSYKER_POWER_LEVEL] > 0
        assert stats["warp_capability"] > 0
        assert stats["leadership_rating"] > 40 # 30*1.4*0.5 + 30 = 21+30=51

    def test_output_validation(self):
        """Test Case 6: Verify output types and set membership."""
        sig = {atom: 1.0 for atom in get_default_elemental_signature()}
        stats = synthesize_universal_stats(sig)
        
        for k, v in stats.items():
            assert k in VALID_METRICS
            assert isinstance(v, float)
            assert not float('nan') == v
            assert not float('inf') == v

    def test_integration_unit_model(self):
        """Test Case 7: Verify synthesized stats can be applied to a Unit."""
        sig = get_default_elemental_signature()
        sig[ATOM_MASS] = 50.0
        sig[ATOM_COHESION] = 40.0
        sig[ATOM_ENERGY] = 50.0
        sig[ATOM_STABILITY] = 20.0
        sig[ATOM_INFORMATION] = 20.0
        
        stats = synthesize_universal_stats(sig)
        
        # Create a blank unit
        unit = Unit("Test Golem", ma=0, md=0, hp=0, armor=0, damage=0, abilities={})
        unit.universal_stats = stats
        
        # Map stats to legacy
        unit.apply_dna_to_legacy()
        
        # Verify legacy stats are populated
        assert unit.base_hp > 0
        assert unit.armor > 0
        assert unit.base_damage > 0
        assert unit.bs > 0
        assert unit.movement_points > 0

    def test_negative_signature(self):
        """Test Case 8: Verify negative atoms are normalized to 0."""
        sig = get_default_elemental_signature()
        sig[ATOM_MASS] = -50.0
        sig[ATOM_ENERGY] = 10.0
        
        stats = synthesize_universal_stats(sig)
        
        # Mass should be treated as 0
        assert stats[PHYSICAL_MASS] == 0.0
        # Energy should still work
        assert stats[ENERGY_THERMAL_OUTPUT] > 0.0

    def test_calculate_ability_effect(self):
        """Test Case 9: Verify ability effect delegation."""
        from src.core.synthesis_layer import calculate_ability_effect
        
        # Mock the PayloadRegistry to verify delegation
        with patch('src.core.payload_registry.PayloadRegistry') as MockRegistry:
            instance = MockRegistry.get_instance.return_value
            instance.execute_payload.return_value = {"damage": 50}
            
            sig = get_default_elemental_signature()
            effect = calculate_ability_effect("LASER_BEAM", sig, sig)
            
            assert effect["damage"] == 50
            instance.execute_payload.assert_called_once()

