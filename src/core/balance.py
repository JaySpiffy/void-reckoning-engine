"""
Economic Balance Module for PPS (Persistent Procedural Sandbox)

This module provides cost calculation formulas for units based on their
Atomic DNA stats. The formulas balance different unit types by assigning
appropriate material and energy costs.
"""

import math
from typing import Dict, Any, List, Optional

# --- FLEET CONSTANTS ---
FLEET_STARTING_REQ = 1000
FLEET_STARTING_PROM = 100
FLEET_SPEED_DEFAULT = 12
FLEET_SPEED_BATTLESHIP = 4
FLEET_SPEED_CRUISER = 6
FLEET_SPEED_ESCORT = 12
FLEET_SPEED_SCOUT_OVERRIDE = 14

SCAN_RANGE_BASE = 3
SCAN_RANGE_CAPITAL = 6
SCAN_RANGE_SCOUT_PATROL = 8

# Battle Engagement (Legacy)
BATTLE_START_DISTANCE = 60
BATTLE_CLOSURE_RATE = 12
BOARDING_CHANCE_PER_ROUND = 0.30
LOG_SAMPLE_RATE = 0.05

# --- UNIT STATS ---
UNIT_UPKEEP_RATIO = 0.05
UNIT_XP_PER_LEVEL_BASE = 100
UNIT_MAX_LEVEL = 50
UNIT_XP_GROWTH_EXPONENT = 1.2
UNIT_LEVEL_UP_UPGRADE_PROBABILITY = 0.3

# XP Award Constants
UNIT_XP_AWARD_DAMAGE_RATIO = 0.05
UNIT_XP_AWARD_KILL = 50.0
UNIT_XP_AWARD_SURVIVAL_ROUND = 10.0
UNIT_XP_AWARD_SURVIVAL_SEC = 1.0
UNIT_XP_AWARD_HEAL_RATIO = 0.1

UNIT_DEFAULT_LEADERSHIP = 70
UNIT_MAX_RANK = 9
UNIT_BASE_AGILITY = 45
UNIT_BASE_MOVEMENT = 6
UNIT_BASE_TOUGHNESS = 4
UNIT_BASE_BS = 50
UNIT_BASE_RANGE = 24
HULL_BASE_STATS = {
    "Corvette": {"hp": 80, "armor": 5, "ma": 50, "md": 50, "shield": 20, "crew": 20, "troop_value": 5},
    "Frigate": {"hp": 200, "armor": 8, "ma": 40, "md": 40, "shield": 100, "crew": 50, "troop_value": 10},
    "Destroyer": {"hp": 350, "armor": 10, "ma": 35, "md": 25, "shield": 150, "crew": 80, "troop_value": 12},
    "Escort": {"hp": 150, "armor": 10, "ma": 30, "md": 30, "shield": 50, "crew": 40, "troop_value": 10},
    "Cruiser": {"hp": 500, "armor": 12, "ma": 40, "md": 20, "shield": 200, "crew": 150, "troop_value": 15},
    "Carrier": {"hp": 800, "armor": 12, "ma": 20, "md": 10, "shield": 400, "crew": 200, "troop_value": 15},
    "Battleship": {"hp": 1200, "armor": 14, "ma": 50, "md": 10, "shield": 500, "crew": 400, "troop_value": 20},
    "Titan": {"hp": 5000, "armor": 25, "ma": 10, "md": 5, "shield": 2000, "crew": 1200, "troop_value": 30},
    "World Devastator": {"hp": 15000, "armor": 40, "ma": 8, "md": 4, "shield": 2000, "crew": 5000, "troop_value": 40},
    "Reality Breaker": {"hp": 13500, "armor": 36, "ma": 12, "md": 6, "shield": 2500, "crew": 4500, "troop_value": 40},
    "Thought Weaver": {"hp": 17250, "armor": 40, "ma": 5, "md": 3, "shield": 4000, "crew": 6000, "troop_value": 50},
    "Solar-Anchor": {"hp": 14000, "armor": 25, "ma": 5, "md": 5, "shield": 6000, "crew": 3000, "troop_value": 50},
    "Mothership": {"hp": 25000, "armor": 60, "ma": 4, "md": 2, "shield": 5000, "crew": 10000, "troop_value": 60}
}

