import pytest
import math
from typing import Dict, Any, List

from src.utils.dna_generator import (
    generate_building_dna, 
    generate_technology_dna, 
    generate_faction_dna,
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_VOLATILITY,
    ATOM_STABILITY, ATOM_FOCUS, ATOM_FREQUENCY, ATOM_AETHER, 
    ATOM_WILL, ATOM_INFORMATION
)
from src.core.weapon_synthesizer import reverse_synthesize_weapon_dna
from src.core.ability_synthesizer import generate_ability_lens
from src.core.atomic_validator import validate_atomic_budget

def test_building_dna_generation():
    # Defensive Structure
    b_def = {"id": "Bunker", "name": "Heavy Bunker", "tier": 3}
    dna_def = generate_building_dna(b_def)
    
    assert dna_def.get(ATOM_COHESION, 0) > 25.0
    assert dna_def.get(ATOM_MASS, 0) > 20.0
    assert validate_atomic_budget(dna_def)[0] is True
    
    # Production Structure
    b_prod = {"id": "Forge", "name": "Manufactorum", "tier": 2}
    dna_prod = generate_building_dna(b_prod)
    
    assert dna_prod.get(ATOM_ENERGY, 0) > 20.0
    assert dna_prod.get(ATOM_INFORMATION, 0) > 15.0
    assert validate_atomic_budget(dna_prod)[0] is True

def test_technology_dna_generation():
    # Research Tech
    t_res = {"id": "Physics_Lab", "category": ["research"]}
    dna_res = generate_technology_dna(t_res)
    
    assert dna_res.get(ATOM_INFORMATION, 0) > 20.0
    assert validate_atomic_budget(dna_res)[0] is True
    
    # Warp Tech
    t_warp = {"id": "Warp_Drive", "category": ["psychic", "warp"]}
    dna_warp = generate_technology_dna(t_warp)
    
    assert dna_warp.get(ATOM_AETHER, 0) > 25.0
    assert validate_atomic_budget(dna_warp)[0] is True

def test_faction_dna_aggregation():
    # Mock Unit
    class MockUnit:
        def __init__(self, dna, tier=1):
            self.elemental_dna = dna
            self.tier = tier
            
    # Basic Roster
    u1_dna = {ATOM_MASS: 50, ATOM_ENERGY: 50} # Simplified unnormalized
    u1 = MockUnit(u1_dna, tier=1)
    
    # Faction Quirks
    quirks = {"diplomacy_bonus": 1, "retreat_threshold_mod": -0.5} 
    # Diplo -> +Will/Info. Retreat -> +Volatility/-Stability
    
    dna_fac = generate_faction_dna("MyFaction", [u1], quirks)
    
    assert validate_atomic_budget(dna_fac)[0] is True
    assert dna_fac.get(ATOM_WILL, 0) > 5.0 # From quirk
    assert dna_fac.get(ATOM_VOLATILITY, 0) > 2.0 # From quirk

def test_weapon_dna_reverse_synthesis():
    # High Strength Weapon
    w_stats = {"S": 10, "AP": 0, "D": 1, "Range": 24}
    dna = reverse_synthesize_weapon_dna(w_stats)
    
    # S10 -> High Energy
    assert dna.get(ATOM_ENERGY, 0) > 20.0
    assert validate_atomic_budget(dna)[0] is True
    
    # High AP Weapon
    w_ap = {"S": 4, "AP": -4, "D": 1}
    dna_ap = reverse_synthesize_weapon_dna(w_ap)
    # AP-4 -> High Focus
    assert dna_ap.get(ATOM_FOCUS, 0) > 20.0

def test_ability_lens_generation():
    # Psychic Ability
    ab_psy = {"id": "Smite", "description": "A focused blast of warp energy."}
    lens = generate_ability_lens(ab_psy)
    
    assert lens.get(ATOM_AETHER, 0) > 30.0

def test_atomic_budget_enforcement():
    # Test extreme inputs
    data = {"id": "Test", "name": "Test", "tier": 10} # High tier -> high multiplier
    dna = generate_building_dna(data)
    
    total = sum(dna.values())
    assert math.isclose(total, 100.0, rel_tol=1e-3)
