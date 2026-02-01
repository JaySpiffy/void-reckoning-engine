
import logging
import sys
import os

# Setup logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
logger = logging.getLogger("src.managers.galaxy_generator")
logger.setLevel(logging.INFO)

# Append src to path
sys.path.append(os.getcwd())

from src.managers.galaxy_generator import GalaxyGenerator
from src.core.universe_data import UniverseDataManager

def test():
    print("Initializing GalaxyGenerator...")
    gg = GalaxyGenerator()
    
    # Needs UniverseDataManager initialized?
    # GalaxyGenerator.load_blueprints uses UniverseDataManager.get_instance().universe_config
    # Does that exist by default?
    udm = UniverseDataManager.get_instance()
    print(f"UDM Config: {udm.universe_config}")
    
    # Try loading
    gg.load_blueprints()
    
    print("\n--- RESULTS ---")
    for f, bps in gg.army_blueprints.items():
        print(f"Faction: {f}, Army Blueprints: {len(bps)}")
        
    for f, bps in gg.unit_blueprints.items():
        print(f"Faction: {f}, ALL Blueprints: {len(bps)}")

if __name__ == "__main__":
    test()
