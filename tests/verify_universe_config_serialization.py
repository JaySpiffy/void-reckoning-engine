import sys
import os
import unittest
from pathlib import Path

sys.path.append(os.getcwd())

from universes.base.universe_config import UniverseConfig

class TestUniverseConfigSerialization(unittest.TestCase):
    def test_to_dict_includes_factions(self):
        # Create a dummy config
        config = UniverseConfig(
            universe_name="TestUniverse",
            universe_version="1.0",
            universe_root=Path("."),
            metadata={"factions": ["FactionA", "FactionB"]}
        )
        
        # Serialize
        data = config.to_dict()
        
        # Verify 'factions' key exists and is correct
        self.assertIn("factions", data, "'factions' key missing from to_dict output")
        self.assertEqual(data["factions"], ["FactionA", "FactionB"], "Factions list mismatch")
        print("PASS: UniverseConfig.to_dict() correctly includes 'factions'.")

if __name__ == "__main__":
    unittest.main()
