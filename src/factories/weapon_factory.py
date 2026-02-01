import random
import json
from typing import Dict, List, Any, Optional

class ProceduralWeaponFactory:
    """
    Generates unique, faction-specific weapon variants based on:
    1. Base Templates (Laser, Projectile, etc.)
    2. Faction Traits (Static stats)
    3. Exotic Tags (Acidic, Gravimetric, etc.)
    """
    
    def __init__(self, base_blueprints: Dict[str, Any]):
        self.blueprints = base_blueprints
        self.rng = random.Random()
        self.invented_paradigms = {}
        self.exotic_tags = [
            "acidic", "disruptor", "logic_virus", "black_hole", "incendiary", "cryo", "phasic",
            "melta", "tesla", "gauss", "radiation", "nanite", "ion", "polaron" 
        ]

    def inject_paradigm(self, paradigm_id: str, data: Dict[str, Any]):
        """Injects a new 'invented' base weapon paradigm at runtime."""
        self.invented_paradigms[paradigm_id] = data
        print(f"[WeaponFactory] New weapon paradigm invented: {paradigm_id}")

    def generate_arsenal(self, faction_name: str, faction_data: Dict[str, Any], count: int = 5, custom_prefixes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generates a list of unique weapons for a faction."""
        arsenal = {}
        preferences = self._get_default_preferences()
        
        # Mix in invented paradigms
        for p_id in self.invented_paradigms:
            preferences[p_id] = 1.0

        for i in range(count):
            base_type = self.rng.choices(
                population=list(preferences.keys()), 
                weights=list(preferences.values()),
                k=1
            )[0]
            
            template = self.invented_paradigms.get(base_type) or self.blueprints.get(base_type)
            if not template: continue
                
            weapon_id = f"{faction_name}_{base_type}_{i}"
            
            # [PHASE 5] Variant Promotion
            # If the chosen base_type has specific variants in the blueprints (e.g. "base_bolter_heavy_rapid_fire"),
            # we should occasionally swap the base template for a specific variant to ensure they appear!
            # Search for variants of this type
            variants = [k for k in self.blueprints.keys() if k.startswith(base_type) and k != base_type]
            if variants and self.rng.random() < 0.7: # 70% chance to pick a specific variant if available
                 variant_id = self.rng.choice(variants)
                 template = self.blueprints.get(variant_id)
                 # We still name the output ID based on the loop, but the CONTENT is the variant
            
            if not template: continue

            weapon_data = self._mutate_weapon(faction_name, template, custom_prefixes)
            weapon_data["id"] = weapon_id
            
            arsenal[weapon_id] = weapon_data
            
        return arsenal
        
    def _get_default_preferences(self) -> Dict[str, float]:
        """Default weapon probability."""
        prefs = {}
        
        # Dynamic Discovery of Blueprint Families
        # We group by the 'base_type' logic (e.g. all 'bolter' weapons share probability)
        # But for now, let's just assign flat probability to high-level categories
        
        # Standard
        prefs["base_projectile_weapon"] = 1.0
        prefs["base_laser_weapon"] = 1.0
        prefs["base_plasma_weapon"] = 1.0
        
        # New High-Flavor Sets (We want these to appear often)
        prefs["base_bolter_weapon"] = 1.0
        prefs["base_melta_weapon"] = 0.8
        prefs["base_tesla_weapon"] = 0.8
        prefs["base_gauss_weapon"] = 0.6
        prefs["base_rad_weapon"] = 0.5
        prefs["base_phaser_weapon"] = 0.8
        prefs["base_disruptor_weapon"] = 0.6
        prefs["base_polaron_weapon"] = 0.5
        prefs["base_antiproton_weapon"] = 0.4
        prefs["base_quantum_torpedo"] = 0.4
        prefs["base_turbolaser_weapon"] = 0.6
        prefs["base_ion_cannon"] = 0.6
        prefs["base_concussion_missile"] = 0.7
        prefs["base_railgun_weapon"] = 0.6
        prefs["base_nanite_weapon"] = 0.3
        prefs["base_sonic_weapon"] = 0.5
        prefs["base_tachyon_weapon"] = 0.4
        prefs["base_volkite_weapon"] = 0.5
        prefs["base_grav_weapon"] = 0.5

        return prefs

    def _mutate_weapon(self, faction_name: str, template: Dict, custom_prefixes: Optional[List[str]] = None) -> Dict:
        """Creates a unique variant with mutated stats and name."""
        variant = json.loads(json.dumps(template)) # Deep copy
        
        # 1. Mutate Stats (Simple +/- 10% variance)
        stats = variant.get("stats", {})
        for k, v in stats.items():
            if isinstance(v, (int, float)):
                stats[k] = round(v * self.rng.uniform(0.9, 1.1), 2)
        
        # 2. Chance to add exotic tags
        if self.rng.random() < 0.2: # 20% chance for exotic infusion
            new_tag = self.rng.choice(self.exotic_tags)
            if "tags" not in variant: variant["tags"] = []
            if new_tag not in variant["tags"]:
                variant["tags"].append(new_tag)
                
        # 3. Generate Flavor Name
        flavor_name = self._generate_name(faction_name, variant)
        variant["name"] = flavor_name
        
        variant["source_file"] = "procedural"
        return variant
        
    def _generate_name(self, faction: str, weapon_data: Dict) -> str:
        """Generates a lore-friendly name including exotic descriptors."""
        base_name = weapon_data["name"]
        tags = weapon_data.get("tags", [])
        
        adjectives = ["Advanced", "Standard", "MKII", "Prototype", "Enhanced", "Tactical", "Heavy", "Light", "Precision"]
        exotic_adjectives = {
            "acidic": "Corrosive",
            "disruptor": "Disruption",
            "logic_virus": "Infected",
            "black_hole": "Singularity",
            "incendiary": "Inferno",
            "cryo": "Glacial",
            "phasic": "Phase",
            "melta": "Fusion",
            "tesla": "Voltaic",
            "gauss": "Flayer",
            "radiation": "Rad",
            "nanite": "Gray-Goo",
            "ion": "Disabling",
            "polaron": "Polaron",
            "antimatter": "Null",
            "quantum": "Quantum",
            "plasma": "Sun-Fury",
            "kinetic": "Macro"
        }
        
        # Pick 1 standard adj
        adj = self.rng.choice(adjectives)
        
        # Check for exotic adj
        exotic_adj = ""
        for tag in tags:
            if tag in exotic_adjectives:
                exotic_adj = exotic_adjectives[tag]
                break
        
        short_base = base_name.replace("Standard ", "").replace(" Weapon", "").replace("Launcher", "").strip()
        
        if exotic_adj:
            return f"{faction} {adj} {exotic_adj} {short_base}"
        else:
            return f"{faction} {adj} {short_base}"
