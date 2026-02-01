import os
import json

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
FACTIONS_DIR = os.path.join(UNIVERSE_PATH, "factions")

# Ability Definitions with 100-point DNA Lenses and refined payloads
ABILITY_DEFINITIONS = {
    # --- Aether Powers (Psyker/Warp) ---
    "Ability_Psychic_Storm": {
        "name": "Psychic Storm",
        "description": "Unleash a torrent of psychic energy that damages all units in target area.",
        "manacost": 150, "cooldown": 120, "range": 300,
        "payload": { "target": "AOE", "radius": 100, "effect": "psychic_damage", "scaling": "atom_aether", "damage_base": 50, "damage_scaling": 1.5 },
        "faction_affinity": ["Ascended_Order", "Rift_Daemons", "Zealot_Legions"],
        "dna": { "atom_aether": 40.0, "atom_volatility": 30.0, "atom_will": 20.0, "atom_energy": 10.0 }
    },
    "Ability_Reality_Tear": {
        "name": "Reality Tear",
        "description": "Rips a hole in reality, summoning warp entities.",
        "manacost": 200, "cooldown": 180, "range": 500,
        "payload": { "target": "Point", "effect": "summon", "scaling": "atom_aether", "summon_count": 3, "duration": 60 },
        "faction_affinity": ["Rift_Daemons"],
        "dna": { "atom_aether": 50.0, "atom_volatility": 25.0, "atom_will": 15.0, "atom_focus": 10.0 }
    },
    "Ability_Mind_Shackles": {
        "name": "Mind Shackles",
        "description": "Target enemy unit is brought under your control.",
        "manacost": 120, "cooldown": 90, "range": 250,
        "payload": { "target": "Single", "effect": "mind_control", "scaling": "atom_will", "duration": 30, "check": "will_atom" },
        "faction_affinity": ["Ascended_Order", "Ancient_Guardians"],
        "dna": { "atom_aether": 35.0, "atom_will": 30.0, "atom_focus": 20.0, "atom_information": 15.0 }
    },
    "Ability_Warp_Jump": {
        "name": "Warp Jump",
        "description": "Teleport unit to a target location through the warp.",
        "manacost": 80, "cooldown": 45, "range": 600,
        "payload": { "target": "Self", "effect": "teleport", "scaling": "atom_aether", "teleport_range": 600, "teleport_delay": 2.0 },
        "faction_affinity": ["Rift_Daemons", "Ascended_Order", "Zealot_Legions"],
        "dna": { "atom_aether": 30.0, "atom_frequency": 30.0, "atom_energy": 25.0, "atom_volatility": 15.0 }
    },
    "Ability_Aether_Lance": {
        "name": "Aether Lance",
        "description": "A focused beam of pure psychic energy.",
        "manacost": 100, "cooldown": 60, "range": 400,
        "payload": { "target": "Single", "effect": "damage", "scaling": "atom_focus", "damage_type": "exotic", "damage_base": 80 },
        "faction_affinity": ["Ascended_Order", "Ancient_Guardians"],
        "dna": { "atom_aether": 40.0, "atom_focus": 30.0, "atom_energy": 20.0, "atom_volatility": 10.0 }
    },
    "Ability_Corruption_Wave": {
        "name": "Corruption Wave",
        "description": "Wave of chaotic energy that reduces enemy cohesion.",
        "manacost": 140, "cooldown": 100, "range": 300,
        "payload": { "target": "AOE", "radius": 150, "effect": "debuff", "scaling": "atom_volatility", "stat": "cohesion", "buff_magnitude": -0.3, "duration": 45 },
        "faction_affinity": ["Rift_Daemons"],
        "dna": { "atom_aether": 35.0, "atom_volatility": 35.0, "atom_will": 20.0, "atom_mass": 10.0 }
    },
    "Ability_Prescience": {
        "name": "Prescience",
        "description": "Grant allies the ability to foresee attacks, increasing accuracy.",
        "manacost": 90, "cooldown": 80, "range": 0,
        "payload": { "target": "Friendly_AOE", "radius": 200, "effect": "buff", "scaling": "atom_information", "stat": "accuracy", "buff_magnitude": 0.25, "buff_duration": 60 },
        "faction_affinity": ["Ancient_Guardians", "Ascended_Order"],
        "dna": { "atom_information": 30.0, "atom_focus": 30.0, "atom_aether": 30.0, "atom_will": 10.0 }
    },
    "Ability_Warp_Rift": {
        "name": "Warp Rift",
        "description": "Creates a persistent hazard zone that damages units inside.",
        "manacost": 180, "cooldown": 150, "range": 400,
        "payload": { "target": "Point", "effect": "hazard_zone", "scaling": "atom_volatility", "damage_per_tick": 20, "duration": 60, "radius": 80 },
        "faction_affinity": ["Rift_Daemons"],
        "dna": { "atom_aether": 45.0, "atom_volatility": 45.0, "atom_energy": 10.0 }
    },
    "Ability_Psychic_Barrier": {
        "name": "Psychic Barrier",
        "description": "Project a shield of will to protect allies.",
        "manacost": 110, "cooldown": 90, "range": 0,
        "payload": { "target": "Friendly_AOE", "radius": 150, "effect": "shield_boost", "scaling": "atom_will", "buff_magnitude": 0.4, "buff_duration": 45 },
        "faction_affinity": ["Ascended_Order", "Zealot_Legions"],
        "dna": { "atom_aether": 30.0, "atom_will": 30.0, "atom_cohesion": 25.0, "atom_stability": 15.0 }
    },
    "Ability_Soul_Drain": {
        "name": "Soul Drain",
        "description": "Drain life from target enemy to heal self.",
        "manacost": 130, "cooldown": 70, "range": 200,
        "payload": { "target": "Single", "effect": "drain_life", "scaling": "atom_aether", "drain_amount": 50, "damage_type": "magical" },
        "faction_affinity": ["Rift_Daemons", "Ascended_Order"],
        "dna": { "atom_aether": 35.0, "atom_will": 25.0, "atom_volatility": 20.0, "atom_energy": 20.0 }
    },

    # --- Control Effects (Tech/Mass) ---
    "Ability_Tractor_Beam": {
        "name": "Tractor Beam",
        "description": "Immobilize a target ship using gravity fields.",
        "manacost": 60, "cooldown": 45, "range": 400,
        "payload": { "target": "Single", "effect": "root", "scaling": "atom_mass", "duration": 15 },
        "faction_affinity": ["Solar_Hegemony", "Iron_Vanguard"],
        "dna": { "atom_mass": 40.0, "atom_energy": 30.0, "atom_stability": 20.0, "atom_focus": 10.0 }
    },
    "Ability_Magnetic_Clamp": {
        "name": "Magnetic Clamp",
        "description": "Lock nearby units in place using strong magnetic fields.",
        "manacost": 90, "cooldown": 60, "range": 200,
        "payload": { "target": "AOE", "radius": 150, "effect": "root", "scaling": "atom_mass", "duration": 12 },
        "faction_affinity": ["Iron_Vanguard", "Scavenger_Clans"],
        "dna": { "atom_mass": 40.0, "atom_cohesion": 30.0, "atom_stability": 20.0, "atom_energy": 10.0 }
    },
    "Ability_Stasis_Field": {
        "name": "Stasis Field",
        "description": "Freezes units in a time-dilated field.",
        "manacost": 150, "cooldown": 120, "range": 300,
        "payload": { "target": "AOE", "radius": 100, "effect": "stun", "scaling": "atom_stability", "duration": 20 },
        "faction_affinity": ["Ancient_Guardians", "Cyber_Synod"],
        "dna": { "atom_information": 35.0, "atom_stability": 30.0, "atom_focus": 25.0, "atom_energy": 10.0 }
    },
    "Ability_Gravity_Well": {
        "name": "Gravity Well",
        "description": "Generates intense gravity preventing FTL escape.",
        "manacost": 200, "cooldown": 240, "range": 0,
        "payload": { "target": "System_Wide", "effect": "inhibit_ftl", "scaling": "atom_mass", "duration": 120 },
        "faction_affinity": ["Iron_Vanguard", "Solar_Hegemony"],
        "dna": { "atom_mass": 45.0, "atom_energy": 25.0, "atom_stability": 20.0, "atom_cohesion": 10.0 }
    },
    "Ability_EMP_Burst": {
        "name": "EMP Burst",
        "description": "Disable electronic systems and shields.",
        "manacost": 100, "cooldown": 60, "range": 0,
        "payload": { "target": "AOE", "radius": 200, "effect": "shield_damage", "scaling": "atom_frequency", "secondary_effect": "silence", "silence_duration": 10, "shield_damage_base": 100 },
        "faction_affinity": ["Cyber_Synod", "Solar_Hegemony"],
        "dna": { "atom_frequency": 40.0, "atom_information": 30.0, "atom_volatility": 20.0, "atom_energy": 10.0 }
    },
    "Ability_Neural_Disruptor": {
        "name": "Neural Disruptor",
        "description": "Scramble enemy targeting sensors.",
        "manacost": 80, "cooldown": 50, "range": 300,
        "payload": { "target": "Single", "effect": "debuff", "scaling": "atom_information", "stat": "accuracy", "buff_magnitude": -0.4, "duration": 25 },
        "faction_affinity": ["Cyber_Synod", "Hive_Swarm"],
        "dna": { "atom_information": 40.0, "atom_aether": 25.0, "atom_will": 20.0, "atom_focus": 15.0 }
    },
    "Ability_Time_Dilation": {
        "name": "Time Dilation",
        "description": "Slow enemy movement in an area.",
        "manacost": 120, "cooldown": 90, "range": 400,
        "payload": { "target": "AOE", "radius": 150, "effect": "slow", "scaling": "atom_frequency", "slow_amount": 0.5, "duration": 30 },
        "faction_affinity": ["Ancient_Guardians", "Ascended_Order"],
        "dna": { "atom_frequency": 35.0, "atom_information": 30.0, "atom_focus": 25.0, "atom_stability": 10.0 }
    },
    "Ability_Logic_Override": {
        "name": "Logic Override",
        "description": "Hack enemy machine systems causing confusion.",
        "manacost": 140, "cooldown": 100, "range": 500,
        "payload": { "target": "Single", "effect": "confusion", "scaling": "atom_information", "duration": 20 },
        "faction_affinity": ["Cyber_Synod"],
        "dna": { "atom_information": 50.0, "atom_stability": 30.0, "atom_focus": 20.0 }
    },

    # --- Damage Abilities (Energy/Volatile) ---
    "Ability_Plasma_Burst": {
        "name": "Plasma Burst",
        "description": "High energy discharge.",
        "manacost": 50, "cooldown": 15, "range": 250,
        "payload": { "target": "Single", "effect": "damage", "scaling": "atom_energy", "type": "energy", "damage_base": 60 },
        "faction_affinity": ["Solar_Hegemony", "Void_Corsairs"],
        "dna": { "atom_energy": 40.0, "atom_volatility": 30.0, "atom_mass": 20.0, "atom_focus": 10.0 }
    },
    "Ability_Kinetic_Strike": {
        "name": "Kinetic Strike",
        "description": "Heavy kinetic impact to crush hulls.",
        "manacost": 40, "cooldown": 10, "range": 100,
        "payload": { "target": "Single", "effect": "damage", "scaling": "atom_mass", "type": "kinetic", "damage_base": 70 },
        "faction_affinity": ["Iron_Vanguard", "Scavenger_Clans"],
        "dna": { "atom_mass": 45.0, "atom_energy": 25.0, "atom_cohesion": 20.0, "atom_volatility": 10.0 }
    },
    "Ability_Antimatter_Torpedo": {
        "name": "Antimatter Torpedo",
        "description": "Exotic matter warhead that annihilates target.",
        "manacost": 250, "cooldown": 300, "range": 800,
        "payload": { "target": "Single", "effect": "damage", "scaling": "atom_energy", "type": "exotic", "damage_base": 500, "splash_radius": 50 },
        "faction_affinity": ["Solar_Hegemony", "Cyber_Synod"],
        "dna": { "atom_energy": 35.0, "atom_volatility": 35.0, "atom_aether": 20.0, "atom_mass": 10.0 }
    },
    "Ability_Orbital_Bombardment": {
        "name": "Orbital Bombardment",
        "description": "Massive kinetic strike from orbit.",
        "manacost": 200, "cooldown": 180, "range": 1000,
        "payload": { "target": "AOE", "radius": 200, "effect": "damage", "scaling": "atom_mass", "type": "kinetic", "damage_base": 200 },
        "faction_affinity": ["Iron_Vanguard", "Solar_Hegemony"],
        "dna": { "atom_mass": 40.0, "atom_energy": 30.0, "atom_volatility": 20.0, "atom_information": 10.0 }
    },
    "Ability_Melta_Beam": {
        "name": "Melta Beam",
        "description": "Armor-melting heat beam.",
        "manacost": 70, "cooldown": 30, "range": 150,
        "payload": { "target": "Single", "effect": "damage", "scaling": "atom_energy", "armor_piercing": 0.8, "damage_base": 90 },
        "faction_affinity": ["Solar_Hegemony", "Zealot_Legions"],
        "dna": { "atom_energy": 45.0, "atom_volatility": 30.0, "atom_focus": 15.0, "atom_mass": 10.0 }
    },
    "Ability_Frag_Barrage": {
        "name": "Frag Barrage",
        "description": "Explosive rounds effective against infantry.",
        "manacost": 60, "cooldown": 20, "range": 300,
        "payload": { "target": "AOE", "radius": 80, "effect": "damage", "scaling": "atom_volatility", "bonus_vs": "infantry", "damage_base": 40 },
        "faction_affinity": ["Iron_Vanguard", "Scavenger_Clans", "Hive_Swarm"],
        "dna": { "atom_volatility": 40.0, "atom_mass": 30.0, "atom_energy": 20.0, "atom_frequency": 10.0 }
    },
    "Ability_Ion_Cannon": {
        "name": "Ion Cannon",
        "description": "Massive energy blast that strips shields.",
        "manacost": 150, "cooldown": 90, "range": 600,
        "payload": { "target": "Single", "effect": "shield_damage", "scaling": "atom_frequency", "shield_damage_mult": 3.0, "damage_base": 100 },
        "faction_affinity": ["Solar_Hegemony", "Ancient_Guardians"],
        "dna": { "atom_frequency": 40.0, "atom_energy": 35.0, "atom_stability": 15.0, "atom_focus": 10.0 }
    },
    "Ability_Vortex_Grenade": {
        "name": "Vortex Grenade",
        "description": "Creates a temporary tear in reality.",
        "manacost": 100, "cooldown": 60, "range": 100,
        "payload": { "target": "AOE", "radius": 50, "effect": "damage", "scaling": "atom_volatility", "type": "exotic", "damage_base": 120 },
        "faction_affinity": ["Zealot_Legions", "Rift_Daemons"],
        "dna": { "atom_aether": 35.0, "atom_volatility": 35.0, "atom_energy": 20.0, "atom_mass": 10.0 }
    },

    # --- Support Abilities (Cohesion/Will) ---
    "Ability_Shield_Harmonics": {
        "name": "Shield Harmonics",
        "description": "Regenerate shields of nearby allies.",
        "manacost": 80, "cooldown": 50, "range": 0,
        "payload": { "target": "Friendly_AOE", "radius": 200, "effect": "shield_regen", "scaling": "atom_cohesion", "regen_amount": 50, "duration": 10 },
        "faction_affinity": ["Ancient_Guardians", "Solar_Hegemony"],
        "dna": { "atom_cohesion": 35.0, "atom_stability": 30.0, "atom_energy": 25.0, "atom_focus": 10.0 }
    },
    "Ability_Nanite_Repair": {
        "name": "Nanite Repair",
        "description": "Repair hull damage over time.",
        "manacost": 80, "cooldown": 60, "range": 200,
        "payload": { "target": "Single", "effect": "heal_over_time", "scaling": "atom_cohesion", "heal_total": 200, "duration": 20 },
        "faction_affinity": ["Hive_Swarm", "Cyber_Synod", "Iron_Vanguard"],
        "dna": { "atom_cohesion": 40.0, "atom_stability": 25.0, "atom_information": 20.0, "atom_mass": 15.0 }
    },
    "Ability_Emergency_Repairs": {
        "name": "Emergency Repairs",
        "description": "Instant burst of hull repair.",
        "manacost": 100, "cooldown": 90, "range": 0,
        "payload": { "target": "Self", "effect": "heal_instant", "scaling": "atom_cohesion", "heal_amount": 300 },
        "faction_affinity": ["Iron_Vanguard", "Scavenger_Clans"],
        "dna": { "atom_cohesion": 45.0, "atom_stability": 30.0, "atom_energy": 15.0, "atom_mass": 10.0 }
    },
    "Ability_Tactical_Doctrine": {
        "name": "Tactical Doctrine",
        "description": "Coordinate attacks to improve accuracy.",
        "manacost": 70, "cooldown": 60, "range": 0,
        "payload": { "target": "Friendly_AOE", "radius": 250, "effect": "buff", "scaling": "atom_information", "stat": "accuracy", "buff_magnitude": 0.2, "buff_duration": 45 },
        "faction_affinity": ["Solar_Hegemony", "Cyber_Synod"],
        "dna": { "atom_information": 35.0, "atom_will": 30.0, "atom_focus": 25.0, "atom_stability": 10.0 }
    },
    "Ability_Morale_Boost": {
        "name": "Morale Boost",
        "description": "Restore morale to nearby units.",
        "manacost": 60, "cooldown": 45, "range": 0,
        "payload": { "target": "Friendly_AOE", "radius": 200, "effect": "restore_morale", "scaling": "atom_will", "restore_amount": 40 },
        "faction_affinity": ["Zealot_Legions", "Solar_Hegemony"],
        "dna": { "atom_will": 40.0, "atom_information": 25.0, "atom_cohesion": 20.0, "atom_stability": 15.0 }
    },
    "Ability_Overcharge_Weapons": {
        "name": "Overcharge Weapons",
        "description": "Increase damage output at risk of self-damage.",
        "manacost": 50, "cooldown": 40, "range": 0,
        "payload": { "target": "Self", "effect": "buff", "stat": "damage", "scaling": "atom_energy", "buff_magnitude": 0.3, "buff_duration": 15, "self_damage": 10 },
        "faction_affinity": ["Solar_Hegemony", "Scavenger_Clans", "Cyber_Synod"],
        "dna": { "atom_energy": 35.0, "atom_volatility": 30.0, "atom_focus": 20.0, "atom_stability": 15.0 }
    },
    "Ability_Fortify_Position": {
        "name": "Fortify Position",
        "description": "Increase armor and resistance.",
        "manacost": 70, "cooldown": 60, "range": 0,
        "payload": { "target": "Self", "effect": "buff", "stat": "armor", "scaling": "atom_cohesion", "buff_magnitude": 0.5, "buff_duration": 30 },
        "faction_affinity": ["Iron_Vanguard", "Zealot_Legions"],
        "dna": { "atom_cohesion": 40.0, "atom_mass": 30.0, "atom_stability": 20.0, "atom_will": 10.0 }
    },
    "Ability_Inspiration_Aura": {
        "name": "Inspiration Aura",
        "description": "Passive aura that improves friendly unit performance.",
        "manacost": 0, "cooldown": 0, "range": 0,
        "payload": { "target": "Passive_Aura", "radius": 250, "effect": "buff_all_stats", "scaling": "atom_will", "buff_magnitude": 0.1 },
        "faction_affinity": ["Zealot_Legions", "Ancient_Guardians"],
        "dna": { "atom_will": 45.0, "atom_aether": 25.0, "atom_information": 20.0, "atom_cohesion": 10.0 }
    },

    # --- Mobility Abilities (Frequency) ---
    "Ability_Phase_Jump": {
        "name": "Phase Jump",
        "description": "Short range tactical teleport.",
        "manacost": 40, "cooldown": 20, "range": 300,
        "payload": { "target": "Self", "effect": "teleport", "scaling": "atom_frequency", "teleport_range": 300 },
        "faction_affinity": ["Void_Corsairs", "Ancient_Guardians", "Cyber_Synod"],
        "dna": { "atom_frequency": 40.0, "atom_energy": 30.0, "atom_aether": 20.0, "atom_focus": 10.0 }
    },
    "Ability_Strategic_Warp": {
        "name": "Strategic Warp",
        "description": "Long range teleport for strategic redeployment.",
        "manacost": 150, "cooldown": 120, "range": 2000,
        "payload": { "target": "Self", "effect": "teleport", "scaling": "atom_frequency", "teleport_range": 2000, "cast_time": 5.0 },
        "faction_affinity": ["Void_Corsairs", "Rift_Daemons"],
        "dna": { "atom_frequency": 30.0, "atom_energy": 30.0, "atom_information": 25.0, "atom_aether": 15.0 }
    },
    "Ability_Evasive_Maneuvers": {
        "name": "Evasive Maneuvers",
        "description": "Increases evasion chance significantly.",
        "manacost": 50, "cooldown": 40, "range": 0,
        "payload": { "target": "Self", "effect": "buff", "stat": "evasion", "scaling": "atom_frequency", "buff_magnitude": 0.4, "buff_duration": 15 },
        "faction_affinity": ["Void_Corsairs", "Ancient_Guardians"],
        "dna": { "atom_frequency": 40.0, "atom_focus": 30.0, "atom_stability": 20.0, "atom_information": 10.0 }
    },
    "Ability_Afterburner": {
        "name": "Afterburner",
        "description": "Temporary massive speed boost.",
        "manacost": 30, "cooldown": 30, "range": 0,
        "payload": { "target": "Self", "effect": "speed_boost", "scaling": "atom_frequency", "movement_bonus": 2.0, "duration": 10 },
        "faction_affinity": ["Void_Corsairs", "Scavenger_Clans", "Hive_Swarm"],
        "dna": { "atom_frequency": 35.0, "atom_energy": 35.0, "atom_volatility": 20.0, "atom_mass": 10.0 }
    },
    "Ability_Webway_Strike": {
        "name": "Webway Strike",
        "description": "Enter or exit the Webway for rapid redeployment.",
        "manacost": 80, "cooldown": 60, "range": 800,
        "payload": { "target": "Self", "effect": "teleport", "scaling": "atom_frequency", "teleport_range": 800 },
        "faction_affinity": ["Ancient_Guardians"],
        "dna": { "atom_frequency": 30.0, "atom_aether": 30.0, "atom_focus": 25.0, "atom_information": 15.0 }
    },
    "Ability_Hit_and_Run": {
        "name": "Hit and Run",
        "description": "Attack and immediately move.",
        "manacost": 40, "cooldown": 25, "range": 0,
        "payload": { "target": "Self", "effect": "maneuver", "scaling": "atom_frequency", "movement_bonus": 1.5, "duration": 5 },
        "faction_affinity": ["Void_Corsairs"],
        "dna": { "atom_frequency": 35.0, "atom_volatility": 30.0, "atom_energy": 20.0, "atom_focus": 15.0 }
    }
}