ARMOR_FACING_FRONT_MULT = 1.0
ARMOR_FACING_SIDE_MULT = 0.75
ARMOR_FACING_REAR_MULT = 0.50

# Traits & Components
TRAIT_RECKLESS_PILOT_DMG_MULT = 1.2
TRAIT_RECKLESS_PILOT_ARMOR_PENALTY = -10
TRAIT_CAUTIOUS_COMMANDER_ARMOR_BONUS = 10
TRAIT_CAUTIOUS_COMMANDER_MA_PENALTY = -10
COMPONENT_SPILLOVER_DMG_RATIO = 0.1
SHIP_SHIELD_REGEN_RATIO = 0.01
SHIP_TURRET_EFFICIENCY = 0.5

# Transport Sizes (Unit Abilities Tags)
TRANSPORT_SIZE_DEFAULT = 1
TRANSPORT_SIZE_VEHICLE = 2
TRANSPORT_SIZE_MONSTER = 3
TRANSPORT_SIZE_TITANIC = 10

# Detection & Stealth
DETECTION_RANGE_BASE = 30
DETECTION_RANGE_SHIP = 100
DETECTION_RANGE_SCOUT_REGIMENT = 50

# Morale & Suppression
SUPPRESSION_RECOVERY_BONUS = 10
ROUT_REQUISITION_PENALTY = 0.8  # If used for income reduction

# Combat Power Calculation (Strength)
STRENGTH_OFFENSE_MA_MULT = 0.5
STRENGTH_OFFENSE_DMG_MULT = 10
STRENGTH_DEFENSE_MD_MULT = 0.5
STRENGTH_DEFENSE_HP_DIVISOR = 10
STRENGTH_DEFENSE_ARMOR_MULT = 2

# [Lethality Tuning] User requested weapons "doing more damedg" (explosions).
GLOBAL_DAMAGE_MULTIPLIER = 2.0 

# --- COMBAT SIMULATOR ---
# Boarding
BOARDING_HULL_PER_DIE = 200
BOARDING_DAMAGE_PER_SUCCESS = 50
BOARDING_BONUS_SM = 2
BOARDING_BONUS_TERMINATOR = 1

BOARDING_RANGE_LIGHTNING = 50.0  # 5,000 units
BOARDING_RANGE_PODS = 25.0       # 2,500 units
BOARDING_PD_INTERCEPT_CHANCE_PODS = 0.2
BOARDING_PD_INTERCEPT_CHANCE_BOATS = 0.4
STANCE_CALL_TO_ARMS_TROOP_BONUS = 5.0

# Combat Modifiers (Hit Chance/MA)
MOD_MELEE_CHARGE_BASE = 10
MOD_MELEE_CHARGE_SHOCK = 15
MOD_STEALTH_PENALTY = -10
MOD_WAAAGH_MA_BONUS = 30
MOD_MARKERLIGHT_MA_BONUS = 20
MOD_SYNAPSE_MA_BONUS = 10
MOD_ULTRAMARINES_AP_BONUS = 10
MOD_TAKE_AIM_MA_BONUS = 10
MOD_PFP_MA_BONUS = 10
MOD_PFP_AP_BONUS = 10
MOD_LONG_RANGE_PENALTY = -10
MOD_SUPPRESSION_BS_PENALTY = -20
MOD_SUPPRESSION_ACCURACY_PENALTY = -25

# [NEW] Ground Combat Lethality
GROUND_LETHALITY_SCALAR = 2.5 # Multiplier for all ground-domain damage

# Modifiers
MOD_COVER_ACCURACY_PENALTY = -10 # Reduced from -15 (Cover is now more about DR than missing)
MOD_EAW_HARDPOINT_DMG_MULT = 1.25
MOD_TANK_HUNTER_AP_BONUS = 40
MOD_KITE_RANGE_BONUS = 5
MOD_DOCTRINE_CHARGE_DMG_MULT = 1.2
MOD_DOCTRINE_CHARGE_DEFENSE_PENALTY = -10
MOD_DOCTRINE_KITE_BS_BONUS = 15
MOD_DOCTRINE_DEFEND_DEFENSE_BONUS = 20

