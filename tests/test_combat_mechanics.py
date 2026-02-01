import pytest
from unittest.mock import MagicMock, patch
from src.mechanics.combat_mechanics import (
    ReanimationProtocolsMechanic, 
    AetherOverloadMechanic, 
    InstabilityMechanic, 
    EternalMechanic,
    FurorMechanic
)

class TestCombatMechanics:
    
    @patch("random.random")
    def test_reanimation_protocols(self, mock_random):
        mech = ReanimationProtocolsMechanic("Cyber Synod", {})
        mech.get_modifier = MagicMock(return_value=0.5) # 50% chance
        
        unit = MagicMock()
        unit.max_hp = 100
        unit.current_hp = 0
        faction = MagicMock()
        faction.stats = {}
        
        context = {"unit": unit, "faction": faction}
        
        # Case 1: Success (random < 0.5)
        mock_random.return_value = 0.3
        mech.on_unit_death(context)
        
        assert context.get("revived") is True
        assert unit.current_hp == 25 # 25% heal
        assert faction.stats["reanimations_this_turn"] == 1
        
        # Case 2: Failure (random > 0.5)
        mock_random.return_value = 0.8
        context["revived"] = False # Reset
        unit.current_hp = 0
        mech.on_unit_death(context)
        
        assert context.get("revived") is False
        assert unit.current_hp == 0

    @patch("random.random")
    def test_aether_overload(self, mock_random):
        mech = AetherOverloadMechanic("Ascended Order", {})
        
        caster = MagicMock()
        caster.elemental_dna = {"atom_stability": 10.0}
        caster.current_hp = 100
        
        ability = {
            "elemental_dna": {"atom_aether": 50.0},
            "payload": {"damage": 200}
        }
        
        context = {"caster": caster, "ability": ability}
        
        # Fail Chance ~ (50/100) * (1 - 0.1) = 0.5 * 0.9 = 0.45
        
        # Case 1: Trigger (random < fail_chance)
        mock_random.return_value = 0.1
        mech.on_ability_use(context)
        
        assert context.get("overload_triggered") is True
        # Damage should be 200 * 0.5 = 100
        assert caster.current_hp == 0 # 100 - 100
        
        # Case 2: No Trigger
        mock_random.return_value = 0.9
        context["overload_triggered"] = False
        mech.on_ability_use(context)
        assert context.get("overload_triggered") is False

    @patch("random.random")
    def test_instability(self, mock_random):
        mech = InstabilityMechanic("Rift Daemons", {})
        
        # Setup Mock Engine Loop
        engine = MagicMock()
        faction = MagicMock()
        faction.name = "Rift Daemons"
        
        unit = MagicMock()
        unit.elemental_dna = {"atom_volatility": 50}
        
        fleet = MagicMock()
        fleet.faction = "Rift Daemons"
        fleet.units = [unit]
        
        engine.fleets = [fleet]
        # Skip planets for simplicity
        del engine.all_planets
        
        context = {"faction": faction, "engine": engine}
        
        # Case 1: Phase Out (random < 0.5)
        mock_random.return_value = 0.2
        mech.on_turn_start(context)
        assert unit.is_phased is True
        
        # Case 2: Phase In
        mock_random.return_value = 0.8
        mech.on_turn_start(context)
        assert unit.is_phased is False

    @patch("random.random")
    def test_eternal(self, mock_random):
        mech = EternalMechanic("Ancient Guardians", {})
        
        # --- on_unit_death ---
        unit = MagicMock()
        unit.max_hp = 100
        unit.current_hp = 0
        unit.is_dormant = False
        
        context = {"unit": unit}
        mech.on_unit_death(context)
        
        assert context["cancel_death"] is True
        assert unit.is_dormant is True
        assert unit.current_hp == 1
        
        # --- on_turn_start (Regen) ---
        engine = MagicMock()
        faction = MagicMock()
        faction.name = "Ancient Guardians"
        
        fleet = MagicMock()
        fleet.faction = "Ancient Guardians"
        fleet.units = [unit]
        engine.fleets = [fleet]
        
        context_turn = {"faction": faction, "engine": engine}
        
        # Success (random < 0.3)
        mock_random.return_value = 0.1
        mech.on_turn_start(context_turn)
        
        assert unit.is_dormant is False
        assert unit.current_hp == 50 # 50% max

    def test_furor_economy(self):
        mech = FurorMechanic("ScrapLord_Marauders", {})
        mech.get_modifier = MagicMock(return_value=0.1) # Generic 0.1 return
        
        faction = MagicMock()
        faction.temp_modifiers = {}
        context = {"faction": faction}
        
        mech.on_economy_phase(context)
        
        # recruitment_cost_mult = 1.0 + 0.1 => 1.1?
        # Logic in code: faction.temp_modifiers["recruitment_cost_mult"] = 1.0 + self.get_modifier("recruitment_cost", 0.0)
        # get_modifier here mocked to 0.1
        assert faction.temp_modifiers["recruitment_cost_mult"] == 1.1
        assert faction.temp_modifiers["melee_damage_mult"] == 1.1 # Same mock return

