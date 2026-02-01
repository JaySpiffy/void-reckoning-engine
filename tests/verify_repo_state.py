import sys
import os
import unittest
from unittest.mock import MagicMock

# Add src and root to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from src.repositories.planet_repository import PlanetRepository
from src.managers.galaxy_state_manager import GalaxyStateManager
from src.managers.asset_manager import AssetManager
from src.models.planet import Planet
from src.core.service_locator import ServiceLocator

class TestRepositoryRefactor(unittest.TestCase):
    def setUp(self):
        # Reset Locator
        ServiceLocator._services = {}
        
        # Patch UDM that Planet uses
        self.udm_patcher = unittest.mock.patch('src.models.planet.UniverseDataManager')
        self.mock_udm_cls = self.udm_patcher.start()
        self.mock_udm_inst = self.mock_udm_cls.get_instance.return_value
        self.mock_udm_inst.get_planet_classes.return_value = {
            "Terran": {
                "req_mod": 1.0, 
                "def_mod": 0, 
                "slots": 5
            }
        }
        
        # 1. Setup Repo
        self.repo = PlanetRepository()
        ServiceLocator.register("PlanetRepository", self.repo)
        
        # 2. Setup Galaxy Manager (uses Locator to get Repo)
        self.galaxy_mgr = GalaxyStateManager(None, None)
        
        # 3. Mock Engine
        self.engine = MagicMock()
        self.engine.galaxy_manager = self.galaxy_mgr
        # Engine should also expose planets_by_faction using the new property delegation usually
        # But here we are testing if AssetManager updates Repo correctly.
        
        # 4. Setup AssetManager
        self.asset_mgr = AssetManager(self.engine)
        # Inject asset manager back to engine if needed (circular dep usually)
        self.engine.asset_manager = self.asset_mgr
        
    def test_ownership_flow(self):
        print("\n=== Testing Planet Ownership Flow (Unit Test) ===")
        
        # 1. Create Planet
        p1 = Planet("Planet A", None, 0)
        p1.owner = "Neutral"
        
        # 2. Save directly to Repo (Simulating Galaxy Generation)
        self.repo.save(p1)
        
        # Verify Index
        index = self.repo.get_ownership_index()
        self.assertIn("Neutral", index)
        self.assertIn(p1, index["Neutral"])
        
        # 3. Change Ownership via AssetManager
        print(f"Update ownership: Neutral -> Imperium")
        self.asset_mgr.update_planet_ownership(p1, "Imperium")
        
        # 4. Verify Repo Index Updated
        index = self.repo.get_ownership_index()
        self.assertIn("Imperium", index)
        self.assertIn(p1, index["Imperium"])
        self.assertNotIn(p1, index.get("Neutral", []))
        
        print("Planet correctly moved in Repository Index.")
        
        # 5. Verify Object Updated
        self.assertEqual(p1.owner, "Imperium")

    def tearDown(self):
        self.udm_patcher.stop()

if __name__ == '__main__':
    unittest.main()
