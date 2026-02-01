import os
import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any

# Detect if running from installed package or development
if getattr(sys, 'frozen', False):
    # Running as frozen executable
    ROOT_DIR = os.path.dirname(sys.executable)
    SRC_DIR = os.path.join(ROOT_DIR, "src")
elif __file__:
    # Running from source: src/core/config.py -> ../../ = ROOT
    CORE_DIR = os.path.dirname(os.path.abspath(__file__))
    SRC_DIR = os.path.dirname(CORE_DIR)
    ROOT_DIR = os.path.dirname(SRC_DIR)
else:
    # Fallback
    ROOT_DIR = os.getcwd()
    SRC_DIR = os.path.join(ROOT_DIR, "src")

# Data Directories (Now at Root)
DATA_ROOT = os.path.join(ROOT_DIR, "data")
UNIVERSE_ROOT = os.path.join(ROOT_DIR, "universes")
ACTIVE_UNIVERSE: Optional[str] = None  # Set by CLI or campaign initialization

# Global path constants (initialized below)
INFRA_DIR = ""
TECH_DIR = ""
FACTIONS_DIR = ""
DATA_DIR = ""
UNITS_DIR = ""
REGISTRY_BUILDING = ""
REGISTRY_TECH = ""
REGISTRY_WEAPON = ""
REGISTRY_ABILITY = ""
REGISTRY_FACTION = ""

def get_universe_config(universe_name: str):
    """Dynamically loads a universe configuration."""
    # Import here to avoid circular dependencies
    from universes.base.universe_loader import UniverseLoader
    loader = UniverseLoader(Path(UNIVERSE_ROOT))
    return loader.load_universe(universe_name)

def _recompute_paths():
    """Recomputes global path constants based on the current ACTIVE_UNIVERSE."""
    global INFRA_DIR, TECH_DIR, FACTIONS_DIR, DATA_DIR, UNITS_DIR
    global REGISTRY_BUILDING, REGISTRY_TECH, REGISTRY_WEAPON, REGISTRY_ABILITY, REGISTRY_FACTION
    
    if ACTIVE_UNIVERSE is None:
        INFRA_DIR = os.path.join(DATA_ROOT, "infrastructure")
        TECH_DIR = os.path.join(DATA_ROOT, "technology")
        FACTIONS_DIR = os.path.join(DATA_ROOT, "factions")
    else:
        universe_config = get_universe_config(ACTIVE_UNIVERSE)
        FACTIONS_DIR = str(universe_config.factions_dir)
        INFRA_DIR = str(universe_config.infrastructure_dir)
        TECH_DIR = str(universe_config.technology_dir)

    DATA_DIR = FACTIONS_DIR # Alias for backward compatibility
    
    if ACTIVE_UNIVERSE and 'universe_config' in locals() and hasattr(universe_config, 'units_dir'):
        UNITS_DIR = str(universe_config.units_dir)
    else:
        UNITS_DIR = FACTIONS_DIR

    # Registry paths (Now dynamic)
    if ACTIVE_UNIVERSE is None:
        REGISTRY_BUILDING = os.path.join(INFRA_DIR, "building_registry.json")
        REGISTRY_TECH = os.path.join(TECH_DIR, "technology_registry.json")
        REGISTRY_WEAPON = os.path.join(FACTIONS_DIR, "weapon_registry.json")
        REGISTRY_ABILITY = os.path.join(FACTIONS_DIR, "ability_registry.json")
        REGISTRY_FACTION = os.path.join(FACTIONS_DIR, "faction_registry.json")
    else:
        universe_config = get_universe_config(ACTIVE_UNIVERSE)
        REGISTRY_BUILDING = str(universe_config.registry_paths["building"])
        REGISTRY_TECH = str(universe_config.registry_paths["tech"])
        REGISTRY_WEAPON = str(universe_config.registry_paths["weapon"])
        REGISTRY_ABILITY = str(universe_config.registry_paths["ability"])
        REGISTRY_FACTION = str(universe_config.registry_paths["faction"])

def _get_active_universe_file():
    """Returns path to the active universe persistence file."""
    config_dir = os.path.join(ROOT_DIR, "config")
    if not os.path.exists(config_dir):
         os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "active_universe.txt")

def set_active_universe(universe_name: Optional[str]):
    """Sets the active universe and recomputes all derived paths.
    
    Args:
        universe_name: The name of the universe to activate, or None for legacy data.
    """
    global ACTIVE_UNIVERSE
    ACTIVE_UNIVERSE = universe_name
    _recompute_paths()
    
    if universe_name:
        # Persist to file
        try:
            with open(_get_active_universe_file(), "w") as f:
                f.write(universe_name)
        except Exception:
            pass

        try:
            from src.core.universe_data import UniverseDataManager
            UniverseDataManager.get_instance().load_universe_data(universe_name)
        except Exception:
            # Fallback for early initialization or missing dependencies
            pass

def get_active_universe() -> Optional[str]:
    """Returns the currently active universe name."""
    global ACTIVE_UNIVERSE
    if ACTIVE_UNIVERSE is None:
        # Try to load from file
        try:
             path = _get_active_universe_file()
             if os.path.exists(path):
                 with open(path, "r") as f:
                     val = f.read().strip()
                     if val:
                         ACTIVE_UNIVERSE = val
                         _recompute_paths() # Ensure paths are synced
        except Exception:
             pass
             
    return ACTIVE_UNIVERSE

def list_available_universes() -> list[str]:
    """Returns list of all available universe names."""
    # Import here to avoid circular dependencies
    from universes.base.universe_loader import UniverseLoader
    loader = UniverseLoader(Path(UNIVERSE_ROOT))
    universes = loader.discover_universes()
    return sorted(universes)

# Initial path computation
_recompute_paths()

# Output directories (Now at Root)
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
SAVES_DIR = os.path.join(ROOT_DIR, "saves")

# Code Directories
SIMULATION_DIR = os.path.join(SRC_DIR, "engine")
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")
