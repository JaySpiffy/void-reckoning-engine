import os
import sys
from pathlib import Path

# Setup Path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from src.core.config import set_active_universe
from src.factories.unit_factory import UnitFactory
from src.core.universal_stats import *
from src.models.unit import Ship, Regiment

def verify_dna_system():
    print("=== Universal Stats DNA System Verification ===")
    
    # 1. Test Eternal Crusade (Regiment with Traits)
    print("\n[Test 1] Eternal Crusade - Regiment with Traits")
    set_active_universe("eternal_crusade")
    
    # Manually create a unit with a trait
    unit = Regiment(
        name="Test Vanguard",
        ma=40, md=40, hp=10, armor=5, damage=5,
        abilities={"Tags": ["Infantry"]},
        traits=["Veteran Crew", "Psionic Lv1"],
        faction="Iron_Vanguard"
    )
    
    # Finalize (Applies traits)
    from src.core.universe_data import UniverseDataManager
    reg = UniverseDataManager.get_instance().get_trait_registry()
    print(f"Registry keys: {list(reg.keys())}")
    
    UnitFactory._finalize_unit(unit)
    
    dna = unit.universal_stats
    print(f"Unit: {unit.name}")
    print(f"Traits: {unit.traits}")
    print(f"DNA [HULL_STRUCTURAL_INTEGRITY]: {dna.get(HULL_STRUCTURAL_INTEGRITY)}")
    print(f"DNA [CREW_EXPERIENCE]: {dna.get(CREW_EXPERIENCE)}")
    print(f"DNA [PSYKER_POWER_LEVEL]: {dna.get(PSYKER_POWER_LEVEL)}")
    
    # Verify Psionic Lv1 (Psionic Power Level +1.0)
    assert dna.get(PSYKER_POWER_LEVEL) == 1.0, f"Expected 1.0, got {dna.get(PSYKER_POWER_LEVEL)}"
    # Verify Veteran Crew (Experience 1.0 * 1.5 = 1.5)
    assert dna.get(CREW_EXPERIENCE) == 1.5, f"Expected 1.5, got {dna.get(CREW_EXPERIENCE)}"
    print("SUCCESS: Eternal Crusade DNA applied correctly.")
    
    # 2. Test Eternal Crusade (Ship with Traits)
    print("\n[Test 2] Eternal Crusade - Ship DNA Mapping")
    set_active_universe("eternal_crusade")
    
    # Simulate a Eternal Crusade Ship
    ship = Ship(
        name="Solar Cruiser",
        ma=30, md=30,
        hp=2000, 
        armor=50,
        damage=0,
        abilities={"Tags": ["Ship"]},
        shield=1000,
        movement_points=3,
        traits=["Cloaked Hunter"],
        faction="Solar_Hegemony"
    )
    UnitFactory._finalize_unit(ship)
    
    dna = ship.universal_stats
    print(f"Unit: {ship.name}")
    print(f"Traits: {ship.traits}")
    print(f"DNA [HULL_STRUCTURAL_INTEGRITY]: {dna.get(HULL_STRUCTURAL_INTEGRITY)}")
    print(f"DNA [STEALTH_RATING] (from Cloaked Hunter): {dna.get(STEALTH_RATING)}")
    
    # HP mapping: 2000 * 10 = 20000
    assert dna.get(HULL_STRUCTURAL_INTEGRITY) == 20000.0
    # Cloaked Hunter mapping: Stealth +5.0 (Additive now)
    assert dna.get(STEALTH_RATING) == 5.0
    print("SUCCESS: Eternal Crusade Ship DNA applied correctly.")
    
    print("\nALL DNA SYSTEM VERIFICATION TESTS PASSED!")

if __name__ == "__main__":
    try:
        verify_dna_system()
    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
