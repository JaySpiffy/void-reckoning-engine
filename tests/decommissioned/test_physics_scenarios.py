import pytest
from unittest.mock import MagicMock, patch
from src.core.elemental_signature import ATOM_MASS, ATOM_ENERGY, ATOM_AETHER, ATOM_WILL, ATOM_COHESION
from src.core.universe_physics import PhysicsProfile
from src.core.universe_data import UniverseDataManager

class TestPhysicsScenarios:
    
    @pytest.fixture
    def physics_profiles(self):
        # Science Universe: Low Aether/Will
        sci_multipliers = {
            ATOM_MASS: 1.0,
            ATOM_ENERGY: 1.0,
            ATOM_AETHER: 0.01,
            ATOM_WILL: 0.1
        }
        
        # Warp Universe: High Aether/Will, Fluid Mass
        warp_multipliers = {
            ATOM_MASS: 0.5,
            ATOM_ENERGY: 1.5,
            ATOM_AETHER: 3.0,
            ATOM_WILL: 2.0
        }
        
        return {
            "Terra": PhysicsProfile(sci_multipliers, "Scientific Reality"),
            "Warp": PhysicsProfile(warp_multipliers, "The Warp")
        }

    @pytest.fixture
    def unit_dnas(self):
        # Lasgun: Tech-based, Mass/Energy high
        lasgun = {
            "name": "Lasgun Battery",
            "elemental_dna": {
                ATOM_MASS: 30.0,
                ATOM_ENERGY: 40.0,
                ATOM_COHESION: 30.0,
                ATOM_AETHER: 0.0,
                ATOM_WILL: 0.0
            },
            "source_universe": "Standard" # Assuming Standard is 1.0 baseline
        }
        
        # Gandalf: Magic-based, Aether/Will high
        gandalf = {
            "name": "Grey Wizard",
            "elemental_dna": {
                ATOM_MASS: 10.0,
                ATOM_ENERGY: 10.0,
                ATOM_COHESION: 10.0,
                ATOM_AETHER: 50.0,
                ATOM_WILL: 20.0
            },
            "source_universe": "Standard"
        }
        
        return {"lasgun": lasgun, "gandalf": gandalf}

    def test_physics_translation_logic(self, physics_profiles, unit_dnas):
        """
        Verifies that rehydrating/translating unit DNA applies correct physics multipliers.
        This reproduces the 'Lasgun vs Gandalf' sanity check logic using the actual Engine class.
        """
        # Mock UniverseDataManager to return our profiles
        with patch.object(UniverseDataManager, 'get_instance', return_value=MagicMock()) as mock_get:
            manager = UniverseDataManager()
            
            # Setup mock behavior for get_physics_profile
            # We assume "Standard" is baseline 1.0 (default profile has all 1.0)
            base_profile = PhysicsProfile()
            
            def get_profile_side_effect(name):
                if name == "Terra": return physics_profiles["Terra"]
                if name == "Warp": return physics_profiles["Warp"]
                return base_profile
                
            manager.get_physics_profile = MagicMock(side_effect=get_profile_side_effect)
            
            # Fix: rehydrate_for_universe requires universe_config to be set
            manager.universe_config = MagicMock()
            manager.universe_config.load_translation_table.return_value = {} # Empty table triggers fallback but continues to physics
            
            # Allow access to manager.rehydrate_for_universe (it's an instance method)
            # We need to call the REAL method, but with mocked get_physics_profile
            # We can use the real instance since we just mocked one method on it
            
            # --- Scenario 1: Terra (Science) ---
            # Translate Lasgun to Terra
            lasgun_terra_dna = manager.rehydrate_for_universe(unit_dnas["lasgun"], "Terra")
            lasgun_terra_sig = lasgun_terra_dna["elemental_dna"]
            
            # Translate Gandalf to Terra
            gandalf_terra_dna = manager.rehydrate_for_universe(unit_dnas["gandalf"], "Terra")
            gandalf_terra_sig = gandalf_terra_dna["elemental_dna"]
            
            # Verify Scaling
            # Lasgun Energy in Terra: 40 * 1.0 = 40
            assert lasgun_terra_sig[ATOM_ENERGY] == pytest.approx(40.0)
            
            # Gandalf Aether in Terra: 50 * 0.01 = 0.5
            assert gandalf_terra_sig[ATOM_AETHER] == pytest.approx(0.5)
            
            # Determine "Power" (Simple Sum for test metric)
            lasgun_power_terra = lasgun_terra_sig[ATOM_ENERGY] + lasgun_terra_sig[ATOM_AETHER]
            gandalf_power_terra = gandalf_terra_sig[ATOM_ENERGY] + gandalf_terra_sig[ATOM_AETHER]
            
            # Tech should dominate in Science
            assert lasgun_power_terra > gandalf_power_terra
            print(f"\nTerra Power: Lasgun={lasgun_power_terra}, Gandalf={gandalf_power_terra}")

            # --- Scenario 2: The Warp (Magic) ---
            # Translate Lasgun to Warp
            lasgun_warp_dna = manager.rehydrate_for_universe(unit_dnas["lasgun"], "Warp")
            lasgun_warp_sig = lasgun_warp_dna["elemental_dna"]
            
            # Translate Gandalf to Warp
            gandalf_warp_dna = manager.rehydrate_for_universe(unit_dnas["gandalf"], "Warp")
            gandalf_warp_sig = gandalf_warp_dna["elemental_dna"]
            
            # Verify Scaling
            # Lasgun Energy in Warp: 40 * 1.5 = 60
            # Lasgun Aether in Warp: 0 * 3.0 = 0
            assert lasgun_warp_sig[ATOM_ENERGY] == pytest.approx(60.0)
            
            # Gandalf Aether in Warp: 50 * 3.0 = 150
            assert gandalf_warp_sig[ATOM_AETHER] == pytest.approx(150.0)
            
            # Determine "Power"
            lasgun_power_warp = lasgun_warp_sig[ATOM_ENERGY] + lasgun_warp_sig[ATOM_AETHER]
            gandalf_power_warp = gandalf_warp_sig[ATOM_ENERGY] + gandalf_warp_sig[ATOM_AETHER]
            
            # Magic should OBLITERATE in Warp
            assert gandalf_power_warp > lasgun_power_warp
            print(f"Warp Power: Lasgun={lasgun_power_warp}, Gandalf={gandalf_power_warp}")

