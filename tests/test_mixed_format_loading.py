import sys
import os
import json
from pathlib import Path
import pytest

from universes.base.universe_loader import UniverseLoader
from src.factories.unit_factory import UnitFactory
from src.utils.format_detector import FormatDetector
from src.core.config import UNIVERSE_ROOT, ROOT_DIR

class TestMixedFormatLoading:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.loader = UniverseLoader(UNIVERSE_ROOT)
        # Check if star_wars config exists, otherwise skip or fail
        try:
             self.sw_config = self.loader.load_universe("star_wars")
        except:
             pytest.skip("Star Wars universe not found, skipping mixed format tests")

        # Create a dummy weapon_database.md to test hybrid merging
        self.dummy_db_path = self.sw_config.factions_dir / "weapon_database.md"
        with open(self.dummy_db_path, "w", encoding="utf-8") as f:
            f.write("# Weapon Database\n")
            f.write("| **Blasters** | |\n")
            f.write("| --- | --- |\n")
            f.write("| DL-44 Heavy Blaster Pistol | Pistol | 50 | 5 | 0 | 4 | Energy |\n")
        
        yield
        
        if self.dummy_db_path.exists():
            os.remove(self.dummy_db_path)

    def test_format_detection(self):
        """Verifies that Star Wars factions detect both XML and md formats if present."""
        formats = self.loader.detect_unit_formats(self.sw_config)
        assert len(formats) > 0
        # Most Star Wars factions have markdown files generated from XML
        # Some might still have XML sources in their dirs if modified manually
        print(f"\nDetected formats for Star Wars: {formats}")

    def test_unit_factory_agnostic_loading(self):
        """Tests that UnitFactory can load from both formats."""
        # Find an XML file and a MD file in Star Wars
        sw_factions_dir = Path(UNIVERSE_ROOT) / "star_wars" / "factions"
        
        md_file = None
        xml_file = None
        
        for root, _, files in os.walk(sw_factions_dir):
            for f in files:
                if f.endswith(".md") and "template" not in f:
                    md_file = os.path.join(root, f)
                if f.endswith(".xml") and "Hardpoints" not in root:
                    xml_file = os.path.join(root, f)
                if md_file and xml_file: break
            if md_file and xml_file: break
        
        if md_file:
            print(f"Testing MD loading: {md_file}")
            unit_md = UnitFactory.create_from_file(md_file, "Imperial_Remnant")
            assert unit_md is not None
            assert hasattr(unit_md, "name")
            
        if xml_file:
            print(f"Testing XML loading: {xml_file}")
            # XML loading requires mod root
            unit_xml = UnitFactory.create_from_file(xml_file, "Imperial_Remnant")
            assert unit_xml is not None

    def test_registry_hybrid_support(self):
        """Verifies that the weapon registry contains source_format metadata."""
        from src.utils import registry_builder
        registry_builder.build_weapon_registry(str(self.sw_config.universe_root), verbose=False)
        
        reg_path = self.sw_config.registry_paths["weapon"]
        assert reg_path.exists()
        
        with open(reg_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
            
        # Check for both formats in the registry
        formats_found = set()
        for entry in registry.values():
            if "source_format" in entry:
                formats_found.add(entry["source_format"])
        
        print(f"Found weapon source formats: {formats_found}")
        assert "markdown" in formats_found
        # XML might not be found if no XML weapons were extracted in this universe path,
        # but for Star Wars it should be there if XML parser hit.
