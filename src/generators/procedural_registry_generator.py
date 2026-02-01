"""
procedural_registry_generator.py

Handles the procedural generation of ship and land unit rosters using design factories.
Extracted from registry_builder.py to separate generation logic from registry compilation.
"""
import os
import json
from src.core.config import UNIVERSE_ROOT
from src.factories.design_factory import ShipDesignFactory
from src.factories.land_factory import LandDesignFactory

def generate_ship_roster(universe_path: str, verbose: bool = True):
    """
    Generates procedural ship designs for all factions using ShipDesignFactory.
    Saves output to universes/<universe>/units/procedural_roster.json.
    """
    if verbose: print("Generating Procedural Ship Roster...")
    
    # 1. Load Blueprints
    hulls_path = os.path.join(UNIVERSE_ROOT, "base", "units", "base_ship_hulls.json")
    modules_path = os.path.join(UNIVERSE_ROOT, "base", "modules", "base_module_blueprints.json")
    
    if not os.path.exists(hulls_path) or not os.path.exists(modules_path):
        if verbose: print(f"WARNING: Blueprints missing at {hulls_path}. Skipping ship generation.")
        return

    with open(hulls_path, 'r', encoding='utf-8') as f: hulls = json.load(f)
    with open(modules_path, 'r', encoding='utf-8') as f: modules = json.load(f)
    
    # 2. Init Factory
    factory = ShipDesignFactory(hulls, modules)
    
    # 3. Load Context (Factions & Arsenal)
    factions_dir = os.path.join(universe_path, "factions")
    f_reg_path = os.path.join(factions_dir, "faction_registry.json")
    arsenal_path = os.path.join(factions_dir, "weapon_registry.json")
    
    if not os.path.exists(f_reg_path) or not os.path.exists(arsenal_path):
        if verbose: 
            print(f"WARNING: Missing Faction Registry or Arsenal.")
        return
        
    with open(f_reg_path, 'r', encoding='utf-8') as f: faction_reg = json.load(f)
    with open(arsenal_path, 'r', encoding='utf-8') as f: arsenal = json.load(f)
    
    # 4. Generate
    full_roster = {}
    
    for faction, f_data in faction_reg.items():
        if faction == "Neutral": continue
        
        # Get Arsenal (Filter by ID prefix)
        f_arsenal = {
            k: v for k, v in arsenal.items() 
            if k.startswith(f"{faction}_")
        }
        
        if not f_arsenal:
            f_arsenal = arsenal 
            
        # Get Traits from Quirks
        quirks = f_data.get("quirks", {})
        traits = list(quirks.keys()) if isinstance(quirks, dict) else []
            
        # Design Ships
        ships = factory.design_roster(faction, traits, f_arsenal)
        
        # Add to roster (keyed by blueprint_id)
        for ship in ships:
            full_roster[ship["blueprint_id"]] = ship
            
    # 5. Save
    units_dir = os.path.join(universe_path, "units")
    if not os.path.exists(units_dir): os.makedirs(units_dir)
    
    out_path = os.path.join(units_dir, "procedural_roster.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(full_roster, f, indent=2)
        
    if verbose: print(f"Generated {len(full_roster)} ship designs to {out_path}")


def generate_land_roster(universe_path: str, verbose: bool = False):
    """
    Generates procedural land units (Infantry, Vehicles) for all factions using Tech/Traits.
    """
    if verbose: print("Generating Procedural Land Roster...")
    
    # 1. Load Blueprints
    base_dir = os.path.join(UNIVERSE_ROOT, "base")
    chassis_path = os.path.join(base_dir, "units", "base_land_chassis.json")
    modules_path = os.path.join(base_dir, "modules", "base_land_modules.json")
    
    if not os.path.exists(chassis_path) or not os.path.exists(modules_path):
        if verbose: print(f"Missing base blueprints: {chassis_path} or {modules_path}")
        return

    with open(chassis_path, 'r', encoding='utf-8') as f: chassis = json.load(f)
    with open(modules_path, 'r', encoding='utf-8') as f: modules = json.load(f)
    
    # 2. Init Factory
    factory = LandDesignFactory(chassis, modules)
    
    # 3. Load Context (Factions + Arsenal)
    f_reg_path = os.path.join(universe_path, "factions", "faction_registry.json")
    arsenal_path = os.path.join(universe_path, "factions", "weapon_registry.json")
    
    if not os.path.exists(f_reg_path) or not os.path.exists(arsenal_path): 
        if verbose: print("Missing Faction Registry or Arsenal files.")
        return
        
    with open(f_reg_path, 'r', encoding='utf-8') as f: faction_reg = json.load(f)
    with open(arsenal_path, 'r', encoding='utf-8') as f: arsenal = json.load(f)
    
    # 4. Generate per Faction
    full_roster = {}
    
    for faction, f_data in faction_reg.items():
        if faction == "Neutral": continue

        # Get Arsenal (Filter by ID prefix)
        f_arsenal = {
            k: v for k, v in arsenal.items() 
            if k.startswith(f"{faction}_")
        }
        
        if not f_arsenal:
            f_arsenal = arsenal 
            
        # Get Traits from Quirks
        quirks = f_data.get("quirks", {})
        traits = list(quirks.keys()) if isinstance(quirks, dict) else []
            
        # Design Land Units
        units = factory.design_roster(faction, traits, f_arsenal)
        
        for u in units:
            full_roster[u["blueprint_id"]] = u
            
    # 5. Save
    units_dir = os.path.join(universe_path, "units")
    if not os.path.exists(units_dir): os.makedirs(units_dir)
    
    out_path = os.path.join(units_dir, "procedural_land_roster.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(full_roster, f, indent=2)
        
    if verbose: print(f"Generated {len(full_roster)} land unit designs to {out_path}")
