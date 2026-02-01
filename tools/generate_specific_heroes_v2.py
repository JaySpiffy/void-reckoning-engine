import os
import json
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")

# Hero Definitions with Manual DNA overrides
HERO_DEFINITIONS = {
    "Zealot_Legions": [
        {
            "name": "High Crusader",
            "tier": 5, "cost": 12000, "role": "hero", "desc": "Supreme melee commander of the Crusade.",
            "stats": { "hp": 500, "armor": 150, "damage": 200, "speed": 6 },
            "dna": { "atom_will": 40.0, "atom_aether": 30.0, "atom_mass": 20.0, "atom_volatility": 10.0 }
        },
        {
            "name": "Arch-Confessor",
            "tier": 4, "cost": 6000, "role": "commander", "desc": "Holy orator who buffs nearby units.",
            "stats": { "hp": 250, "armor": 60, "damage": 80, "speed": 5 },
            "dna": { "atom_will": 50.0, "atom_aether": 20.0, "atom_cohesion": 20.0, "atom_information": 10.0 }
        },
        {
            "name": "Saint's Avatar",
            "tier": 5, "cost": 15000, "role": "titan", "desc": "Living manifestation of the Emperor's Will.",
            "stats": { "hp": 1200, "armor": 200, "damage": 400, "speed": 8 },
            "dna": { "atom_aether": 40.0, "atom_will": 40.0, "atom_energy": 20.0 }
        }
    ],
    "Ascended_Order": [
        {
            "name": "Aether Sage",
            "tier": 5, "cost": 10000, "role": "hero", "desc": "Master of the Warp and Psionic arts.",
            "stats": { "hp": 300, "armor": 40, "damage": 300, "speed": 8 },
            "dna": { "atom_aether": 50.0, "atom_focus": 30.0, "atom_will": 20.0 }
        },
        {
            "name": "Mind-Weaver",
            "tier": 4, "cost": 6000, "role": "specialist", "desc": "Telepathic controller of enemies.",
            "stats": { "hp": 200, "armor": 30, "damage": 100, "speed": 6 },
            "dna": { "atom_information": 40.0, "atom_focus": 40.0, "atom_will": 20.0 }
        }
    ],
    "Hive_Swarm": [
        {
            "name": "Brood Tyrant",
            "tier": 5, "cost": 11000, "role": "hero", "desc": "Synapse creature directing the swarm.",
            "stats": { "hp": 600, "armor": 100, "damage": 180, "speed": 9 },
            "dna": { "atom_will": 40.0, "atom_frequency": 40.0, "atom_mass": 20.0 }
        },
        {
            "name": "Apex Predator",
            "tier": 5, "cost": 14000, "role": "titan", "desc": "Massive biological siege engine.",
            "stats": { "hp": 2000, "armor": 150, "damage": 350, "speed": 10 },
            "dna": { "atom_mass": 40.0, "atom_volatility": 40.0, "atom_energy": 20.0 }
        }
    ],
    "Iron_Vanguard": [
        {
            "name": "Iron Lord",
            "tier": 5, "cost": 13000, "role": "hero", "desc": "Master of Siege Warfare.",
            "stats": { "hp": 800, "armor": 250, "damage": 150, "speed": 4 },
            "dna": { "atom_mass": 40.0, "atom_stability": 40.0, "atom_cohesion": 20.0 }
        },
        {
            "name": "Forge Master",
            "tier": 4, "cost": 7000, "role": "commander", "desc": "Repairs and fortifies machines.",
            "stats": { "hp": 400, "armor": 100, "damage": 80, "speed": 5 },
            "dna": { "atom_focus": 40.0, "atom_mass": 40.0, "atom_energy": 20.0 }
        }
    ],
    "Cyber_Synod": [
        {
            "name": "Prime Calculator",
            "tier": 5, "cost": 12000, "role": "hero", "desc": "Supreme logic engine.",
            "stats": { "hp": 500, "armor": 80, "damage": 200, "speed": 10 },
            "dna": { "atom_information": 60.0, "atom_focus": 20.0, "atom_energy": 20.0 }
        },
        {
            "name": "Logic Titan",
            "tier": 5, "cost": 15000, "role": "titan", "desc": "Walking data-center of death.",
            "stats": { "hp": 4000, "armor": 300, "damage": 500, "speed": 5 },
            "dna": { "atom_energy": 40.0, "atom_stability": 40.0, "atom_information": 20.0 }
        }
    ],
    "Void_Corsairs": [
        {
            "name": "Void Prince",
            "tier": 5, "cost": 11000, "role": "hero", "desc": "Master of the Hit and Run.",
            "stats": { "hp": 300, "armor": 50, "damage": 250, "speed": 20 },
            "dna": { "atom_frequency": 60.0, "atom_volatility": 20.0, "atom_energy": 20.0 }
        },
        {
            "name": "Shadow Baron",
            "tier": 4, "cost": 7000, "role": "commander", "desc": "Stealth fleet commander.",
            "stats": { "hp": 200, "armor": 40, "damage": 150, "speed": 15 },
            "dna": { "atom_frequency": 50.0, "atom_focus": 30.0, "atom_aether": 20.0 }
        }
    ],
    "Solar_Hegemony": [
        {
            "name": "Grand Marshal",
            "tier": 5, "cost": 10000, "role": "hero", "desc": "Supreme commander of the Hegemony.",
            "stats": { "hp": 400, "armor": 100, "damage": 120, "speed": 6 },
            "dna": { "atom_will": 30.0, "atom_focus": 30.0, "atom_cohesion": 40.0 }
        },
        {
            "name": "High Diplomat",
            "tier": 4, "cost": 5000, "role": "commander", "desc": "Unity through words or force.",
            "stats": { "hp": 150, "armor": 40, "damage": 50, "speed": 5 },
            "dna": { "atom_information": 50.0, "atom_cohesion": 50.0 }
        }
    ],
    "Rift_Daemons": [
        {
            "name": "Warp Lord",
            "tier": 5, "cost": 13000, "role": "hero", "desc": "Daemon Prince of the Rift.",
            "stats": { "hp": 800, "armor": 80, "damage": 300, "speed": 12 },
            "dna": { "atom_aether": 60.0, "atom_volatility": 40.0 }
        },
        {
            "name": "Entropy Avatar",
            "tier": 5, "cost": 15000, "role": "titan", "desc": "Living storm of chaos.",
            "stats": { "hp": 5000, "armor": 50, "damage": 600, "speed": 8 },
            "dna": { "atom_volatility": 70.0, "atom_aether": 30.0 }
        }
    ],
    "Scavenger_Clans": [
        {
            "name": "Warlord",
            "tier": 5, "cost": 10000, "role": "hero", "desc": " Biggest and strongest Ork.",
            "stats": { "hp": 800, "armor": 120, "damage": 250, "speed": 7 },
            "dna": { "atom_volatility": 50.0, "atom_mass": 30.0, "atom_cohesion": 20.0 }
        },
        {
            "name": "Big Mek",
            "tier": 4, "cost": 6000, "role": "commander", "desc": "Builder of great machines.",
            "stats": { "hp": 400, "armor": 80, "damage": 120, "speed": 6 },
            "dna": { "atom_energy": 40.0, "atom_mass": 30.0, "atom_focus": 30.0 }
        }
    ],
    "Ancient_Guardians": [
        {
            "name": "Farseer",
            "tier": 5, "cost": 11000, "role": "hero", "desc": "Predicts the future of battle.",
            "stats": { "hp": 250, "armor": 40, "damage": 180, "speed": 10 },
            "dna": { "atom_focus": 50.0, "atom_aether": 30.0, "atom_will": 20.0 }
        },
        {
            "name": "Avatar of War",
            "tier": 5, "cost": 15000, "role": "titan", "desc": "Molten god of war.",
            "stats": { "hp": 1500, "armor": 200, "damage": 500, "speed": 9 },
            "dna": { "atom_energy": 40.0, "atom_volatility": 40.0, "atom_mass": 20.0 }
        }
    ]
}

