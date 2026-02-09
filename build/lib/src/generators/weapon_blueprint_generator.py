
import json
import os
import random

# Configuration
OUTPUT_FILE = "universes/base/weapons/base_weapon_blueprints.json"

# Combinatorial Data
SIZES = ["Light", "Standard", "Heavy", "Super-Heavy", "Titan-Class"]
VARIANTS = ["Rapid Fire", "Sniper", "Blast", "Twin-Linked", "Overcharged", "Compact", "Master-Crafted"]

PATTERNS = {
    "las": {
        "name_root": "Las",
        "desc_root": "Laser weapon",
        "category": "Energy",
        "tags": ["energy", "laser"],
        "base_stats": {"range": 24, "strength": 3, "ap": 0, "attacks": 1},
        "color": "Red"
    },
    "bolter": {
        "name_root": "Bolt",
        "desc_root": "Rocket-propelled explosive rounds",
        "category": "Ballistic",
        "tags": ["kinetic", "explosive"],
        "base_stats": {"range": 24, "strength": 4, "ap": -1, "attacks": 2},
        "color": "Metal"
    },
    "plasma": {
        "name_root": "Plasma",
        "desc_root": "Superheated matter projector",
        "category": "Energy",
        "tags": ["energy", "plasma", "high_damage"],
        "base_stats": {"range": 24, "strength": 7, "ap": -3, "attacks": 1},
        "color": "Blue"
    },
    "melta": {
        "name_root": "Melta",
        "desc_root": "Thermal agitation beam",
        "category": "Thermal",
        "tags": ["thermal", "melta", "anti_tank"],
        "base_stats": {"range": 12, "strength": 8, "ap": -4, "attacks": 1},
        "color": "Orange"
    },
    "gauss": {
        "name_root": "Gauss",
        "desc_root": "Magnetic molecular flayer",
        "category": "Exotic",
        "tags": ["exotic", "gauss", "rending"],
        "base_stats": {"range": 24, "strength": 5, "ap": -2, "attacks": 2},
        "color": "Green"
    },
    "tesla": {
        "name_root": "Tesla",
        "desc_root": "Arcing lightning projector",
        "category": "Energy",
        "tags": ["energy", "tesla", "arcing"],
        "base_stats": {"range": 18, "strength": 5, "ap": 0, "attacks": 3},
        "color": "Blue-White"
    },
    "rad": {
        "name_root": "Rad",
        "desc_root": "Radioactive emitter",
        "category": "Exotic",
        "tags": ["radiation", "poison", "anti_infantry"],
        "base_stats": {"range": 18, "strength": 2, "ap": 0, "attacks": 1}, # Low Str, but poison handles dmg
        "color": "Sickly Green"
    },
    "grav": {
        "name_root": "Grav",
        "desc_root": "Gravimetric crusher",
        "category": "Exotic",
        "tags": ["gravimetric", "control", "anti_heavy"],
        "base_stats": {"range": 18, "strength": 5, "ap": -3, "attacks": 3},
        "color": "Black"
    },
    "volkite": {
        "name_root": "Volkite",
        "desc_root": "Thermal ray that combusts targets",
        "category": "Thermal",
        "tags": ["thermal", "volkite", "deflagrate"],
        "base_stats": {"range": 30, "strength": 6, "ap": -1, "attacks": 2},
        "color": "Red"
    },
    "rail": {
        "name_root": "Rail",
        "desc_root": "Hyper-velocity slug thrower",
        "category": "Ballistic",
        "tags": ["kinetic", "railgun", "long_range"],
        "base_stats": {"range": 60, "strength": 8, "ap": -3, "attacks": 1},
        "color": "Grey"
    },
    "phaser": {
        "name_root": "Phaser",
        "desc_root": "Phased energy beam",
        "category": "Energy",
        "tags": ["energy", "phaser", "accurate"],
        "base_stats": {"range": 30, "strength": 5, "ap": -2, "attacks": 2},
        "color": "Orange"
    },
    "disruptor": {
        "name_root": "Disruptor",
        "desc_root": "Matter destabilizer",
        "category": "Energy",
        "tags": ["energy", "disruptor", "brutal"],
        "base_stats": {"range": 18, "strength": 6, "ap": -3, "attacks": 1},
        "color": "Green"
    },
    "ion": {
        "name_root": "Ion",
        "desc_root": "Ionized particle stream",
        "category": "Energy",
        "tags": ["energy", "ion", "emp"],
        "base_stats": {"range": 36, "strength": 7, "ap": -1, "attacks": 3},
        "color": "Blue"
    },
    "polaron": {
        "name_root": "Polaron",
        "desc_root": "Polaron particle beam",
        "category": "Energy",
        "tags": ["energy", "polaron", "shield_piercing"],
        "base_stats": {"range": 28, "strength": 6, "ap": -2, "attacks": 2},
        "color": "Purple"
    },
    "stubber": {
        "name_root": "Stub",
        "desc_root": "Solid projectile machine gun",
        "category": "Ballistic",
        "tags": ["kinetic", "rapid_fire", "cheap"],
        "base_stats": {"range": 36, "strength": 3, "ap": 0, "attacks": 4},
        "color": "Grey"
    },
    "autocannon": {
        "name_root": "Autocannon",
        "desc_root": "Large caliber automatic cannon",
        "category": "Ballistic",
        "tags": ["kinetic", "heavy", "reliable"],
        "base_stats": {"range": 48, "strength": 7, "ap": -1, "attacks": 2},
        "color": "Grey"
    },
    "missile": {
        "name_root": "Missile",
        "desc_root": "Guided warhead",
        "category": "Missile",
        "tags": ["missile", "explosive", "guided"],
        "base_stats": {"range": 48, "strength": 8, "ap": -2, "attacks": 1},
        "color": "White"
    },
    "flamer": {
        "name_root": "Flamer",
        "desc_root": "Chemical INCENDIARY projector",
        "category": "Thermal",
        "tags": ["thermal", "incendiary", "area"],
        "base_stats": {"range": 8, "strength": 4, "ap": 0, "attacks": 6}, # Hit auto
        "color": "Orange"
    },
    "sonic": {
        "name_root": "Sonic",
        "desc_root": "Sound wave projector",
        "category": "Exotic",
        "tags": ["sonic", "ignore_cover", "disruptor"],
        "base_stats": {"range": 24, "strength": 4, "ap": -1, "attacks": 3},
        "color": "Pink"
    },
     "tachyon": {
        "name_root": "Tachyon",
        "desc_root": "Faster-than-light particle lance",
        "category": "Exotic",
        "tags": ["energy", "tachyon", "sniper"],
        "base_stats": {"range": 100, "strength": 10, "ap": -5, "attacks": 1},
        "color": "Blue"
    }
}

