
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.managers.economy.insolvency_handler import InsolvencyHandler
from src.managers.economy.budget_allocator import BudgetAllocator
from src.services.recruitment_service import RecruitmentService
from src.models.unit import Unit, Ship
from src.models.fleet import Fleet
from src.models.army import ArmyGroup
from src.core.constants import ORBIT_DISCOUNT_MULTIPLIER

class TestEconomyStabilization(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_engine.logger = MagicMock()
        self.mock_engine.telemetry = MagicMock()
        
    def test_insolvency_prioritizes_effective_upkeep(self):
        """Verify that InsolvencyHandler targets units that actually cost money first."""
        handler = InsolvencyHandler(self.mock_engine)
        
        # 1. Setup Mock Faction in Debt
        mock_faction = MagicMock()
        mock_faction.requisition = -5000
        
        # 2. Setup Units
        # Unit A: High upkeep, but FREE (Garrisoned)
        # Unit B: Low upkeep, but PAID (In Transit)
        unit_free = MagicMock(spec=Unit)
        unit_free.name = "FreeWarrior"
        unit_free.upkeep = 100
        unit_free.cost = 1000
        
        unit_paid = MagicMock(spec=Unit)
        unit_paid.name = "PaidSoldier"
        unit_paid.upkeep = 10 # Effective 10
        unit_paid.cost = 100

        # 3. Setup Containers
        # Planet with capacity 1 (Unit A is free)
        p1 = MagicMock()
        p1.name = "Bastion"
        p1.garrison_capacity = 1
        p1.node_reference = "node_p1"
        
        ag_free = ArmyGroup("ag1", "test_f", [unit_free], p1)
        
        p1.armies = [ag_free]
        
        # Fleet not in orbit (Unit B is paid)
        f1 = Fleet("f1", "test_f", p1)
        f1.destination = MagicMock() # Force not in orbit
        f1.units = [unit_paid]
        f1.cargo_armies = []
        f1.is_destroyed = False
        
        self.mock_engine.planets_by_faction = {"test_f": [p1]}
        self.mock_engine.fleets_by_faction = {"test_f": [f1]}
        self.mock_engine.get_planet.return_value = p1
        
        # Standard Income
        income = 100
        upkeep = 150 # Deficit
        
        # 4. Run Insolvency
        # We need to make sure handle_insolvency doesn't exit early
        with patch('src.managers.economy.insolvency_handler.bal') as mock_bal:
            mock_bal.MAINT_CAP_NAVY = 0.125
            mock_bal.MAINT_CAP_ARMY = 0.125
            mock_bal.MAINT_CAP_INFRA = 0.125
            
            handler.handle_insolvency("test_f", mock_faction, [f1], income, upkeep)
        
        # 5. Assertions
        # PaidSoldier should be removed (Effective 10 > 0)
        # FreeWarrior should NOT be removed (Effective 0)
        
        # Check if unit removed from container
        self.assertNotIn(unit_paid, f1.units)
        
        # Verify it didn't remove the free unit
        self.assertIn(unit_free, ag_free.units)
        
    def test_budget_forfeiture_to_debt(self):
        """Verify that BudgetAllocator pulls from buckets to pay debt."""
        alloc = BudgetAllocator(self.mock_engine, MagicMock(), MagicMock(), None)
        
        mock_faction = MagicMock()
        mock_faction.requisition = -2000
        mock_faction.budgets = {"navy": 500, "construction": 1000}
        
        econ_data = {
            "income": 0,
            "upkeep": 0,
            "margin": 0,
            "active_mode": {"name": "WAR", "budget": {"construction": 1, "research": 0, "recruitment": 0}}
        }
        
        self.mock_engine.planets_by_faction = {"test_f": []}
        
        alloc.execute_budget("test_f", mock_faction, econ_data)
        
        # Budgets should be 0
        self.assertEqual(mock_faction.budgets["navy"], 0)
        self.assertEqual(mock_faction.budgets["construction"], 0)
        
        # Requisition should have recovered by 1500
        # -2000 + 1500 = -500
        self.assertEqual(mock_faction.requisition, -500)

    def test_recruitment_debt_protection(self):
        """Verify that recruitment is blocked if requisition is negative."""
        service = RecruitmentService(self.mock_engine)
        
        mock_faction = MagicMock()
        mock_faction.requisition = -100
        mock_faction.get_modifier.return_value = 1.0
        
        # Should return 0 spent immediately
        spent = service.process_fleet_commissioning("test_f", mock_faction, [MagicMock()], 5000)
        self.assertEqual(spent, 0)
        
        # Check that it didn't even try to create_fleet
        self.mock_engine.create_fleet.assert_not_called()

if __name__ == '__main__':
    unittest.main()
