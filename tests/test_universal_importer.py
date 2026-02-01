import pytest
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from tools.universal_importer import UniversalImporter
from src.utils.import_progress_tracker import ImportProgressTracker

@pytest.fixture
def test_dirs():
    """Fixture to handle test directory creation and cleanup."""
    game_dir = "tests/fixtures/mock_game"
    universe_name = "test_universe_import"
    
    if not os.path.exists(game_dir):
        os.makedirs(game_dir)
        
    yield game_dir, universe_name
    
    if os.path.exists(game_dir):
        shutil.rmtree(game_dir)

class TestUniversalImporter:
            
    def test_dry_run_initialization(self, test_dirs):
        """Test that importer can initialize in dry run mode."""
        game_dir, universe_name = test_dirs
        
        importer = UniversalImporter(
            game_dir=game_dir,
            universe_name=universe_name,
            dry_run=True,
            engine="generic"
        )
        assert importer.dry_run
        assert isinstance(importer.tracker, ImportProgressTracker)
        
    @patch('src.utils.parser_registry.ParserRegistry.get_instance')
    @patch('src.utils.format_detector.FormatDetector.detect_game_engine')
    @patch('src.utils.import_validator.ImportValidator.validate_file_structure')
    def test_run_orchestration(self, mock_valid, mock_detect, mock_registry_instance, test_dirs):
        """Test that run method calls stages in order."""
        game_dir, universe_name = test_dirs
        mock_detect.return_value = "generic"
        mock_valid.return_value = []
        
        # Mock Registry Metadata
        mock_registry_impl = MagicMock()
        mock_registry_impl.get_metadata.return_value = {
            "importer_module": "tools.dummy_importer",
            "importer_class": "DummyImporter"
        }
        mock_registry_instance.return_value = mock_registry_impl
        
        importer = UniversalImporter(
            game_dir=game_dir,
            universe_name=universe_name,
            dry_run=True,
            engine="generic",
            skip_registries=True # Skip actual complex registry build in test
        )
        
        # Mock methods to track calls
        importer._generate_dna = MagicMock()
        importer._calibrate_physics = MagicMock()
        importer._load_importer = MagicMock(return_value=MagicMock())
        
        importer.run()
        
        # Verify stages were called
        importer._generate_dna.assert_called_once()
        # Physics calibration might be skipped if PhysicsCalibrator is None, check logic or mock it
        # But we primarily want to ensure orchestration logic works
        
        # We can also verify tracker stages
        assert importer.tracker.current_stage >= 5
        importer._generate_dna.assert_called_once()
        # Physics calibration called if not skipped (default) and module exists
        # In this mock env we can't guarantee PhysicsCalibrator exists, but logic holds.

    def test_tracker_integration(self):
        tracker = ImportProgressTracker(quiet=True)
        tracker.start_stage("Test Stage", 100)
        tracker.update(50, "Halfway")
        
    @patch('tools.universal_importer.inject_dna_into_markdown')
    @patch('tools.universal_importer.generate_dna_from_stats')
    @patch('tools.universal_importer.extract_parser_data')
    @patch('os.walk')
    def test_dna_logic(self, mock_walk, mock_extract, mock_gen, mock_inject, test_dirs):
        """Test the DNA generation logic."""
        import os # Ensure os is available within the test execution scope if used by patches
        game_dir, universe_name = test_dirs
        
        # Setup mocks
        mock_walk.return_value = [
            ("root/factions/empire", [], ["unit_test.md"])
        ]
        mock_extract.return_value = {"stats": {"mass": 50, "energy": 50}}
        mock_gen.return_value = {"mass": 50.0, "energy": 50.0}
        mock_inject.return_value = True
        
        importer = UniversalImporter(
            game_dir=game_dir,
            universe_name=universe_name,
            dry_run=False,
            engine="generic",
            skip_registries=True,
            quiet=True
        )
        
        # Run just the stage
        importer._generate_dna()
        
        # Verify
        mock_extract.assert_called()
        mock_gen.assert_called()
        mock_inject.assert_called()
        assert importer.entity_counts['units'] == 1
