from typing import Dict

def synthesize_personality_vectors(dna: Dict[str, float]) -> Dict[str, float]:
    """
    Automatically calculates AI personality fields from Faction DNA.
    
    Uses Weighted Vector Projection to map the 10 Atoms onto 5 Personality Axes.
    
    Args:
        dna: Faction DNA dictionary
    
    Returns:
        Dictionary with aggression, cohesiveness, expansion_bias
    """
    # 1. Aggression Calculation
    # Aggression = (Volatility * 2.0 + Energy * 1.0 + Mass * 0.5) - (Stability * 1.5)
    aggression_score = (
        dna.get("atom_volatility", 0) * 2.0 + 
        dna.get("atom_energy", 0) * 1.0 +
        dna.get("atom_mass", 0) * 0.5
    ) - (dna.get("atom_stability", 0) * 1.5)
    
    # Normalize to 0.0 - 2.0 range (Standard is ~1.0)
    final_aggression = max(0.2, min(2.0, aggression_score / 50.0))

    # 2. Cohesiveness (Swarm vs Elite)
    # High Cohesion/Will = Tight formations. High Volatility = Chaos.
    cohesion_score = (
        dna.get("atom_cohesion", 0) * 1.5 +
        dna.get("atom_will", 0) * 1.0 +
        dna.get("atom_stability", 0) * 0.5
    ) - (dna.get("atom_volatility", 0) * 1.2)
    
    final_cohesion = max(0.1, min(2.0, cohesion_score / 60.0))

    # 3. Expansion Bias (Aggressive factions usually expand more)
    final_expansion = round(final_aggression * 0.8, 2)

    return {
        "aggression": round(final_aggression, 2),
        "cohesiveness": round(final_cohesion, 2),
        "expansion_bias": final_expansion
    }

def infer_doctrine_from_dna(dna: Dict[str, float]) -> Dict[str, str]:
    """
    Infers strategic, combat, and tech doctrines from faction DNA.
    
    Args:
        dna: Faction DNA dictionary
    
    Returns:
        Dictionary with strategic_doctrine, combat_doctrine, tech_doctrine
    """
    # Strategic Doctrine
    if dna.get("atom_volatility", 0) > 20:
        strategic = "AGGRESSIVE_EXPANSION"
    elif dna.get("atom_stability", 0) > 20:
        strategic = "DEFENSIVE_FORTIFICATION"
    elif dna.get("atom_information", 0) > 20:
        strategic = "TECHNOLOGICAL_ASCENDANCY"
    else:
        strategic = "BALANCED_GROWTH"
    
    # Combat Doctrine
    if dna.get("atom_mass", 0) > 25:
        combat = "SHOCK_ASSAULT"
    elif dna.get("atom_focus", 0) > 20:
        combat = "PRECISE_STRIKE"
    elif dna.get("atom_cohesion", 0) > 20:
        combat = "SWARM_TACTICS"
    else:
        combat = "ADAPTIVE_WARFARE"
    
    # Tech Doctrine
    if dna.get("atom_aether", 0) > 15:
        tech = "AETHERIC_MASTERY"
    elif dna.get("atom_information", 0) > 20:
        tech = "CYBERNETIC_ASCENSION"
    elif dna.get("atom_energy", 0) > 20:
        tech = "ENERGY_DOMINANCE"
    else:
        tech = "BALANCED_RESEARCH"
    
    return {
        "strategic_doctrine": strategic,
        "combat_doctrine": combat,
        "tech_doctrine": tech
    }
