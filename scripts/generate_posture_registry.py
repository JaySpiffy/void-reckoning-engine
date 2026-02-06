import json
import os

def generate_registry():
    archetypes = {
        "BALANCED": {
            "name": "Balanced",
            "weights": {"income": 1.0, "strategic": 1.0, "distance": 1.0, "threat": 1.0, "capital": 1.0, "weakness": 1.0, "expansion_bias": 1.0},
            "personality_mods": {}
        },
        "BLITZ": {
            "name": "Blitz",
            "weights": {"income": 0.5, "strategic": 1.5, "distance": 0.2, "threat": 0.5, "capital": 4.0, "weakness": 2.0, "expansion_bias": 2.5},
            "personality_mods": {"aggression": 1.5}
        },
        "TURTLE": {
            "name": "Turtle",
            "weights": {"income": 1.2, "strategic": 2.5, "distance": 4.0, "threat": 2.0, "capital": 0.2, "weakness": 0.2, "expansion_bias": 0.1},
            "personality_mods": {"aggression": 0.6}
        },
        "BOOM": {
            "name": "Boom",
            "weights": {"income": 3.0, "strategic": 0.5, "distance": 1.5, "threat": 1.5, "capital": 0.1, "weakness": 1.0, "expansion_bias": 1.5},
            "personality_mods": {"expansion_bias": 1.5}
        },
        "PIONEER": {
            "name": "Pioneer",
            "weights": {"income": 0.5, "strategic": 1.0, "distance": 1.0, "threat": 1.0, "capital": 0.1, "weakness": 1.0, "expansion_bias": 3.0, "suitability": 3.0},
            "personality_mods": {"expansion_bias": 2.0}
        },
        "RAID": {
            "name": "Raid",
            "weights": {"income": 0.2, "strategic": 0.5, "distance": 0.5, "threat": 0.1, "capital": 0.5, "weakness": 4.0, "expansion_bias": 0.5},
            "personality_mods": {"aggression": 1.2}
        },
        "DIPLO": {
            "name": "Diplomatic",
            "weights": {"income": 1.0, "strategic": 1.0, "distance": 1.0, "threat": 0.5, "capital": 0.1, "weakness": 0.1, "expansion_bias": 0.2},
            "personality_mods": {"cohesiveness": 1.5}
        },
        "TOTAL": {
            "name": "Total War",
            "weights": {"income": 0.1, "strategic": 3.0, "distance": 0.1, "threat": 0.0, "capital": 5.0, "weakness": 2.0, "expansion_bias": 3.0},
            "personality_mods": {"aggression": 2.0}
        },
        "ATTRIT": {
            "name": "Attrition",
            "weights": {"income": 1.0, "strategic": 2.0, "distance": 1.0, "threat": 0.8, "capital": 1.0, "weakness": 1.0, "expansion_bias": 0.8},
            "personality_mods": {"patience": 1.5}
        },
        "ADAPT": {
            "name": "Adaptive",
            "weights": {"income": 1.0, "strategic": 1.5, "distance": 1.5, "threat": 1.0, "capital": 1.0, "weakness": 1.5, "expansion_bias": 1.0},
            "personality_mods": {"adaptation_speed": 2.0}
        },
        "ELITE": {
            "name": "Elite",
            "weights": {"income": 1.5, "strategic": 1.0, "distance": 1.0, "threat": 0.5, "capital": 1.5, "weakness": 0.5, "expansion_bias": 0.5},
            "personality_mods": {"quality_bias": 1.5}
        },
        "SWARM": {
            "name": "Swarm",
            "weights": {"income": 0.5, "strategic": 1.0, "distance": 0.5, "threat": 2.0, "capital": 1.0, "weakness": 3.0, "expansion_bias": 3.0},
            "personality_mods": {"quantity_bias": 2.0}
        }
    }

    postures = {
        "BALANCED": {"archetype": "BALANCED", "general": True, "description": "Standard balanced operation."},
        "BLITZ": {"archetype": "BLITZ", "general": True, "description": "Rapid offensive.", "triggers": {"military_ratio": 1.3}},
        "TURTLE": {"archetype": "TURTLE", "general": True, "description": "Defensive posture.", "triggers": {"econ_state": "STRESSED"}},
        "BOOM": {"archetype": "BOOM", "general": True, "description": "Economic expansion.", "triggers": {"is_at_war": False}},
        "PIONEER": {"archetype": "PIONEER", "general": True, "description": "City founding focus.", "triggers": {"is_at_war": False}}
    }

    # Generate 100 more postures (Total 101)
    archetype_keys = list(archetypes.keys())
    
    # 50 General Postures
    for i in range(1, 51):
        arch = archetype_keys[i % len(archetype_keys)]
        p_id = f"GEN_{i:03d}"
        postures[p_id] = {
            "archetype": arch,
            "general": True,
            "description": f"General Posture Variations {i} based on {arch} archetype."
        }

    # 50 Faction-Specific Postures
    factions = ["Bio-Tide_Collective", "Templars_of_the_Flux", "Algorithmic_Hierarchy", "Scavenger_Clans", "Ancient_Guardians"]
    for i in range(1, 51):
        arch = archetype_keys[(i + 5) % len(archetype_keys)]
        fac = factions[i % len(factions)]
        p_id = f"FAC_{fac[:3].upper()}_{i:03d}"
        postures[p_id] = {
            "archetype": arch,
            "general": False,
            "faction_affinity": [fac],
            "description": f"Specialized {fac} posture {i} focusing on {arch} mechanics."
        }

    registry = {
        "version": "1.0",
        "archetypes": archetypes,
        "postures": postures
    }

    path = "universes/void_reckoning/ai/posture_registry.json"
    with open(path, 'w') as f:
        json.dump(registry, f, indent=2)
    print(f"Generated {len(postures)} postures in {path}")

if __name__ == "__main__":
    generate_registry()
