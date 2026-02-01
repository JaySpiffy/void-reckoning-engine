import random

# Procedural Name Generation components
SYLLABLES_START = ["Ax", "Xan", "Vet", "Kry", "Zer", "Ome", "Tal", "Rax", "Vor", "Cyl", "Qua", "Zyn", "Kel", "Tho", "Myr"]
SYLLABLES_MID = ["a", "o", "i", "e", "u", "ar", "or", "in", "en", "un", "ra", "ro", "ri", "ka", "ko", "ki"]
SYLLABLES_END = ["bor", "nax", "tor", "lar", "ius", "ven", "zak", "rris", "tis", "sus", "lon", "gar", "thos", "kora", "zera"]

SYSTEM_PREFIXES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Theta", "Omicron", "Sigma", "Tau"]
SYSTEM_SUFFIXES = ["Major", "Minor", "Prime", "Secundus", "Tertius", "Sector", "Expanse", "Nebula", "Void", "Cluster"]

def generate_system_name(index, rng=random):
    """Generates a procedural alien/sci-fi system name."""
    roll = rng.random()
    
    if roll < 0.7:
        # Alien Name (2-3 syllables)
        name = rng.choice(SYLLABLES_START)
        if rng.random() > 0.5:
            name += rng.choice(SYLLABLES_MID)
        name += rng.choice(SYLLABLES_END)
        
        # Add a number sometimes
        if rng.random() > 0.8:
            name += f" {rng.choice(['Prime', 'VII', 'IX', 'IV', 'Major'])}"
        return name
    else:
        # Greek+Suffix
        prefix = rng.choice(SYSTEM_PREFIXES)
        suffix = rng.choice(SYSTEM_SUFFIXES)
        return f"{prefix} {suffix} {index}"