def generate():
    blueprints = {}
    
    count = 0
    for key, template in PATTERNS.items():
        base_stats = template["base_stats"]
        
        # 1. Base Version
        bp_id = f"base_{key}_weapon"
        blueprints[bp_id] = {
            "name": f"Standard {template['name_root']} Weapon",
            "category": template["category"],
            "description": f"Standard {template['desc_root']}.",
            "stats": base_stats,
            "tags": template["tags"]
        }
        count += 1
        
        # 2. Generate Size Variations (Light, Heavy, Titan)
        for size in SIZES:
            size_slug = size.lower().replace("-", "_")
            new_id = f"base_{key}_{size_slug}"
            
            # Modifier logic
            mult_str = 1.0
            mult_range = 1.0
            mult_attacks = 1.0
            mod_ap = 0
            
            if size == "Light":
                mult_str = 0.8
                mult_range = 0.8
                mult_attacks = 1.5
                desc_pre = "Light-weight"
            elif size == "Standard":
                continue # Already done as base
            elif size == "Heavy":
                mult_str = 1.25
                mult_range = 1.5
                mult_attacks = 0.75 # Slower fire
                mod_ap = -1
                desc_pre = "Heavy mounted"
            elif size == "Super-Heavy":
                mult_str = 1.5
                mult_range = 1.8
                mult_attacks = 0.5
                mod_ap = -2
                desc_pre = "Super-heavy"
            elif size == "Titan-Class":
                mult_str = 2.0
                mult_range = 2.5
                mult_attacks = 1.0 # Titans fire big guns normally
                mod_ap = -4
                desc_pre = "God-engine class"
            
            new_stats = {
                "range": max(1, int(base_stats["range"] * mult_range)),
                "strength": max(1, int(base_stats["strength"] * mult_str)),
                "ap": min(0, base_stats["ap"] + mod_ap),
                "attacks": max(1, int(base_stats["attacks"] * mult_attacks))
            }
            
            tags = list(template["tags"])
            if size in ["Heavy", "Super-Heavy", "Titan-Class"]:
                tags.append("heavy")
            if size == "Titan-Class":
                tags.append("macro")
            
            blueprints[new_id] = {
                "name": f"{size} {template['name_root']} {get_suffix(key)}",
                "category": template["category"],
                "description": f"{desc_pre} {template['desc_root']}.",
                "stats": new_stats,
                "tags": tags
            }
            count += 1
            
            # 3. Generate Variants for Standard and Heavy
            if size in ["Standard", "Heavy"]:
                for variant in VARIANTS:
                    var_slug = variant.lower().replace(" ", "_").replace("-", "_")
                    var_id = f"base_{key}_{size_slug}_{var_slug}"
                    
                    var_stats = new_stats.copy()
                    var_tags = list(tags)
                    
                    if variant == "Rapid Fire":
                        var_stats["attacks"] = int(var_stats["attacks"] * 1.5) + 1
                        var_stats["range"] = int(var_stats["range"] * 0.8)
                        var_tags.append("rapid_fire")
                    elif variant == "Sniper":
                        var_stats["range"] = int(var_stats["range"] * 1.5)
                        var_stats["attacks"] = 1
                        var_stats["ap"] -= 1
                        var_tags.append("accurate")
                    elif variant == "Blast":
                        var_stats["attacks"] = max(1, int(var_stats["attacks"] * 0.5))
                        var_stats["strength"] = int(var_stats["strength"] * 1.2)
                        var_tags.append("blast")
                    elif variant == "Twin-Linked":
                        var_stats["attacks"] *= 2
                        var_tags.append("twin_linked")
                    elif variant == "Overcharged":
                        var_stats["strength"] = int(var_stats["strength"] * 1.3)
                        var_stats["ap"] -= 1
                        var_tags.append("hazardous")
                        var_tags.append("overcharged")
                    elif variant == "Compact":
                        var_stats["range"] = int(var_stats["range"] * 0.6)
                        var_tags.append("assault")
                    elif variant == "Master-Crafted":
                        var_stats["strength"] += 1
                        var_stats["ap"] -= 1
                        var_tags.append("master_crafted")

                    blueprints[var_id] = {
                        "name": f"{variant} {size} {template['name_root']} {get_suffix(key)}",
                        "category": template["category"],
                        "description": f"{variant} modified {template['desc_root']}.",
                        "stats": var_stats,
                        "tags": var_tags
                    }
                    count += 1

    print(f"Generated {count} distinct weapon blueprints.")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(blueprints, f, indent=4)
    print(f"Saved to {OUTPUT_FILE}")

def get_suffix(key):
    if key in ["las", "plasma", "melta", "ion", "polaron", "phaser", "volkite", "tachyon"]:
        return "Cannon" if random.random() < 0.5 else "Projector"
    elif key in ["bolter", "stubber", "autocannon", "rail", "gauss"]:
        return "Gun" if random.random() < 0.5 else "Rifle"
    elif key == "missile":
        return "Launcher"
    elif key == "tesla":
        return "Coil"
    return "System"

if __name__ == "__main__":
    generate()
