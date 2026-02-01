import random
import json
from typing import Dict, List, Any
from src.data.weapon_data import WEAPON_DB

class ShipDesignFactory:
    """
    Procedurally designs ships by fitting hulls with components from a faction's arsenal.
    """
    
    def __init__(self, hull_blueprints: Dict, module_blueprints: Dict):
        self.hulls = hull_blueprints
        self.modules = module_blueprints
        self.rng = random.Random()
        
    def design_roster(self, faction_name: str, faction_traits: List[str], arsenal: Dict[str, Any]) -> List[Dict]:
        """Generates a full roster of ship designs for a faction."""
        roster = []
        
        # Hydrate Arsenal if provided as List of IDs
        if isinstance(arsenal, list):
            new_arsenal = {}
            for w_id in arsenal:
                if isinstance(w_id, str):
                    db_entry = WEAPON_DB.get(w_id.lower())
                    if db_entry:
                        w_data = db_entry.copy()
                        w_data["id"] = w_id
                        w_data["category"] = "General"
                        
                        power = db_entry.get("S", 4) * db_entry.get("D", 1) * 2
                        w_rng = db_entry.get("Range", 24)
                        
                        w_data["stats"] = {
                            "power": power,
                            "range": w_rng,
                            "recharge": 10
                        }
                        
                        new_arsenal[w_id] = w_data
            arsenal = new_arsenal

        # DNA system removed. Using traits or default "Balanced" doctrine.
        doctrine = self._determine_doctrine(faction_traits)
        
        for hull_id, hull_data in self.hulls.items():
            # 1. Standard Issue
            roster.append(self._design_ship(faction_name, hull_id, hull_data, arsenal, doctrine, "Standard"))
            
            # 2. Specialized Variant
            specialty = self._get_specialty_role(faction_traits)
            roster.append(self._design_ship(faction_name, hull_id, hull_data, arsenal, doctrine, specialty))
            
            # 3. Elite Variant (for Capital ships)
            if hull_data.get("base_cost", 0) > 5000:
                roster.append(self._design_ship(faction_name, hull_id, hull_data, arsenal, doctrine, "Elite"))

        # [PHASE 102] Universal Interdictor Access
        if "interdictor" in self.hulls:
             roster.append(self._design_ship(faction_name, "interdictor", self.hulls["interdictor"], arsenal, doctrine, "Interdictor"))
                
        return roster
        
    def _design_ship(self, faction: str, hull_id: str, hull: Dict, arsenal: Dict, doctrine: str, role: str) -> Dict:
        """Fits a specific ship hull."""
        
        design = {
            "name": f"{faction} {role} {hull['name']}",
            "blueprint_id": f"{faction.lower()}_{hull_id}_{role.lower()}",
            "type": hull_id, 
            "faction": faction,
            "cost": hull["base_cost"],
            "base_stats": {
                "hp": hull["base_hp"],
                "armor": 0,
                "shield": 0,
                "damage": 0,
                "speed": hull["base_speed"],
                "range": 0,
                "sensors": 0
            },
            "components": [],
            "traits": [role],
            "abilities": {}
        }
        
        if role == "Interdictor" or hull_id == "interdictor":
             design["traits"].append("Interdictor")
             design["abilities"]["Gravity_Well"] = True

        hardpoints = hull.get("hardpoints", {})

        # Fit Weapons
        for hp_type, count in hardpoints.items():
            if "weapon" in hp_type:
                primary_count = int(count * 0.6)
                if primary_count == 0 and count > 0: primary_count = 1
                secondary_count = count - primary_count
                
                w_primary = self._select_best_weapon(hp_type, arsenal, doctrine, role, "Primary")
                w_secondary = self._select_best_weapon(hp_type, arsenal, doctrine, role, "Secondary", exclude_ids=[w_primary["id"]] if w_primary else None)
                
                if not w_secondary: w_secondary = w_primary
                
                for i in range(count):
                    w = w_primary if i < primary_count else w_secondary
                    if w:
                        design["components"].append({"slot": hp_type, "component": w["id"]})
                        design["base_stats"]["damage"] += w["stats"].get("power", 10)
                        w_range = w["stats"].get("range", 0)
                        if w_range > design["base_stats"]["range"]:
                            design["base_stats"]["range"] = w_range
                        
        # Fit Modules
        def_slots = hardpoints.get("module_defense", 0)
        for _ in range(def_slots):
            mod_type = self._select_defense_module(doctrine, role)
            mod = self.modules.get(mod_type)
            if mod:
                design["components"].append({"slot": "module_defense", "component": mod["name"]}) 
                design["base_stats"]["hp"] += mod["stats"].get("hp_bonus", 0)
                design["base_stats"]["shield"] += mod["stats"].get("shield_bonus", 0)
                design["base_stats"]["armor"] += mod["stats"].get("armor_bonus", 0)
                
        util_slots = hardpoints.get("module_utility", 0)
        
        # [PHASE 24] Interdiction Logic (Modular Approach)
        # 1. Specialized Interdictor Hulls/Roles always get it
        is_interdictor = (role == "Interdictor" or hull_id == "interdictor")
        
        # 2. Large Ships (Cruiser+) have a chance to fit it if Doctrine is INTERDICTION
        # User Request: "Module like a weapon or shield generator" on larger ships
        is_large_ship = hull.get("base_cost", 0) >= 1500 # Approx Cruiser cost
        should_fit_module = is_interdictor
        
        if not should_fit_module and is_large_ship and doctrine == "INTERDICTION":
             # 20% Chance for random large ships to verify user request "one or two in each fleet"
             if self.rng.random() < 0.20:
                  should_fit_module = True

        if should_fit_module:
             mod = self.modules.get("base_interdictor")
             if mod:
                  design["components"].append({"slot": "module_utility", "component": mod["name"]})
                  design["abilities"]["Gravity_Well"] = True # Grant Ability
                  design["traits"].append("Interdictor") # Tag for AI logic
                  util_slots = max(0, util_slots - 1)
                  
        for _ in range(util_slots):
            mod_type = "base_engine" if self.rng.random() > 0.5 else "base_sensor"
            mod = self.modules.get(mod_type)
            if mod:
                 design["components"].append({"slot": "module_utility", "component": mod["name"]})
                 design["base_stats"]["speed"] += mod["stats"].get("speed_bonus", 0)
                 design["base_stats"]["sensors"] += mod["stats"].get("detection", 0)
                 
        if role == "Elite":
            design["base_stats"]["hp"] = int(design["base_stats"]["hp"] * 1.2)
            design["base_stats"]["damage"] = int(design["base_stats"]["damage"] * 1.2)
            design["cost"] = int(design["cost"] * 1.5)
            
        return design

    def _select_best_weapon(self, slot_type: str, arsenal: Dict, doctrine: str, role: str, purpose: str = "Primary", exclude_ids: List[str] = None) -> Dict:
        """Picks the best weapon."""
        valid_weapons = []
        for w in arsenal.values():
            if exclude_ids and w["id"] in exclude_ids: continue
            
            w_stats = w.get("stats", {})
            w_power = w_stats.get("power", 0)
            
            # [PHASE 5] AI Preference for Exotic Weapons
            # Boost power rating for selection purposes to favor new arsenal
            if w.get("category") == "Exotic":
                w_power *= 1.25
            
            if "heavy" in slot_type and w_power > 30: valid_weapons.append(w)
            elif "light" in slot_type and w_power <= 30: valid_weapons.append(w)
            elif "medium" in slot_type: valid_weapons.append(w)
            
        if not valid_weapons: 
            if exclude_ids:
                 return self._select_best_weapon(slot_type, arsenal, doctrine, role, purpose, exclude_ids=None)
            valid_weapons = list(arsenal.values())
            
        if not valid_weapons: return None
            
        # Optimization Logic
        if purpose == "Primary":
            return max(valid_weapons, key=lambda x: x["stats"].get("power", 0))
        else:
            return min(valid_weapons, key=lambda x: x["stats"].get("recharge", 999))

    def _determine_doctrine(self, traits: List[str]) -> str:
        """Determines fitting strategy based on traits."""
        if not traits: return "Balanced"
        traits_str = " ".join(traits).lower()
        if any(t in traits_str for t in ["strong", "aggressive", "militarist"]): return "Aggressive"
        if any(t in traits_str for t in ["defensive", "fortified", "resilient"]): return "Defensive"
        if any(t in traits_str for t in ["fast", "agile"]): return "Speed"
        return "Balanced"
        
    def _get_specialty_role(self, traits: List[str]) -> str:
        """Determines specialty role."""
        if not traits: return "Tactical"
        traits_str = " ".join(traits).lower()
        if "heavy" in traits_str or "strong" in traits_str: return "Siege"
        if "aggressive" in traits_str: return "Assault"
        if "fast" in traits_str: return "Strike"
        return "Tactical"
        
    def _select_defense_module(self, doctrine: str, role: str) -> str:
        """Selects Armor vs Shield."""
        if doctrine == "Defensive" or role == "Armored":
            return "base_armor"
        elif doctrine == "Speed":
            return "base_shield"
        else:
            return self.rng.choice(["base_armor", "base_shield"])
