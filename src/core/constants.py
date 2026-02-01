import os
import json
import src.core.config as config

# --- Configuration ---
AGREEMENT_NUMERALS = ["Prime", "Secundus", "Tertius", "Quartus", "Quintus", "Sextus"]

# --- Universe Data Access ---
from src.core.universe_data import UniverseDataManager

def get_factions():
    """Returns faction list for active universe."""
    return UniverseDataManager.get_instance().get_factions()

def get_planet_classes():
    """Returns planet classes for active universe."""
    return UniverseDataManager.get_instance().get_planet_classes()

def get_terrain_modifiers():
    """Returns terrain modifiers for active universe."""
    return UniverseDataManager.get_instance().get_terrain_modifiers()

def get_building_defense_bonus():
    """Returns building defense bonuses for active universe."""
    return UniverseDataManager.get_instance().get_building_defense_bonus()

def get_historical_bias():
    """Returns diplomacy historical bias for active universe."""
    return UniverseDataManager.get_instance().get_historical_bias()

# --- PHASE 11: GAMEPLAY CONSTANTS ---
# Economy
TRADE_BONUS_PER_PARTNER = 0.05
RESEARCH_COST_THRESHOLD = 700
FLEET_COMMISSION_THRESHOLD = 4000
FLEET_COMMISSION_COST = 2000
CONSTRUCTION_REQ_THRESHOLD = 1000
COLONIZATION_REQ_COST = 3000
ORBIT_DISCOUNT_MULTIPLIER = 0.5

# Construction
BUILD_TIME_DIVISOR = 100
MAX_BUILD_TIME = 10

# Combat & Units
MAX_COMBAT_ROUNDS = 2000
MAX_FLEET_SIZE = 500
MAX_LAND_UNITS = 20
SUPPRESSED_THRESHOLD = 25.0
PINNED_THRESHOLD = 75.0
SUPPRESSION_RECOVERY_BONUS = 5.0

# Victory
VICTORY_PLANET_THRESHOLD = 0.50
VICTORY_TURN_LIMIT = 300

# --- PHASE 5: ELEMENTAL CONSTANTS ---
ATOMIC_BUDGET_ENFORCEMENT = "warn"  # Options: "strict", "warn", "normalize", "off"

# --- PHASE 8: BUILDING DATABASE ---
def get_building_database():
    """Returns the building database for active universe."""
    return UniverseDataManager.get_instance().get_building_database()

def categorize_building(building_id: str, building_data: dict) -> str:
    """
    Categorizes a building as Economy, Military, or Research based on its effects.
    
    Args:
        building_id: The building identifier
        building_data: The building data dictionary
    
    Returns:
        str: "Economy", "Military", "Research", or "Infrastructure"
    """
    effects = building_data.get("effects", {})
    description = str(effects.get("description", ""))
    
    # Check for explicit category first
    if "category" in building_data:
        cat = building_data["category"]
        if cat in ["Economy", "Military", "Research"]:
            return cat
            
    # 1. Military (Hard Check: Unlocks)
    # If it unlocks units, it is military infrastructure, costing upkeep.
    if building_data.get("unlocks"):
        return "Military"
    
    # 2. Research indicators
    research_keywords = [
        "Research", "Tech", "Laboratory", "Academy", "University",
        "Science", "Innovation", "Archive", "Library", "Databank"
    ]
    if any(kw in description for kw in research_keywords) or "Research" in building_id:
        return "Research"

    # 3. Economy indicators (Income Generators)
    economy_keywords = [
        "Requisition", "Mining", "Trade", "Tax", "Income", "Credits",
        "Wealth", "Finance", "Harvest"
    ]
    if any(kw in description for kw in economy_keywords):
        return "Economy"
        
    # Check active income field
    # (Some mods use income_req for generation, though we usually use effects)
    if building_data.get("income_req", 0) > 0:
        return "Economy"

    # 4. Military / Defense Keywords (Fallback)
    military_keywords = [
        "Garrison", "Barracks", "Shipyard", "Dock", "Foundry", "Drydock", 
        "Military", "Defense", "Fortification", "Bunker", "Shield", 
        "Turret", "Wall", "Factory", "Assembly"
    ]
    if any(kw in description for kw in military_keywords):
        return "Military"
    
    # Default
    return "Infrastructure"

def get_building_category(building_id: str) -> str:
    """
    Returns the category of a building.
    
    Args:
        building_id: The building identifier
    
    Returns:
        str: "Economy", "Military", "Research", or "Infrastructure"
    """
    building_db = get_building_database()
    if not building_db or building_id not in building_db:
        return "Infrastructure"
    
    return categorize_building(building_id, building_db[building_id])

# --- Backward Compatibility Layer ---
def __getattr__(name):
    """Module-level getattr to support legacy constant imports."""
    if name == "FACTIONS":
        return get_factions()
    if name == "PLANET_CLASSES":
        return get_planet_classes()
    if name == "TERRAIN_MODIFIERS":
        return get_terrain_modifiers()
    if name == "BUILDING_DEFENSE_BONUS":
        return get_building_defense_bonus()
    if name == "HISTORICAL_BIAS":
        return get_historical_bias()
    if name == "BUILDING_DATABASE":
        return get_building_database()
        
    raise AttributeError(f"module {__name__} has no attribute {name}")

# Legacy names (for backward compatibility) - these will be intercepted by __getattr__

# --- PHASE 22: UI CONSTANTS ---
FACTION_ABBREVIATIONS = {
    "Templars_of_the_Flux": "TPL",
    "Transcendent_Order": "TRA",
    "SteelBound_Syndicate": "STE",
    "BioTide_Collective": "BIO",
    "Algorithmic_Hierarchy": "ALG",
    "Nebula_Drifters": "NEB",
    "Aurelian_Hegemony": "AUR",
    "VoidSpawn_Entities": "VOI",
    "ScrapLord_Marauders": "SCR",
    "Primeval_Sentinels": "PRM"
}

