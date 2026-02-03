import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Adjust path to include src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet, DOCTRINE_CHARGE
from src.models.unit import Unit, Ship
from src.combat.combat_phases import OrbitalSupportPhase, ShootingPhase
import src.combat.combat_phases as phases_module

class TestRemainingFeatures(unittest.TestCase):

    def setUp(self):
        self.mock_planet = MagicMock()
        self.mock_planet.name = "TestPlanet"
        self.mock_planet.system = MagicMock()
        self.mock_planet.system.name = "TestSystem"

    def test_fleet_roles_and_capabilities(self):
        """Verify Fleet capability matrix correctly identifies Unit roles."""
        fleet = Fleet("F1", "Imperium", self.mock_planet)
        
        # Create units with different roles
        escort = MagicMock(spec=Ship, name="EscortUnit")
        escort.ship_class = "Escort"
        escort.is_alive.return_value = True
        escort.transport_capacity = 0
        escort.abilities = {}
        escort.traits = []
        
        capital = MagicMock(spec=Ship, name="CapitalUnit")
        capital.ship_class = "Battleship"
        capital.is_alive.return_value = True
        capital.transport_capacity = 0
        capital.abilities = {}
        capital.traits = []

        transport = MagicMock(spec=Ship, name="TransportUnit")
        transport.ship_class = "Transport" 
        transport.is_alive.return_value = True
        transport.transport_capacity = 50 
        transport.abilities = {}
        transport.traits = []

        scout = MagicMock(spec=Ship, name="ScoutUnit")
        scout.ship_class = "Escort"
        scout.is_alive.return_value = True
        scout.is_scout = True
        scout.abilities = {"Tags": ["Scout"]}
        scout.traits = []
        
        fleet.units = [escort, capital, transport, scout]
        
        # Invalidate cache to force recalc
        fleet.invalidate_caches()
        
        matrix = fleet.get_capability_matrix()
        
        # Assertions
        self.assertEqual(matrix["Battleship"], 1)
        
        # Logic Double Count Check:
        # 1. ship_class="Transport" -> matrix["Transport"] += 1
        # 2. capacity > 0 -> matrix["Transport"] += 1
        # Total = 2 for one transport ship.
        self.assertEqual(matrix["Transport"], 2) 
        
        # Scout logic:
        # 1. Tags "Scout" -> matrix["Scout"] += 1
        self.assertEqual(matrix["Scout"], 1)

    @patch('src.managers.combat.suppression_manager.SuppressionManager')
    def test_orbital_bombardment_phase(self, mock_suppression_manager):
        """Verify OrbitalSupportPhase logic."""
        phase = OrbitalSupportPhase()
        
        # Mock Context
        mock_manager = MagicMock()
        mock_location = MagicMock() # Planet
        mock_location.parent_planet = mock_location
        mock_location.is_province = True
        mock_manager.location = mock_location
        
        # Campaign Context to provide fleets
        mock_campaign = MagicMock()
        mock_manager.context = mock_campaign
        
        # Active Orbiting Fleet (Friendly)
        friendly_fleet = MagicMock()
        friendly_fleet.faction = "Imperium"
        friendly_fleet.location = mock_location
        friendly_fleet.is_destroyed = False
        
        mock_campaign.get_all_fleets.return_value = [friendly_fleet]
        
        # Armies on ground
        friendly_unit = MagicMock()
        friendly_unit.faction = "Imperium"
        friendly_unit.is_alive.return_value = True
        
        enemy_unit = MagicMock()
        enemy_unit.faction = "Orks"
        enemy_unit.is_alive.return_value = True
        # Fix: Return tuple for take_damage to avoid unpacking error if called
        # Fix: Mocks need compatible types for math if logic does checks
        enemy_unit.take_damage.return_value = (10, 0, 0, None) 
        enemy_unit.current_hp = 100
        enemy_unit.max_hp = 100
        enemy_unit.morale_current = 100
        
        mock_manager.armies_dict = {
            "Imperium": [friendly_unit],
            "Orks": [enemy_unit]
        }
        
        context = {
            "manager": mock_manager,
            "round_num": 1,
            "detailed_log_file": None
        }
        
        phase.execute(context)
        
        mock_campaign.get_all_fleets.assert_called()
        # Verify suppression was applied
        mock_suppression_manager.return_value.apply_suppression.assert_called()

    @patch('src.combat.combat_phases.random')
    def test_cover_destruction(self, mock_random):
        """Verify shooting phase calls damage_cover on grid."""
        phase = ShootingPhase()
        
        mock_grid = MagicMock()
        mock_grid.get_distance.return_value = 10
        mock_grid.damage_cover.return_value = "DESTROYED"
        
        # Attacker
        attacker = MagicMock(spec=Unit, name="Attacker")
        attacker.name = "Tank"
        attacker.faction = "Imperium"
        attacker.is_alive.return_value = True
        attacker.bs = 100 
        attacker.components = []
        attacker.formations = [] 
        
        # Ensure properties that might be accessed are set
        attacker.current_suppression = 0.0
        attacker.leadership = 10
        attacker.max_hp = 100
        attacker.current_hp = 100
        
        # Weapon
        weapon = MagicMock()
        weapon.type = "Weapon"
        weapon.is_destroyed = False
        weapon.weapon_stats = {"Range": 100, "Damage": 50, "Shots": 1} 
        attacker.components.append(weapon)
        
        # Target
        target = MagicMock(spec=Unit, name="Target")
        target.name = "Infantry"
        target.faction = "Orks"
        target.is_alive.return_value = True
        target.grid_x = 5
        target.grid_y = 5
        target.take_damage.return_value = (50, 0, 0, None)
        
        # Fix for TypeError:
        target.current_suppression = 0.0
        target.leadership = 7
        target.max_hp = 100
        target.current_hp = 100
        
        mock_tracker = MagicMock()
        mock_tracker.compute_nearest_enemies.return_value = {
            id(attacker): (id(target), 10)
        }
        
        # Setup context for Batch
        context = {
            "active_units": [(attacker, "Imperium"), (target, "Orks")],
            "enemies_by_faction": {"Imperium": [target], "Orks": [attacker]},
            "grid": mock_grid,
            "tracker": mock_tracker, 
            "gpu_tracker": mock_tracker,
            "faction_doctrines": {},
            "faction_metadata": {},
            "manager": MagicMock()
        }
        
        with patch.dict('sys.modules', {'src.combat.batch_shooting': MagicMock()}):
                 import src.combat.batch_shooting as mock_batch
                 
                 mock_batch.resolve_shooting_batch.return_value = [{
                     "attacker": attacker,
                     "target": target,
                     "damage": 50,
                     "is_hit": True,
                     "weapon": weapon,
                     "dist": 10
                 }]
                 
                 phase.execute(context)
                 
                 mock_grid.damage_cover.assert_called_with(target.grid_x, target.grid_y, 25)


if __name__ == '__main__':
    unittest.main()