# Morale
MORALE_LDR_THRESHOLD_HP_RATIO = 0.5
MORALE_FAILURE_MA_MULT = 0.8
MORALE_FEAR_LDR_PENALTY = -10
MORALE_RECOVERY_RATE = 5.0
MORALE_DAMAGE_WEIGHT = 0.5
MORALE_REAR_PENALTY = 20.0
MORALE_FLANK_PENALTY = 10.0
MORALE_HERO_BOOST = 15.0
MORALE_FEAR_DRAIN = 5.0
MORALE_TERROR_DRAIN = 15.0
MORALE_INSPIRATION_BOOST = 10.0

# Combat Modifiers (Damage/Crit)
MOD_ANTI_INFANTRY_MULT = 0.15
MOD_ANTI_LARGE_MULT = 0.15
MOD_CRIT_CHANCE_LETHAL = 10
MOD_CRIT_CHANCE_MONSTER_SLAYER = 20

# Mitigation & Armor
MAX_MITIGATION_PCT = 0.90
COVER_SAVE_IMPROVEMENT = 1
SAVE_TARGET_D6_MAX = 7
SAVE_TARGET_D6_MIN = 2

# Titan Reactor Overload
TITAN_REACTOR_DMG_MULT = 1.5
TITAN_REACTOR_SELF_DMG_MIN = 10
TITAN_REACTOR_SELF_DMG_MAX = 50
TITAN_REACTOR_SPECIALIST_MULT = 0.5

# --- ECONOMY & AI ---
ECON_INFRASTRUCTURE_RATIO = 1.5
ECON_RESERVE_MIN = 300
ECON_RESERVE_TARGET = 400
ECON_CONSTRUCTION_BUDGET_MIN = 500
ECON_STOCKPILE_OVERRIDE_THRESHOLD = 50000 # Reduced from 100k to 50k for earlier expansion triggers
ECON_NAVY_PENALTY_RATE = 0.10 # Reduced from 0.25 to curb 500+ fleet spam
ECON_MARGIN_CRISIS_THRESHOLD = 1.1

# Insolvency
INSOLVENCY_DEFICIT_MODERATE = 10000
INSOLVENCY_DEFICIT_MAJOR = 50000
INSOLVENCY_DISBAND_BASE = 50
INSOLVENCY_DISBAND_MODERATE = 100
INSOLVENCY_DISBAND_MAJOR = 250

# --- MAINTENANCE CAPS (User Plan) ---
# Hard caps for budget categories to prevent death spiral.
# Total Maintenance shoud not exceed 37.5% of Income.
MAINT_CAP_NAVY = 0.60   # Increased from 25% to 60% (Massive Navy)
MAINT_CAP_ARMY = 0.25   # 25%
MAINT_CAP_INFRA = 0.20  # 20%

# Phase 10: Garrison Discounts & Conquest Costs
GARRISON_UPKEEP_MULTIPLIER = 0.5  # Armies within planetary capacity are cheaper
PACIFICATION_COST = 500           # Base cost to occupy a hostile planet

# --- RECRUITMENT ---
RECRUIT_STOCKPILE_OVERRIDE_MULT = 5.0
RECRUIT_BATCH_SIZE_MAX = 200
RECRUIT_NAVY_CAP_BASE = 25 # Increased from 10 to 25
RECRUIT_ARMY_BATCH_CAP = 100

# --- CONSTRUCTION ---
CONST_EMERGENCY_BUDGET_THRESHOLD = 1000
CONST_HIGH_PRIORITY_THRESHOLD = 3000

# --- USER BALANCING ADJUSTMENTS ---
FLEET_MAINTENANCE_SCALAR = 0.2  # Reduced from 0.5 to 0.2 (80% Discout on standard upkeep)

