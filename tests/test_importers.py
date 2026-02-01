import pytest
from tools.universal_importer import UniversalImporter
from src.utils.format_detector import FormatDetector
import os

# Skip tests if E:\SteamLibrary doesn't exist (Local Environment Check)
STEAM_LIB_PATH = "E:\\SteamLibrary"
HAS_STEAM_LIB = os.path.exists(STEAM_LIB_PATH)

@pytest.mark.skipif(not HAS_STEAM_LIB, reason="Steam Library not found on E:")
def test_steam_library_scan():
    """Test scanning Steam library for supported games."""
    results = FormatDetector.scan_steam_library(STEAM_LIB_PATH)
    # Start with assumption we might find something, or at least no crash
    assert isinstance(results, dict) 

@pytest.mark.skipif(not HAS_STEAM_LIB, reason="Steam Library not found on E:")
def test_eaw_import_dry_run():
    """Test Empire at War import in dry-run mode."""
    game_path = os.path.join(STEAM_LIB_PATH, "steamapps", "common", "Star Wars Empire at War", "GameData")
    if not os.path.exists(game_path):
        pytest.skip("EaW not installed")
        
    importer = UniversalImporter(
        game_dir=game_path,
        universe_name="test_star_wars",
        dry_run=True,
        extract_ai=False # Speed up test
    )
    importer.run()
    assert len(importer.errors) == 0

@pytest.mark.skipif(not HAS_STEAM_LIB, reason="Steam Library not found on E:")
def test_stellaris_import_dry_run():
    """Test Stellaris mod import in dry-run mode."""
    # Using a generic mod path or checking if Stellaris base exists
    # The plan used a specific mod path, we'll try to use that if it exists
    mod_path_example = os.path.join(STEAM_LIB_PATH, "steamapps", "common", "Stellaris", "mod", "test_mod")
    
    # Fallback to base game if mod doesn't exist for general parsing test
    base_game = os.path.join(STEAM_LIB_PATH, "steamapps", "common", "Stellaris")
    
    target_path = mod_path_example if os.path.exists(mod_path_example) else base_game
    if not os.path.exists(target_path):
        pytest.skip("Stellaris/Mod not installed")

    importer = UniversalImporter(
        game_dir=target_path,
        universe_name="test_stellaris",
        engine="paradox",
        dry_run=True,
        skip_registries=True 
    )
    importer.run()
    assert len(importer.errors) == 0
