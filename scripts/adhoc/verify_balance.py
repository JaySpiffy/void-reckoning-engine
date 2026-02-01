
from src.core.weapon_synthesizer import synthesize_weapon_stats
from src.core.elemental_signature import ATOM_MASS, ATOM_ENERGY, ATOM_VOLATILITY, ATOM_FOCUS, ATOM_INFORMATION, ATOM_COHESION, ATOM_STABILITY, ATOM_FREQUENCY, ATOM_AETHER, ATOM_WILL

# Sample DNA from Iron Vanguard (from logs/roster)
# Hammer Class (Frigate)
iron_vanguard_dna = {
    ATOM_MASS: 19.35,
    ATOM_ENERGY: 10.75,
    ATOM_COHESION: 26.9,
    ATOM_VOLATILITY: 4.3,
    ATOM_STABILITY: 10.75,
    ATOM_FOCUS: 4.3,
    ATOM_FREQUENCY: 4.3,
    ATOM_AETHER: 4.3,
    ATOM_WILL: 10.75,
    ATOM_INFORMATION: 4.3
}

# Ancient Guardians (from logs/roster - inferred)
# High Stability/Focus usually
ancient_guardians_dna = {
    ATOM_MASS: 10.0,
    ATOM_ENERGY: 40.0,
    ATOM_COHESION: 10.0,
    ATOM_VOLATILITY: 5.0,
    ATOM_STABILITY: 40.0,
    ATOM_FOCUS: 20.0,
    ATOM_FREQUENCY: 10.0,
    ATOM_AETHER: 5.0,
    ATOM_WILL: 5.0,
    ATOM_INFORMATION: 20.0
}

def test_synthesis(name, dna):
    print(f"\n--- {name} ---")
    stats = synthesize_weapon_stats(dna)
    print("Stats:")
    for k, v in stats.items():
        if k != "raw_potency":
            print(f"  {k}: {v}")
    print("Raw:")
    for k, v in stats["raw_potency"].items():
        print(f"  {k}: {v:.2f}")

if __name__ == "__main__":
    test_synthesis("Iron Vanguard (Frigate)", iron_vanguard_dna)
    test_synthesis("Ancient Guardians (Archetype)", ancient_guardians_dna)
