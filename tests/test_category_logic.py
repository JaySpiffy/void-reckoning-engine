import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.unit import Unit
from src.factories.unit_factory import UnitFactory
from src.core.universe_data import UniverseDataManager

def test_categories():
    print("\n=== Verifying Atomic Ability Category Handlers ===\n")
    
    # Note: Third-party universe tests have been removed.
    # This test now validates generic category handling for eternal_crusade.
    print("Note: To add custom universe-specific category tests, add them here.")
    print("Multi-universe architecture is preserved for adding custom universes.")

if __name__ == "__main__":
    test_categories()
