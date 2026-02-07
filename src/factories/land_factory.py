
import random
import json
import os
import copy
from typing import Dict, List, Any
from src.utils.game_logging import GameLogger, LogCategory

class LandDesignFactory:
    """
    Procedurally designs land units (Infantry, Vehicles, Walkers).
    Handles weapon downscaling and unified hardpoint fitting.
    """
    
    def __init__(self, chassis_blueprints: Dict, module_blueprints: Dict, equipment_blueprints: Dict = None):
        self.chassis = chassis_blueprints
        self.modules = module_blueprints
        self.equipment = equipment_blueprints or {}
        self.rng = random.Random()
        self.logger = GameLogger()
        self.output_dir = "logs" # Default fallback


        
    def design_roster(self, faction_name: str, faction_traits: List[str], arsenal: Dict[str, Any]) -> List[Dict]:
        """Generates a land army roster with unified design logic."""
        roster = []
        
        # 1. Create Multi-Scale Land Arsenal
        multi_scale_arsenal = self._create_multi_scale_arsenal(arsenal)
        
        # 2. Determine Doctrine & Style
        doctrine = self._determine_doctrine(faction_traits)
        style = self._determine_style(faction_name, faction_traits)
        
        for ch_id, ch_data in self.chassis.items():
            # Standard Variant
            roster.append(self._design_land_unit(faction_name, ch_id, ch_data, multi_scale_arsenal, doctrine, style, "Standard"))
            
            # Elite/Specialized Variant for larger units
            if ch_data.get("base_cost", 0) > 1000:
                roster.append(self._design_land_unit(faction_name, ch_id, ch_data, multi_scale_arsenal, doctrine, style, "Elite"))
            elif ch_data.get("category") == "Infantry":
                roster.append(self._design_land_unit(faction_name, ch_id, ch_data, multi_scale_arsenal, doctrine, style, "Assault"))
                    
        return roster

    def _create_multi_scale_arsenal(self, ship_arsenal: Dict) -> Dict:
        """
        Creates scaled versions of ship weapons for different land unit tiers.
        Scales: micro (0.005), light (0.01), medium (0.05), heavy (0.15), titan (0.45).
        Only scales weapons marked with 'ground_capable': true.
        """
        scales = {
            "micro": 0.05,
            "light": 0.12,
            "medium": 0.30,
            "heavy": 0.60,
            "titan": 1.50
        }
        
        land_arsenal = {s: {} for s in scales}
        
        for w_id, w_data in ship_arsenal.items():
            # [NEW] Check for ground capability
            if not w_data.get("ground_capable", True):
                continue

            if "Stolen" in w_data.get("name", ""): continue
            
            base_name = w_data["name"]
            
            for scale_name, factor in scales.items():
                scaled_w = copy.deepcopy(w_data)
                scaled_w["id"] = f"land_{scale_name}_{w_id}"
                scaled_w["name"] = f"{scale_name.capitalize()} {base_name}"
                scaled_w["scale_type"] = scale_name
                
                # Scale Stats (Selective)
                # We only want to scale Strength/Damage to hit the HP targets.
                # Range and Attacks should remain functional for the tactical grid.
                for stat, val in scaled_w.get("stats", {}).items():
                    if isinstance(val, (int, float)):
                        if stat in ["S", "Str", "D", "Damage", "strength"]:
                            scaled_w["stats"][stat] = val * factor
                        elif stat in ["Range", "range"]:
                            # Soft scale range: don't let it fall below 12 for most weapons
                            scaled_w["stats"][stat] = max(12, val)
                        elif stat in ["AP", "ap"]:
                            # Keep AP as is or slight reduction
                            scaled_w["stats"][stat] = val
                        elif stat in ["Attacks", "attacks", "A"]:
                            # Keep attacks to maintain volume of fire
                            scaled_w["stats"][stat] = val
                
                # Add to scale-specific sub-arsenal
                land_arsenal[scale_name][scaled_w["id"]] = scaled_w
                
        return land_arsenal
        
    def _design_land_unit(self, faction: str, ch_id: str, chassis: Dict, multi_arsenal: Dict, doctrine: str, style: str, role: str) -> Dict:
        """Unified designer for all land units using hardpoint layouts."""
        
        design = {
            "blueprint_id": f"{faction.lower()}_{ch_id}_{role.lower()}",
            "name": f"{faction} {role} {chassis['name']}",
            "type": ch_id,
            "faction": faction,
            "category": chassis.get("category", "Land Unit"),
            "logic_role": chassis.get("logic_role", "unknown"),
            "collision_shape": chassis.get("collision_shape", "box"),
            "style": style,
            "base_stats": {
                "hp": chassis["base_hp"],
                "armor": chassis.get("base_armor", 0),
                "speed": chassis.get("base_speed", 5),
                "soft_attack": 0,
                "hard_attack": 0
            },
            "components": [],
            "traits": [role],
            "abilities": {}
        }
        
        hardpoints = chassis.get("hardpoints", {})
        squad_size = chassis.get("squad_size", 1)
        design["squad_members"] = []
        
        # Fit Components into Hardpoints for each squad member
        for i in range(squad_size):
            member_components = []
            m_role = "Rifleman"
            if squad_size > 1:
                if i == 0: m_role = "Leader"
                elif i < (squad_size // 4) + 1: m_role = "Specialist"
                
            for slot_name, slot_type in hardpoints.items():
                if slot_type == "defense":
                    mod = self._select_defense_module(doctrine, role)
                    if mod:
                        member_components.append({"slot": slot_name, "component": mod["name"]})
                        design["base_stats"]["hp"] += mod["stats"].get("hp_bonus", 0)
                        design["base_stats"]["armor"] += mod["stats"].get("armor_bonus", 0)
                elif slot_type == "utility":
                    mod_type = "util_jump" if self.rng.random() > 0.5 else "util_optic"
                    mod = self.modules.get(mod_type)
                    if mod:
                        member_components.append({"slot": slot_name, "component": mod["name"]})
                        design["base_stats"]["speed"] += mod["stats"].get("speed_bonus", 0)
                else:
                    # Weapon Selection
                    w_scale = slot_type
                    w_cat = "General"
                    if m_role == "Specialist":
                        w_cat = "Anti-Armor" if self.rng.random() > 0.3 else "General"
                    elif m_role == "Leader":
                        w_cat = "General"
                    
                    if w_scale in ["heavy", "titan"]: 
                        w_cat = "Anti-Armor"
                    
                    # Unified Candidate Pool (Specialized Equipment + Scaled Arsenal)
                    candidates = [v for v in self.equipment.values() if v.get("scale") == w_scale]
                    candidates.extend(list(multi_arsenal.get(w_scale, {}).values()))
                    
                    if not candidates: # Fallback to light
                        candidates = [v for v in self.equipment.values() if v.get("scale") == "light"]
                        candidates.extend(list(multi_arsenal.get("light", {}).values()))
                    
                    # Inject IDs
                    for c in candidates:
                        if "id" not in c:
                            c["id"] = c.get("name", "unknown").lower().replace(" ", "_")

                    is_melee_slot = "melee" in slot_name.lower()
                    is_sidearm_slot = "sidearm" in slot_name.lower()
                    
                    # Filter by Style (Energy/Kinetic) with 80% weight
                    if self.rng.random() < 0.8:
                        style_candidates = [c for c in candidates if style.lower() in [t.lower() for t in c.get("tags", [])]]
                        if style_candidates:
                            candidates = style_candidates

                    if is_melee_slot:
                        candidates = [c for c in candidates if "melee" in c.get("tags", [])]
                    elif is_sidearm_slot:
                        candidates = [c for c in candidates if "sidearm" in c.get("tags", [])]
                    elif w_scale == "light":
                        candidates = [c for c in candidates if "melee" not in c.get("tags", [])]
                        
                    if candidates:
                        weapon = self.rng.choice(candidates)
                    else:
                        weapon = self._select_weapon_from_scale(multi_arsenal, w_scale, doctrine, style, w_cat)
                    if weapon:
                        member_components.append({"slot": slot_name, "component": weapon["id"]})
                        w_stats = weapon.get("stats", {})
                        power = w_stats.get("power", 1)
                        
                        # Aggregated Attack Power
                        if w_cat == "Anti-Armor":
                            design["base_stats"]["hard_attack"] += power
                            design["base_stats"]["soft_attack"] += power * 0.4
                        else:
                            design["base_stats"]["soft_attack"] += power
                            design["base_stats"]["hard_attack"] += power * 0.3
            
            design["squad_members"].append({
                "role": m_role,
                "components": member_components
            })
            design["components"].extend(member_components)
                        
        # Role bonuses
        if role == "Elite":
            design["base_stats"]["hp"] = int(design["base_stats"]["hp"] * 1.5)
            design["base_stats"]["armor"] = int(design["base_stats"]["armor"] * 1.2)
            design["cost"] = int(chassis["base_cost"] * 2.0)
        elif role == "Assault":
             design["base_stats"]["soft_attack"] *= 1.3
             design["base_stats"]["speed"] *= 1.2
             design["cost"] = int(chassis["base_cost"] * 1.3)
        else:
            design["cost"] = chassis["base_cost"]
            
        # Add weapon cost
        design["cost"] += int(design["base_stats"]["soft_attack"] + design["base_stats"]["hard_attack"])
        
        # Logging & Persistence
        self.logger.log(LogCategory.AI, f"Designed land unit: {design['name']} ({role}) for {faction}")
        self._persist_design(design, faction)
        
        return design

    def _persist_design(self, design: Dict[str, Any], faction: str):
        """Saves the design to the reports directory for inspection."""
        # Use log_dir if available (typically reports/runs/RunID)
        base_dir = self.logger.log_dir if hasattr(self.logger, "log_dir") else self.output_dir
        
        design_dir = os.path.join(base_dir, "designs", faction.replace(" ", "_"))
        if not os.path.exists(design_dir):
            os.makedirs(design_dir, exist_ok=True)
            
        filename = f"land_{design['blueprint_id']}.json"
        filepath = os.path.join(design_dir, filename)
        
        try:
            with open(filepath, "w", encoding='utf-8') as f:
                json.dump(design, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to persist land design {design['name']}: {e}")


    def _select_weapon_from_scale(self, multi_arsenal: Dict, scale: str, doctrine: str, style: str, category: str) -> Dict:
        """Picks a weapon, prioritizing specialized land equipment over scaled ship weapons."""
        
        # 1. Search Specialized Land Equipment
        land_candidates = []
        for k, v in self.equipment.items():
            if v.get("scale") == scale:
                item = v.copy()
                item["id"] = k
                land_candidates.append(item)

        # Style Filter (80% weight)
        if land_candidates and self.rng.random() < 0.8:
            style_match = [c for c in land_candidates if style.lower() in [t.lower() for t in c.get("tags", [])]]
            if style_match:
                land_candidates = style_match

        # Doctrine/Category Filter
        if land_candidates:
            if category == "Anti-Armor":
                aa_candidates = [c for c in land_candidates if "anti_armor" in c.get("tags", [])]
                if aa_candidates: return self.rng.choice(aa_candidates)
            
            return self.rng.choice(land_candidates)

        # 2. Fallback to Scaled Ship Arsenal
        candidates = list(multi_arsenal.get(scale, {}).values())
        if style:
             style_cands = [c for c in candidates if style.lower() in [t.lower() for t in c.get("tags", [])]]
             if style_cands: candidates = style_cands

        if not candidates:
            candidates = list(multi_arsenal.get("light", {}).values())
            
        if not candidates: return None
        return self.rng.choice(candidates)


    def _select_defense_module(self, doctrine: str, role: str) -> str:
        """Selects appropriate defense module from blueprints."""
        if doctrine == "Defensive" or role == "Elite":
            return self.modules.get("vehicle_armor_composite") or self.modules.get("land_armor_heavy")
        return self.modules.get("land_armor_medium") or self.modules.get("land_armor_light")

    def _determine_doctrine(self, traits: List[str]) -> str:
        """Determines fitting strategy based on traits."""
        if not traits: return "Balanced"
        traits_str = " ".join(traits).lower()
        if any(t in traits_str for t in ["strong", "aggressive", "militarist"]): return "Aggressive"
        if any(t in traits_str for t in ["defensive", "fortified", "resilient"]): return "Defensive"
        if any(t in traits_str for t in ["fast", "agile"]): return "Speed"
        return "Balanced"

    def _determine_style(self, faction: str, traits: List[str]) -> str:
        """Determines weapon preference (Energy, Kinetic, Organic) based on faction identity."""
        f_lower = faction.lower()
        if any(x in f_lower for x in ["transcendent", "order", "guardian", "ancient"]): return "Energy"
        if any(x in f_lower for x in ["steel", "syndicate", "marauder", "clans"]): return "Kinetic"
        if any(x in f_lower for x in ["biotide", "hive", "spawn"]): return "Organic"
        
        # Trait fallbacks
        traits_str = " ".join(traits).lower()
        if "technological" in traits_str: return "Energy"
        if "brutal" in traits_str: return "Kinetic"
        if "adaptive" in traits_str: return "Organic"
        
        return "Kinetic" # Default


