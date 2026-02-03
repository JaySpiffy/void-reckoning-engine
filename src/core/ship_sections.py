from typing import Dict, List, Any

# Slot Type definitions:
# S: Small (Light Weapons/PD)
# M: Medium (Standard Weapons)
# L: Large (Heavy Weapons)
# X: Extra-Large (Spinal/Super-Heavy)
# P: Point Defense
# G: Guided (Torpedoes/Missiles)
# H: Hangar (Strike Craft)
# D: Defense (Armor/Shields)
# E: Engine
# T: Tractor Beam
# I: Interdiction Field

SECTIONS = {
    "Corvette": {
        "Integrated": {
            "Brawler": ["S", "S", "D", "E"],
            "Intercepter": ["S", "P", "D", "E"],
            "Missile": ["G", "D", "E"]
        }
    },
    "Frigate": {
        "Integrated": {
            "Artillery": ["M", "S", "D", "D", "E"],
            "Escort": ["S", "S", "P", "D", "D", "E"],
            "Torpedo": ["G", "G", "D", "D", "E"]
        }
    },
    "Destroyer": {
        "Bow": {
            "Artillery": ["L", "M", "S", "S"],
            "Brawler": ["M", "M", "M", "S", "S"],
            "Picket": ["P", "P", "P", "S"]
        },
        "Stern": {
            "Engine": ["D", "D", "E"],
            "Weapon": ["M", "M", "D", "E"]
        }
    },
    "Cruiser": {
        "Bow": {
            "Artillery": ["L", "L", "M", "M"],
            "Carrier": ["H", "H", "S", "P"],
            "Torpedo": ["G", "G", "G", "M"]
        },
        "Core": {
            "Broadside": ["M", "M", "M", "M", "M", "M"],
            "Hangar": ["H", "H", "D", "D", "D", "D"],
            "Sentinel": ["P", "P", "P", "P", "P", "P"],
            "Artillery": ["L", "L", "D", "D"]
        },
        "Stern": {
            "Engine": ["D", "D", "E", "E"],
            "Weapon": ["M", "M", "M", "M", "E"],
            "Interdictor": ["I", "D", "D", "E", "E"]
        }
    },
    "Battleship": {
        "Bow": {
            "Spinal": ["X", "L", "L", "L"],
            "Artillery": ["L", "L", "L", "L", "L"],
            "Hangar": ["H", "H", "H", "H", "P"]
        },
        "Core": {
            "Artillery": ["L", "L", "L", "L", "L", "L", "D", "D", "D", "D"],
            "Carrier": ["H", "H", "H", "H", "H", "H", "D", "D", "D", "D"],
            "Brawler": ["M", "M", "M", "M", "M", "M", "M", "M", "D", "D"]
        },
        "Stern": {
            "Artillery": ["L", "L", "L", "L", "E", "E"],
            "Engine": ["D", "D", "D", "D", "E", "E"],
            "Interdictor": ["I", "I", "D", "D", "D", "D", "E", "E"]
        }
    },
    "Titan": {
        "Bow": {
            "Perdition": ["X", "X", "L", "L", "L", "L", "L", "L"],
            "Heavy Artillery": ["L", "L", "L", "L", "L", "L", "L", "L", "L", "L"]
        },
        "Core": {
            "Bastion": ["D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D"],
            "Massive Artillery": ["L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "D", "D"],
            "Hangar Deck": ["H", "H", "H", "H", "H", "H", "H", "H", "D", "D", "D", "D", "D", "D"]
        },
        "Stern": {
            "Fortress": ["D", "D", "D", "D", "D", "D", "D", "D", "E", "E", "E", "E"],
            "Tractor": ["T", "T", "D", "D", "D", "D", "D", "D", "E", "E", "E", "E"]
        }
    },
    "Massive": { # For World Devastators, Motherships, 64-slot Target
        "Bow": {
            "Super-Artillery": ["X", "X", "X", "X", "L", "L", "L", "L", "L", "L", "L", "L", "P", "P", "P", "P"],
            "Invasion": ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H", "H", "H", "L", "L", "L", "L"]
        },
        "Core": {
            "Armored Hive": ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H", "H", "H", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D"],
            "Dreadnought": ["X", "X", "X", "X", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "L", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D"]
        },
        "Stern": {
            "Propulsion Hub": ["E", "E", "E", "E", "E", "E", "E", "E", "D", "D", "D", "D", "D", "D", "D", "D"]
        }
    }
}

def get_sections_for_hull(hull_class: str) -> List[str]:
    """Returns the names of the sections required for this hull."""
    if hull_class in ["Corvette", "Frigate"]:
        return ["Integrated"]
    if hull_class == "Destroyer":
        return ["Bow", "Stern"]
    return ["Bow", "Core", "Stern"]

def select_section(hull_class: str, pos: str, role: str) -> Dict[str, Any]:
    """Picks a section configuration based on role and position."""
    # Map high level roles to section roles
    hull_data = SECTIONS.get(hull_class, SECTIONS.get("Massive")) # Fallback to Massive for specials
    if pos not in hull_data:
        return {"name": "Standard", "slots": ["M", "D"]}
    
    options = hull_data[pos]
    
    # Simple matching for now
    if role in options:
        return {"name": role, "slots": options[role]}
    
    # Fallback to first option if role not found
    first_role = list(options.keys())[0]
    return {"name": first_role, "slots": options[first_role]}