# Economy Recovery Constants
MIN_PLANET_INCOME = 50              # Base income per planet
EMERGENCY_GRANT_PER_PLANET = 200   # Emergency aid per planet
EMERGENCY_GRANT_MAX = 3000          # Maximum emergency grant
EMERGENCY_AID_COOLDOWN = 10        # Turns between emergency grants
DEBT_RESTRUCTURING_TURNS = 20       # Turns of insolvency for debt forgiveness
DEBT_FORGIVENESS_RATIO = 0.5        # Portion of debt to forgive
GROUND_RAID_INCOME_RATIO = 0.1      # Planet value percentage for ground raid
GROUND_RAID_MAX_PER_ARMY = 200      # Maximum raid income per army
RECOVERY_RECRUITMENT_MILD = 0.4     # Recruitment budget in mild RECOVERY
RECOVERY_RECRUITMENT_MODERATE = 0.25 # Recruitment budget in moderate RECOVERY
RECOVERY_DEBT_THRESHOLD_MILD = 5000   # Debt threshold for mild RECOVERY
RECOVERY_DEBT_THRESHOLD_MODERATE = 20000  # Debt threshold for moderate RECOVERY



def calculate_material_cost(dna: dict) -> int:
    """
    Calculates the 'Metal' cost of a unit based on physical mass.
    Heavy units cost more resources to build.
    
    The material cost is primarily driven by:
    - atom_mass: Physical weight of the unit (heavier = more expensive)
    - atom_cohesion: Structural integrity (stronger materials = more expensive)
    
    Formula: Base + (Mass * 2) + (Cohesion * 1.5)
    
    Args:
        dna: A dictionary containing Atomic DNA stats for the unit.
              Expected keys: 'atom_mass', 'atom_cohesion'
    
    Returns:
        The material cost as an integer.
    
    Examples:
        >>> calculate_material_cost({"atom_mass": 100, "atom_cohesion": 50})
        275
        
        >>> calculate_material_cost({"atom_mass": 0, "atom_cohesion": 0})
        50
    """
    mass = dna.get("atom_mass", 0)
    cohesion = dna.get("atom_cohesion", 0)
    
    # Formula: Base + (Mass * 2) + (Cohesion * 1.5)
    return int(50 + (mass * 2.0) + (cohesion * 1.5))


def calculate_energy_cost(dna: dict) -> int:
    """
    Calculates the 'Energy' cost based on high-tech complexity.
    Smart/Magical units are expensive to power.
    
    The energy cost is primarily driven by:
    - atom_energy: Standard energy consumption
    - atom_information: Advanced computing/AI systems (premium: 3x multiplier)
    - atom_aether: Magical or exotic power sources (premium: 5x multiplier)
    
    Formula: Base + (Energy * 1.0) + (Information * 3.0) + (Aether * 5.0)
    
    Args:
        dna: A dictionary containing Atomic DNA stats for the unit.
              Expected keys: 'atom_energy', 'atom_information', 'atom_aether'
    
    Returns:
        The energy cost as an integer.
    
    Examples:
        >>> calculate_energy_cost({"atom_energy": 100, "atom_information": 50, "atom_aether": 10})
        410
        
        >>> calculate_energy_cost({"atom_energy": 0, "atom_information": 0, "atom_aether": 0})
        10
    """
    energy = dna.get("atom_energy", 0)
    info = dna.get("atom_information", 0)
    aether = dna.get("atom_aether", 0)
    
    # Information and Aether are 'premium' stats (3x and 5x multiplier respectively)
    return int(10 + (energy * 1.0) + (info * 3.0) + (aether * 5.0))


def calculate_total_cost(dna: dict) -> dict:
    """
    Returns both material and energy costs for a unit.
    
    This is a convenience function that calculates both cost types
    in a single call, useful for unit creation and validation.
    
    Args:
        dna: A dictionary containing Atomic DNA stats for the unit.
    
    Returns:
        A dictionary with keys 'material_cost' and 'energy_cost'.
    
    Examples:
        >>> calculate_total_cost({"atom_mass": 100, "atom_cohesion": 50, 
        ...                      "atom_energy": 100, "atom_information": 50, "atom_aether": 10})
        {'material_cost': 275, 'energy_cost': 410}
    """
    return {
        "material_cost": calculate_material_cost(dna),
        "energy_cost": calculate_energy_cost(dna)
    }


