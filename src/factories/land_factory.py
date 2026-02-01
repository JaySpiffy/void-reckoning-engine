
import random
import copy
from typing import Dict, List, Any

class LandDesignFactory:
    """
    Procedurally designs land units (Infantry, Vehicles, Walkers).
    Handles weapon downscaling and squad composition.
    """
    
    def __init__(self, chassis_blueprints: Dict, module_blueprints: Dict):
        self.chassis = chassis_blueprints
        self.modules = module_blueprints
        self.rng = random.Random()
        
    def design_roster(self, faction_name: str, faction_traits: List[str], arsenal: Dict[str, Any]) -> List[Dict]:
        """Generates a land army roster."""
        roster = []
        
        # 1. Create Land Arsenal (Downscaled Ship Weapons)
        land_arsenal = self._create_land_arsenal(arsenal)
        
        # 2. Determine Doctrine
        doctrine = self._determine_doctrine(faction_traits)
        
        for ch_id, ch_data in self.chassis.items():
            category = ch_data.get("category", "Vehicle")
            
            # Design Variants based on Doctrine
            if category == "Infantry":
                # Standard Squad
                roster.append(self._design_infantry_squad(faction_name, ch_id, ch_data, land_arsenal, doctrine, "Standard"))
                # Specialist/Assault Squad
                roster.append(self._design_infantry_squad(faction_name, ch_id, ch_data, land_arsenal, doctrine, "Assault"))
            else:
                # Vehicles
                roster.append(self._design_vehicle(faction_name, ch_id, ch_data, land_arsenal, doctrine, "Standard"))
                if ch_data.get("base_cost", 0) > 800:
                    roster.append(self._design_vehicle(faction_name, ch_id, ch_data, land_arsenal, doctrine, "Elite"))
                    
        return roster

    def _create_land_arsenal(self, ship_arsenal: Dict) -> Dict:
        """Creates small-scale versions of ship weapons."""
        land_arsenal = {}
        for w_id, w_data in ship_arsenal.items():
            # Skip non-weapons or already processed
            if "Stolen" in w_data.get("name", ""): continue
            
            # Cloning
            base_name = w_data["name"]
            
            # Variant 1: Infantry Small Arm (1/100 scale)
            inf_w = copy.deepcopy(w_data)
            inf_w["id"] = f"land_small_{w_id}"
            inf_w["name"] = f"Portable {base_name}"
            # Scale Stats
            for stat, val in inf_w["stats"].items():
                if isinstance(val, (int, float)):
                    inf_w["stats"][stat] = val * 0.01
            land_arsenal[inf_w["id"]] = inf_w
            
            # Variant 2: Vehicle Weapon (1/10 scale)
            veh_w = copy.deepcopy(w_data)
            veh_w["id"] = f"land_vehicle_{w_id}"
            veh_w["name"] = f"Mounted {base_name}"
            for stat, val in veh_w["stats"].items():
                if isinstance(val, (int, float)):
                    veh_w["stats"][stat] = val * 0.10
            land_arsenal[veh_w["id"]] = veh_w
            
        return land_arsenal
        
    def _design_infantry_squad(self, faction: str, ch_id: str, chassis: Dict, arsenal: Dict, doctrine: str, role: str) -> Dict:
        """Composes an infantry squad with mixed roles."""
        design = {
            "blueprint_id": f"{faction.lower()}_{ch_id}_{role.lower()}_squad",
            "name": f"{faction} {role} {chassis['name']}",
            "type": ch_id,
            "faction": faction,
            "category": "Infantry",
            "base_stats": {
                "hp": chassis["base_hp"], # PER MODEL
                "organization": chassis["base_org"],
                "soft_attack": 0,
                "hard_attack": 0,
                "manpower": chassis["slots"]["squad_size"]
            },
            "components": [], # Abstract representation
            "composition": {} # Actual Soldier Breakdown
        }
        
        squad_size = chassis["slots"]["squad_size"]
        special_slots = chassis["slots"].get("specialist_slots", 1)
        
        # Select Weapons
        # Standard Rifle (Portable / Light)
        rifle = self._select_weapon(arsenal, "small", doctrine, "General")
        # Heavy Weapon (Portable / Heavy)
        heavy = self._select_weapon(arsenal, "small", doctrine, "Anti-Armor") 
        
        comp = {"Rifleman": 0, "Specialist": 0, "Medic": 0, "Leader": 1}
        
        # Composition Logic
        remaining = squad_size - 1 # Leader exists
        
        spec_count = min(remaining, special_slots)
        if role == "Assault": spec_count = min(remaining, special_slots + 2)
        
        comp["Specialist"] = spec_count
        remaining -= spec_count
        
        # Utilitarian
        if remaining > 0 and self.rng.random() > 0.5:
            comp["Medic"] = 1
            remaining -= 1
            
        comp["Rifleman"] = remaining
        design["composition"] = comp
        
        # Aggregating Stats
        # Leader = Rifle + Buff
        # Rifleman = Rifle
        # Specialist = Heavy Weapon
        
        rif_stats = rifle["stats"] if rifle else {"power": 1}
        hvy_stats = heavy["stats"] if heavy else {"power": 5}
        
        total_power = 0
        total_power += comp["Rifleman"] * rif_stats.get("power", 1)
        total_power += comp["Leader"] * (rif_stats.get("power", 1) * 1.2)
        total_power += comp["Specialist"] * hvy_stats.get("power", 5)
        
        design["base_stats"]["soft_attack"] = total_power
        # Heuristic: Hard attack is 20% of Soft Attack for energy weapons, or specific for missiles
        design["base_stats"]["hard_attack"] = total_power * 0.2 
        
        if comp["Medic"] > 0:
            design["base_stats"]["hp"] *= 1.2
            design["base_stats"]["organization"] *= 1.2
            
        design["cost"] = chassis["base_cost"] + (total_power * 2)
        
        # Save components for reference
        if rifle: design["components"].append({"slot": "standard_issue", "component": rifle["id"]})
        if heavy: design["components"].append({"slot": "special_issue", "component": heavy["id"]})
        
        return design

    def _design_vehicle(self, faction: str, ch_id: str, chassis: Dict, arsenal: Dict, doctrine: str, role: str) -> Dict:
        """Fits a vehicle chassis."""
        design = {
            "blueprint_id": f"{faction.lower()}_{ch_id}_{role.lower()}",
            "name": f"{faction} {role} {chassis['name']}",
            "type": ch_id,
            "faction": faction,
            "category": chassis.get("category", "Vehicle"),
            "base_stats": {
                "hp": chassis["base_hp"],
                "armor": chassis["base_armor"],
                "soft_attack": 0,
                "hard_attack": 0,
                "speed": 10
            },
            "components": []
        }
        
        hardpoints = chassis.get("hardpoints", {})
        
        for slot, slot_type in hardpoints.items():
            # Weapon Fitting
            w_cat = "General"
            if slot_type == "heavy": w_cat = "Anti-Titan"
            elif slot_type == "medium": w_cat = "Anti-Armor"
            
            weapon = self._select_weapon(arsenal, "vehicle", doctrine, w_cat)
            
            if weapon:
                design["components"].append({"slot": slot, "component": weapon["id"]})
                power = weapon["stats"].get("power", 10)
                
                # Distribution
                if w_cat == "Anti-Armor":
                    design["base_stats"]["hard_attack"] += power
                    design["base_stats"]["soft_attack"] += power * 0.3
                else:
                    design["base_stats"]["soft_attack"] += power
                    design["base_stats"]["hard_attack"] += power * 0.5
                    
        design["cost"] = chassis["base_cost"] + (design["base_stats"]["soft_attack"] + design["base_stats"]["hard_attack"])
        
        return design

    def _select_weapon(self, arsenal: Dict, scale: str, doctrine: str, category_pref: str) -> Dict:
        """Selects appropriate weapon from scaled arsenal."""
        candidates = [w for w in arsenal.values() if scale in w["id"]]
        if not candidates: return None
        
        # Filter by preference if strictly needed, otherwise random weighted
        # Simplified for now
        return self.rng.choice(candidates)

    def _determine_doctrine(self, traits: List[str]) -> str:
        """Determines fitting strategy based on traits."""
        if not traits: return "Balanced"
        traits_str = " ".join(traits).lower()
        if any(t in traits_str for t in ["strong", "aggressive", "militarist"]): return "Aggressive"
        if any(t in traits_str for t in ["defensive", "fortified", "resilient"]): return "Defensive"
        if any(t in traits_str for t in ["fast", "agile"]): return "Speed"
        return "Balanced"