def generate_abilities():
    print(f"Generating {len(ABILITY_DEFINITIONS)} Atomic Abilities...")
    
    registry = {}
    
    for ability_id, data in ABILITY_DEFINITIONS.items():
        # Validate DNA sum
        dna_sum = sum(data["dna"].values())
        if abs(dna_sum - 100.0) > 0.1:
            print(f"[WARN] Ability {ability_id} DNA mismatch: {dna_sum}")
            
        # Complete DNA dict
        full_dna = {
            "atom_mass": 0.0, "atom_energy": 0.0, "atom_cohesion": 0.0,
            "atom_volatility": 0.0, "atom_stability": 0.0, "atom_focus": 0.0,
            "atom_frequency": 0.0, "atom_aether": 0.0, "atom_will": 0.0,
            "atom_information": 0.0
        }
        full_dna.update(data["dna"])
        
        # Build registry entry
        entry = {
            "id": ability_id,
            "name": data["name"],
            "description": data["description"],
            "elemental_dna": full_dna,
            "manacost": data["manacost"],
            "cooldown": data["cooldown"],
            "range": data["range"],
            "payload": data["payload"],
            "faction_affinity": data["faction_affinity"],
            "source": "atomic_design_v2"
        }
        registry[ability_id] = entry
        
    out_path = os.path.join(FACTIONS_DIR, "ability_registry.json")
    with open(out_path, 'w') as f:
        json.dump(registry, f, indent=2)
    print(f"Saved {len(registry)} abilities to {out_path}")

if __name__ == "__main__":
    generate_abilities()
