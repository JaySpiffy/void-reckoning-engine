
import sys
import os
sys.path.append(os.getcwd())

from src.models.unit import Unit
from src.core.synthesis_layer import synthesize_universal_stats
from src.core.universal_stats import HULL_STRUCTURAL_INTEGRITY, get_default_universal_stats

def test_scaling():
    print("\n--- TEST: Stats Scaling ---")
    
    # DNA from Reference (Zealot Legions Fighter)
    dna = {
      "atom_mass": 6.25,
      "atom_energy": 18.75,
      "atom_cohesion": 6.25,
      "atom_volatility": 2.5,
      "atom_stability": 6.25,
      "atom_focus": 21.25,
      "atom_frequency": 2.5,
      "atom_aether": 2.5,
      "atom_will": 6.25,
      "atom_information": 27.5
    }
    
    print(f"Input DNA Mass: {dna['atom_mass']}")
    print(f"Input DNA Cohesion: {dna['atom_cohesion']}")
    
    # manual calc
    m = dna['atom_mass']
    c = dna['atom_cohesion']
    hull_raw = m * c * 10
    print(f"Expected Hull Raw (m*c*10): {hull_raw}")
    
    # Run Synthesis
    stats = synthesize_universal_stats(dna)
    syn_hull = stats.get(HULL_STRUCTURAL_INTEGRITY)
    print(f"Synthesized Hull Param: {syn_hull}")
    
    # Instantiate Unit
    print("\nInstantiating Unit...")
    u = Unit(
        name="Test Fighter", 
        ma=50, md=50, hp=80, armor=0, damage=10, abilities={},
        elemental_dna=dna,
        faction="Zealot_Legions",
        domain="space"
    )
    
    print(f"Unit Base HP (Init Arg): 80")
    print(f"Unit Final HP: {u.base_hp}")
    print(f"Unit Current HP: {u.current_hp}")
    print(f"Universal Stats [HULL]: {u.universal_stats.get(HULL_STRUCTURAL_INTEGRITY)}")
    
    if u.base_hp > 500:
        print("FAILURE: HP Inflation Detected!")
    else:
        print("SUCCESS: HP within normal bounds.")

if __name__ == "__main__":
    test_scaling()
