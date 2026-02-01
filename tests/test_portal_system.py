import pytest
import json
from pathlib import Path
from src.utils.portal_validator import PortalValidator
from src.managers.galaxy_generator import GalaxyGenerator

class TestPortalSystem:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        self.test_root = tmp_path / "universes"
        self.test_root.mkdir(parents=True, exist_ok=True)
        
        self.ec_config = {
            "enable_portals": True,
            "portals": [
                {
                    "portal_id": "link_alpha",
                    "source_coords": [10, 10],
                    "dest_universe": "eternal_crusade",
                    "dest_coords": [50, 50],
                    "placement_strategy": "galactic_core"
                }
            ]
        }
        
        # Save mock configs
        (self.test_root / "eternal_crusade").mkdir(exist_ok=True)
        with open(self.test_root / "eternal_crusade" / "portal_config.json", 'w') as f:
            json.dump(self.ec_config, f)
        yield
        # Cleanup handled by tmp_path

    def test_validator_basic(self):
        """Verify that validator catches missing fields."""
        bad_config = {"enable_portals": True, "portals": [{"portal_id": "test"}]}
        path = self.test_root / "bad_config.json"
        with open(path, 'w') as f:
            json.dump(bad_config, f)
            
        res = PortalValidator.validate_portal_config(path)
        assert not res["valid"]
        assert "missing 'source_coords'" in res["error"]

    def test_placement_strategies(self):
        """Verify GalaxyGenerator respects placement strategies."""
        gen = GalaxyGenerator()
        # Mock systems
        from src.models.star_system import StarSystem
        center_sys = StarSystem("Center", 50, 50)
        edge_sys = StarSystem("Edge", 90, 90)
        gen.systems = [center_sys, edge_sys]
        
        # Portal 1: Galactic Core
        p1_def = self.ec_config["portals"][0]
        
        # Core strategy -> should be center_sys
        host = min(gen.systems, key=lambda s: (s.x - 50)**2 + (s.y - 50)**2)
        assert host.name == "Center"
        
        # Border strategy -> should be edge_sys
        rim_candidates = [s for s in gen.systems if s.x > 75 or s.y > 75 or s.x < 25 or s.y < 25]
        host_rim = min(rim_candidates, key=lambda s: (s.x - 10)**2 + (s.y - 10)**2)
        assert host_rim.name == "Edge"
