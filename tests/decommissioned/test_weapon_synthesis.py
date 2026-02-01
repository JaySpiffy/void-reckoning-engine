import pytest
from src.core.weapon_synthesizer import synthesize_weapon_stats
from src.data.weapon_data import get_weapon_stats
from src.core.elemental_signature import (
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_VOLATILITY, ATOM_FOCUS, ATOM_STABILITY, ATOM_FREQUENCY
)

class TestWeaponSynthesis:
    
    def test_synthesis_formulas_laser(self):
        """Test synthesis for a high energy laser weapon."""
        dna = {
            ATOM_ENERGY: 60.0,
            ATOM_FOCUS: 30.0,
            ATOM_STABILITY: 20.0,
            ATOM_FREQUENCY: 20.0,
            ATOM_MASS: 5.0
        }
        stats = synthesize_weapon_stats(dna)
        
        # Calculations:
        # Strength: (60*0.8) + (5*0.4) = 48 + 2 = 50 -> Scaled /10 = 5
        assert stats["S"] == 5
        
        # AP: (30*0.6) + (0*0.4) + (20*0.3) = 18 + 0 + 6 = 24 -> Scaled /10 = 2 -> -2
        assert stats["AP"] == -2
        
        # Range: (20*1.5) + (60*0.5) + (20*0.5) = 30 + 30 + 10 = 70 -> Scaled *0.5 = 35
        assert stats["Range"] == 35

    def test_synthesis_formulas_projectile(self):
        """Test synthesis for a projectile weapon."""
        dna = {
            ATOM_MASS: 40.0,
            ATOM_COHESION: 40.0, # Hardness
            ATOM_ENERGY: 20.0,   # Kinetic
            ATOM_VOLATILITY: 10.0
        }
        stats = synthesize_weapon_stats(dna)
        
        # Strength: (20*0.8) + (40*0.4) = 16 + 16 = 32 -> 3
        assert stats["S"] == 3
        
        # AP: (0*0.6) + (40*0.4) = 16 -> 1 -> -1
        assert stats["AP"] == -1
        
        # Range: (0*1.5) + (20*0.5) = 10 -> 5 -> Min 12
        assert stats["Range"] == 12

    def test_data_integration_atomic(self):
        """Test retrieving a blueprint weapon via get_weapon_stats."""
        # Ensure registry is loaded
        name = "Standard Laser Weapon"
        stats = get_weapon_stats(name)
        
        # Check source flag
        assert stats.get("dna_source")
        assert stats["Type"] == "Atomic Weapon"
        assert stats["S"] == 5

    def test_data_integration_legacy(self):
        """Test fallback to legacy weapon."""
        # name = "Lasgun" # Should define as S3 AP0 D1 Range 24? Default S4 usually if not found
        # In legacy weapon_db.json if exists? Or fallback logic.
        # Check standard fallback return
        stats = get_weapon_stats("NonExistentLegacyWeapon")
        assert stats["S"] == 4
        assert not stats.get("dna_source", False)
