"""
registry_builder.py

Orchestrates the regeneration of procedural content and registries.
Restored to fix missing module error in validation CLI.
"""
import logging
import os
from src.generators.procedural_registry_generator import generate_ship_roster, generate_land_roster
from src.generators import weapon_blueprint_generator
from src.core.config import UNIVERSE_ROOT

def build_all_registries(universe_name: str = "void_reckoning", verbose: bool = True):
    """
    Regenerates all procedural content for the specified universe.
    Includes base weapon blueprints and faction-specific unit rosters.
    """
    if verbose:
        print(f"Building registries for universe: {universe_name}")
    
    # 1. Base Weapons (Global)
    try:
        if verbose: print("Generating Base Weapon Blueprints...")
        weapon_blueprint_generator.generate()
    except Exception as e:
        logging.error(f"Failed to generate base weapons: {e}")
        if verbose: print(f"Error generating base weapons: {e}")

    # 2. Universe Procedural Rosters
    universe_path = os.path.join(UNIVERSE_ROOT, universe_name)
    if os.path.exists(universe_path):
        try:
            generate_ship_roster(universe_path, verbose=verbose)
            generate_land_roster(universe_path, verbose=verbose)
        except Exception as e:
            logging.error(f"Failed to generate rosters: {e}")
            if verbose: print(f"Error generating rosters: {e}")
    else:
        if verbose: print(f"Universe path not found: {universe_path}")

    if verbose: print("Registry build complete.")