def calculate_unit_tier(dna: dict) -> int:
    """
    Determines the tier of a unit based on its total cost.
    
    Tiers are used to categorize units for balance and progression:
    - Tier 1: Total cost < 100 (Basic units)
    - Tier 2: Total cost 100-299 (Standard units)
    - Tier 3: Total cost 300-599 (Elite units)
    - Tier 4: Total cost >= 600 (Legendary units)
    
    Args:
        dna: A dictionary containing Atomic DNA stats for the unit.
    
    Returns:
        The tier as an integer (1-4).
    """
    costs = calculate_total_cost(dna)
    total = costs["material_cost"] + costs["energy_cost"]
    
    if total < 100:
        return 1
    elif total < 300:
        return 2
    elif total < 600:
        return 3
    else:
        return 4


def is_affordable(material_cost: int, energy_cost: int,
                  available_material: int, available_energy: int) -> bool:
    """
    Checks if a faction can afford a unit with the given costs.
    
    Args:
        material_cost: The material cost of the unit.
        energy_cost: The energy cost of the unit.
        available_material: The faction's available material (requisition).
        available_energy: The faction's available energy.
    
    Returns:
        True if the faction can afford the unit, False otherwise.
    """
    return material_cost <= available_material and energy_cost <= available_energy


def calculate_research_turns(tech_requirements: Dict[str, float], faction_dna: Dict[str, float], base_cost: int = 1000) -> int:
    """
    Calculates how many turns it takes for a faction to research a specific tech.
    
    Formula: Turns = Base_Tech_Cost / (Faction_Intelligence * (1 + Efficiency_Score / 50))
    
    Args:
        tech_requirements: Dict mapping atoms to their importance for this tech
                          Example: {"atom_energy": 0.5, "atom_frequency": 0.5}
        faction_dna: Faction's DNA dictionary
        base_cost: Base research cost for this technology
    
    Returns:
        Number of turns to research
    """
    efficiency_score = 0.0
    for atom, weight in tech_requirements.items():
        # The faction's capability in this specific atom
        atom_val = faction_dna.get(atom, 0.0)
        efficiency_score += atom_val * weight

    # Base research speed comes from Information (Intelligence)
    base_intelligence = faction_dna.get("atom_information", 1.0)
    
    # Formula: Cost / (Intelligence * Specific_Know_How)
    research_power = base_intelligence * (1 + (efficiency_score / 50.0))
    turns = base_cost / max(research_power, 1.0)
    
    return int(turns)


def calculate_bounded_stat(dna_value: float, midpoint: float = 50, steepness: float = 0.1) -> float:
    """
    Uses Sigmoid Function to squash any input number into a 0.0 to 1.0 range.
    
    Formula: S(x) = 1 / (1 + e^(-k * (x - x0)))
    
    Args:
        dna_value: The raw DNA sum
        midpoint: The midpoint where result is 0.5 (default: 50)
        steepness: How steep the curve is (default: 0.1)
    
    Returns:
        Value between 0.0 and 1.0
    
    Examples:
        - If Information is 10, Accuracy = ~2%
        - If Information is 50, Accuracy = 50%
        - If Information is 200, Accuracy = 99.9% (Never hits 100%)
    """
    sigmoid = 1 / (1 + math.exp(-steepness * (dna_value - midpoint)))
    return sigmoid


def calculate_accuracy(dna: Dict[str, float]) -> float:
    """Calculates unit accuracy using sigmoid scaling."""
    # Information + Focus contribute to accuracy
    info_sum = dna.get("atom_information", 0) + dna.get("atom_focus", 0)
    return calculate_bounded_stat(info_sum, midpoint=50, steepness=0.08)


def calculate_evasion(dna: Dict[str, float]) -> float:
    """Calculates unit evasion using sigmoid scaling."""
    # Frequency + Cohesion contribute to evasion
    evasion_sum = dna.get("atom_frequency", 0) + dna.get("atom_cohesion", 0)
    return calculate_bounded_stat(evasion_sum, midpoint=50, steepness=0.08)


def calculate_crit_chance(dna: Dict[str, float]) -> float:
    """Calculates critical hit chance using sigmoid scaling."""
    # Volatility + Will contribute to crit chance
    crit_sum = dna.get("atom_volatility", 0) + dna.get("atom_will", 0)
    return calculate_bounded_stat(crit_sum, midpoint=60, steepness=0.06)


