import pytest
from unittest.mock import MagicMock, patch
from src.mechanics.resource_mechanics import (
    ConvictionMechanic,
    BiomassMechanic,
    IndustrialMightMechanic
)

class TestResourceMechanics:
    
    # --- Conviction Tests ---
    def test_conviction_stack_mechanics(self):
        mech = ConvictionMechanic("Zealot Legions", {})
        faction = MagicMock()
        faction.name = "Zealot Legions"
        faction.conviction_stacks = 10
        faction.temp_modifiers = {}
        
        # 1. Kill (We kill Enemy)
        context = {
            "killer": faction,
            "faction": faction,
            "unit": MagicMock()
        }
        mech.on_unit_death(context)
        
        assert faction.conviction_stacks == 11
        assert faction.temp_modifiers["global_damage_mult"] == pytest.approx(1.0 + 0.055) # 11 * 0.005 = 0.055
        
        # 2. Decay
        mech.on_turn_start({"faction": faction})
        # 11 - 5 = 6
        assert faction.conviction_stacks == 6
        
    def test_conviction_morale_immune(self):
        mech = ConvictionMechanic("Zealot Legions", {})
        faction = MagicMock()
        faction.conviction_stacks = 60 # > 50
        
        context = {
            "faction": faction,
            "unit": MagicMock(),
            "is_immune": False
        }
        
        result = mech.on_morale_check(context)
        assert result is True
        assert context["is_immune"] is True

    # --- Biomass Tests ---
    def test_biomass_mechanics(self):
        mech = BiomassMechanic("Hive Swarm", {})
        faction = MagicMock()
        faction.name = "Hive Swarm"
        faction.biomass_pool = 100
        faction.requisition = 1000
        
        # 1. Gain Biomass on Death (Own Planet)
        planet = MagicMock()
        planet.owner = "Hive Swarm"
        unit = MagicMock()
        unit.cost = 100
        
        context = {
            "unit": unit,
            "faction": faction,
            "location": planet
        }
        mech.on_unit_death(context)
        
        # Gain 30% of 100 = 30
        assert faction.biomass_pool == 130
        
        # 2. Spend Biomass on Recruit (Refund)
        # Unit Cost 100. Max Discount 20% = 20.
        # Pool has 130. We can afford 20.
        context_recruit = {
            "unit": unit,
            "faction": faction
        }
        mech.on_unit_recruited(context_recruit)
        
        assert faction.biomass_pool == 110 # 130 - 20
        assert faction.requisition == 1020 # 1000 + 20 refund

    def test_biomass_decay(self):
        mech = BiomassMechanic("Hive Swarm", {})
        faction = MagicMock()
        faction.biomass_pool = 100
        
        mech.on_economy_phase({"faction": faction})
        assert faction.biomass_pool == 90 # 10% decay

    # --- Industrial Tests ---
    @patch("random.random")
    def test_industrial_queue_speedup(self, mock_random):
        mech = IndustrialMightMechanic("Iron Vanguard", {})
        
        planet = MagicMock()
        task1 = {'turns_left': 5}
        task2 = {'turns_left': 1} # Should not reduce below 1? Logic says > 1
        planet.construction_queue = [task1, task2]
        
        context = {"planet": planet}
        
        # Success (random < 0.25)
        mock_random.return_value = 0.1
        mech.on_building_constructed(context)
        
        assert task1['turns_left'] == 4
        assert task2['turns_left'] == 1 # Unchanged because logic > 1