def generate_heroes():
    if not os.path.exists(UNITS_DIR): os.makedirs(UNITS_DIR)

    for faction, heroes in HERO_DEFINITIONS.items():
        print(f"Generating Specific Heroes for {faction}...")
        
        hero_file = os.path.join(UNITS_DIR, f"{faction.lower()}_heroes.json")
        hero_data = []

        for h in heroes:
            # Complete the DNA (fill 0s)
            complete_dna = {
                "atom_mass": 0.0, "atom_energy": 0.0, "atom_cohesion": 0.0,
                "atom_volatility": 0.0, "atom_stability": 0.0, "atom_focus": 0.0,
                "atom_frequency": 0.0, "atom_aether": 0.0, "atom_will": 0.0,
                "atom_information": 0.0
            }
            # Merge manual DNA
            for k, v in h["dna"].items():
                complete_dna[k] = v
            
            # Normalize to 100
            total = sum(complete_dna.values())
            if total > 0:
                for k in complete_dna:
                    complete_dna[k] = round((complete_dna[k] / total) * 100.0, 2)
            
            unit_entry = {
                "name": h["name"],
                "blueprint_id": f"{faction.lower()}_{h['name'].lower().replace(' ', '_').replace('-', '_').replace("'", "")}",
                "type": "hero",
                "faction": faction,
                "tier": h["tier"],
                "cost": h["cost"],
                "base_stats": {
                    "role": h["role"],
                    "tier": h["tier"],
                    "hp": h["stats"]["hp"],
                    "armor": h["stats"]["armor"],
                    "damage": h["stats"]["damage"],
                    "speed": h["stats"].get("speed", 10),
                    "cost": h["cost"],
                    "keywords": f"hero unique {h['role']} tier{h['tier']}"
                },
                "elemental_dna": complete_dna,
                "source_universe": "eternal_crusade",
                "description": h["desc"],
                "hero": True,
                "unique": True,
                "traits": ["Trait_Fearless", "Trait_Hatred"] # Base hero traits, refine later if needed
            }
            hero_data.append(unit_entry)
            
        with open(hero_file, 'w') as f:
            json.dump(hero_data, f, indent=2)

if __name__ == "__main__":
    generate_heroes()