def calculate_combat_power(unit_dna: Dict[str, float], weapon_stats: Dict[str, float]) -> float:
    """
    Calculates the Combat Power (CP) score for a unit.
    Uses Lanchester's Square Law derivative.
    
    Formula: CP = Effective_HP * Damage_Output
    
    Where:
        Effective_HP = (Mass * Cohesion) / (1 - ArmorRating/100)
        Damage_Output = Damage * FireRate * Accuracy
    
    Args:
        unit_dna: The unit's DNA dictionary
        weapon_stats: The unit's weapon statistics
    
    Returns:
        Combat Power score
    """
    # Calculate Effective HP
    mass = unit_dna.get("atom_mass", 10.0)
    cohesion = unit_dna.get("atom_cohesion", 10.0)
    armor = weapon_stats.get("armor", 0.0)
    
    # Avoid division by zero
    armor_factor = max(0.1, 1.0 - (armor / 100.0))
    effective_hp = (mass * cohesion) / armor_factor
    
    # Calculate Damage Output
    damage = weapon_stats.get("damage", 10.0)
    fire_rate = weapon_stats.get("fire_rate", 1.0)
    accuracy = weapon_stats.get("accuracy", 0.5)
    
    damage_output = damage * fire_rate * accuracy
    
    # Combat Power
    combat_power = effective_hp * damage_output
    
    return combat_power


def normalize_unit_power(unit_dna: Dict[str, float], weapon_stats: Dict[str, float],
                        standard_cp: float = 100.0) -> Dict[str, Any]:
    """
    Normalizes a unit's power against a standard reference point.
    Applies balancing if the unit is too powerful.
    
    Args:
        unit_dna: The unit's DNA dictionary
        weapon_stats: The unit's weapon statistics
        standard_cp: The Combat Power of a standard unit (default: 100)
    
    Returns:
        Dictionary with normalized stats and any balancing modifiers
    """
    # Calculate current Combat Power
    current_cp = calculate_combat_power(unit_dna, weapon_stats)
    
    # Calculate power ratio
    power_ratio = current_cp / standard_cp
    
    # Balancing thresholds
    max_ratio = 1.5  # Allow up to 50% more powerful than standard
    min_ratio = 0.5   # Don't allow below 50% of standard
    
    result = {
        "combat_power": current_cp,
        "power_ratio": power_ratio,
        "is_balanced": True,
        "cost_modifier": 1.0,
        "stat_modifier": 1.0
    }
    
    # If unit is too powerful, apply cost penalty
    if power_ratio > max_ratio:
        result["is_balanced"] = False
        # Make it expensive
        result["cost_modifier"] = round(power_ratio * 1.5, 2)
    
    # If unit is too weak, apply cost bonus
    elif power_ratio < min_ratio:
        result["is_balanced"] = False
        # Make it cheap
        result["cost_modifier"] = round(max(0.5, power_ratio * 0.8), 2)
    
    return result


def calculate_faction_power_balance(faction_dna: Dict[str, float],
                                  unit_roster: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates the overall power balance of a faction's unit roster.
    
    Args:
        faction_dna: The faction's DNA dictionary
        unit_roster: List of the faction's units with their stats
    
    Returns:
        Dictionary with power balance metrics
    """
    if not unit_roster:
        return {
            "total_combat_power": 0.0,
            "average_power": 0.0,
            "power_variance": 0.0,
            "balance_score": 0.0
        }
    
    # Calculate power for each unit
    unit_powers = []
    for unit in unit_roster:
        unit_dna = unit.get("dna", faction_dna)
        weapon_stats = unit.get("weapon_stats", {})
        cp = calculate_combat_power(unit_dna, weapon_stats)
        unit_powers.append(cp)
    
    # Calculate metrics
    total_power = sum(unit_powers)
    average_power = total_power / len(unit_powers)
    
    # Calculate variance (how spread out the power levels are)
    variance = sum((p - average_power) ** 2 for p in unit_powers) / len(unit_powers)
    
    # Balance score: Higher is better (lower variance, good average power)
    balance_score = average_power / (1 + variance / 1000.0)
    
    return {
        "total_combat_power": round(total_power, 2),
        "average_power": round(average_power, 2),
        "power_variance": round(variance, 2),
        "balance_score": round(balance_score, 2)
    }
