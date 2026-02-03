import json
import random
import os

# Thematic Word Pools
PREFIXES = [
    "Experimental", "Ancient", "Venerable", "Warp-Touched", "Corrupted", "Sanctified",
    "Siege", "Assault", "Vanguard", "Covert", "Elite", "Tactical", "Strategic",
    "Omni", "Hyper", "Proto", "Neo", "Arcane", "Cyber", "Bio", "Plasma", "Thermal",
    "Void", "Spectral", "Ghost", "Iron", "Storm", "Thunder", "Frost", "Flame"
]

NOUNS = [
    "Pulse", "Beam", "Cloud", "Strike", "Array", "protocol", "overdrive", "burst",
    "resonance", "matrix", "field", "surge", "shroud", "flare", "wave", "impact",
    "salvo", "barrage", "interdictor", "harmonizer", "disruptor", "catalyst",
    "effector", "stabilizer", "vortex", "anchor", "relay", "beacon"
]

GROUND_ARCHETYPES = [
    {"name": "Frag Grenade", "payload": "aoe_damage", "radius": 1, "damage": 20, "base_id": "frag_grenade"},
    {"name": "Melta Mine", "payload": "damage", "damage": 100, "base_id": "melta_mine"},
    {"name": "Med-Kit", "payload": "heal", "heal": 30, "base_id": "med_kit"},
    {"name": "Stim-Shot", "payload": "buff", "effects": {"speed_mult": 1.5, "duration": 5}, "base_id": "stim_shot"},
    {"name": "Suppression Fire", "payload": "debuff", "effects": {"accuracy_mult": 0.5, "duration": 5}, "base_id": "suppress"},
    {"name": "Entrench", "payload": "buff", "effects": {"armor_mult": 2.0, "duration": 10}, "base_id": "entrench"},
    {"name": "Charge", "payload": "charge", "duration": 5, "base_id": "charge"},
    {"name": "Sniper Shot", "payload": "damage", "damage": 50, "range": 30, "base_id": "sniper"},
    {"name": "Mortar Strike", "payload": "aoe_damage", "radius": 2, "damage": 40, "range": 40, "base_id": "mortar"},
    {"name": "Aura of Faith", "payload": "buff", "effects": {"morale_regen": 2.0, "duration": 15}, "base_id": "faith_aura"}
]

SPACE_ARCHETYPES = [
    {"name": "Shield Overload", "payload": "buff", "effects": {"shield_regen_mult": 3.0, "duration": 10}, "base_id": "shield_overload"},
    {"name": "Weapon Burnout", "payload": "buff", "effects": {"damage_mult": 2.0, "duration": 5}, "base_id": "weapon_burnout"},
    {"name": "Micro-Jump", "payload": "teleport", "range": 50, "base_id": "micro_jump"},
    {"name": "Boarding Action", "payload": "capture", "capture_threshold": 0.3, "base_id": "boarding"},
    {"name": "Tractor Beam", "payload": "debuff", "effects": {"speed_mult": 0.0, "duration": 8}, "base_id": "tractor"},
    {"name": "Gravity Well", "payload": "debuff", "effects": {"speed_mult": 0.5, "duration": 20}, "base_id": "gravity_well"},
    {"name": "Sensor Jammer", "payload": "buff", "effects": {"stealth": True, "duration": 15}, "base_id": "jam"},
    {"name": "Nova Cannon", "payload": "aoe_damage", "radius": 5, "damage": 500, "range": 100, "base_id": "nova"},
    {"name": "Repair Drones", "payload": "heal", "heal": 100, "base_id": "repair"},
    {"name": "Plasma Burst", "payload": "aoe_damage", "radius": 3, "damage": 150, "base_id": "plasma_burst"}
]

def generate_abilities(archetypes, domain, count=1000):
    registry = {}
    base_ids = set()
    
    for i in range(count):
        # Pick a base archetype
        arch = random.choice(archetypes).copy()
        
        # Unique Name & ID
        prefix = random.choice(PREFIXES)
        noun = random.choice(NOUNS)
        name = f"{prefix} {arch['name']} {noun}"
        base_id = f"{domain}_{arch['base_id']}_{i}"
        
        # Ensure ID uniqueness (though 'i' handles it mostly)
        base_ids.add(base_id)
        
        # Generate 5 tiers
        for tier in range(1, 6):
            tier_id = f"{base_id}_v{tier}"
            tier_name = f"{name} (Mark {tier})"
            
            # Scale stats based on tier
            tier_def = arch.copy()
            tier_def["id"] = tier_id
            tier_def["name"] = tier_name
            tier_def["category"] = domain
            tier_def["tier"] = tier
            
            # Basic Scaling
            scale = 1.0 + (tier - 1) * 0.5 # 1.0, 1.5, 2.0, 2.5, 3.0
            
            if "damage" in tier_def: tier_def["damage"] = int(tier_def["damage"] * scale)
            if "heal" in tier_def: tier_def["heal"] = int(tier_def["heal"] * scale)
            if "radius" in tier_def: tier_def["radius"] = int(tier_def["radius"] * (1.0 + (tier-1)*0.2))
            if "effects" in tier_def:
                for k, v in tier_def["effects"].items():
                    if isinstance(v, float):
                        # Some multipliers should go up (damage), some down (speed debuff)
                        if v > 1.0: tier_def["effects"][k] = round(1.0 + (v-1.0) * scale, 2)
                        elif v < 1.0: tier_def["effects"][k] = round(max(0.01, 1.0 - (1.0 - v) * scale), 2)
                    elif isinstance(v, (int, float)):
                        tier_def["effects"][k] = round(v * scale, 1)

            registry[tier_id] = tier_def
            
    return registry

def main():
    print("Generating Massive Ability Registries...")
    
    space_registry = generate_abilities(SPACE_ARCHETYPES, "space", count=1000)
    ground_registry = generate_abilities(GROUND_ARCHETYPES, "ground", count=1000)
    
    # Save to JSON
    os.makedirs("src/combat/abilities", exist_ok=True)
    
    with open("src/combat/abilities/space_massive.json", "w") as f:
        json.dump(space_registry, f, indent=2)
        
    with open("src/combat/abilities/ground_massive.json", "w") as f:
        json.dump(ground_registry, f, indent=2)
        
    print(f"Generated {len(space_registry)} space abilities and {len(ground_registry)} ground abilities.")

if __name__ == "__main__":
    main()
