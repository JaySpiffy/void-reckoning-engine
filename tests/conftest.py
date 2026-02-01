import pytest
import os
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import set_active_universe, get_universe_config, ACTIVE_UNIVERSE
from universes.base.universe_loader import UniverseLoader
from src.managers.campaign_manager import CampaignEngine

@pytest.fixture(scope="session")
def universe_loader():
    """Provides UniverseLoader instance for all tests."""
    universes_root = Path(__file__).parent.parent / "universes"
    loader = UniverseLoader(universes_root)
    loader.discover_universes()
    return loader

@pytest.fixture
def mock_engine_with_universe(request):
    """Creates mock engine with universe context initialized.
    
    Usage: @pytest.mark.parametrize("mock_engine_with_universe", ["eternal_crusade"], indirect=True)
    """
    universe_name = getattr(request, "param", "void_reckoning")
    set_active_universe(universe_name)
    
    mock_engine = MagicMock(spec=CampaignEngine)
    mock_engine.universe_config = get_universe_config(universe_name)
    mock_engine.report_organizer = MagicMock()
    mock_engine.logger = MagicMock()
    
    return mock_engine

@pytest.fixture
def test_universe(universe_loader):
    """Provides a guaranteed 'void_reckoning' universe for testing."""
    # Ensure it's reachable or fallback to mock?
    # For now, we assume void_reckoning exists as default generic universe
    return "void_reckoning"

@pytest.fixture
def eternal_crusade_universe(universe_loader):
    """Provides void_reckoning universe context for testing."""
    set_active_universe("void_reckoning")
    return "void_reckoning"
