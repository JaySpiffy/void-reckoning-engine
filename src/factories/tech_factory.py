import random
import json
import os
from typing import Dict, List, Any, Optional

class ProceduralTechGenerator:
    """
    Generates unique tech trees based on deterministic seeds.
    Implements 'Self-Evolving Tech Trees'.
    Note: DNA and Atom-level logic has been decommissioned.
    """
    def __init__(self, universe_id: str):
        self.seed = universe_id
        self.rng = random.Random(self.seed)

    def evolve_tree(self, base_tree: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mutates a base tech tree to create a universe-specific variant.
        Mutation: Cost jitter and topology changes only.
        """
        evolved_nodes = {}
        evolved_units = base_tree.get("units", {}).copy()
        
        # 1. Cost Mutation (Deterministic Jitter)
        for tech_id, original_cost in base_tree.get("techs", {}).items():
            # Apply deterministic jitter (+/- 10%)
            jitter = self.rng.uniform(0.9, 1.1)
            new_cost = int(original_cost * jitter)
            evolved_nodes[tech_id] = new_cost
            
        # 2. Topology Mutation (Prerequisite Swap)
        all_tech_ids = list(evolved_nodes.keys())
        keys_to_mutate = [k for k in evolved_units.keys() if self.rng.random() < 0.1]
        
        for unit_name in keys_to_mutate:
            current_parent = evolved_units[unit_name]
            if not all_tech_ids: continue
            new_parent = self.rng.choice(all_tech_ids)
            if new_parent != unit_name and new_parent != current_parent:
                 evolved_units[unit_name] = new_parent
                 
        return {
            "techs": evolved_nodes,
            "units": evolved_units
        }
        
    
    def generate_procedural_tree(self, faction_name: str, base_tree: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extends the existing tree with procedurally generated nodes.
        Includes Generic Categories AND Specific Weapon Unlocks from Universal Registry.
        """
        techs = base_tree.get("techs", {}).copy()
        prereqs = base_tree.get("prerequisites", {}).copy()
        effects = {}
        
        # 1. Generic Improvements
        categories = {
            "Offense": ["Laser", "Plasma", "Kinetic", "Missile", "Melee"],
            "Defense": ["Shield", "Armor", "Hull", "Point-Defense", "Stealth"],
            "Economy": ["Mining", "Manufacturing", "Trade", "Logistics", "Energy"],
            "Mobility": ["Engine", "Flux", "Thruster", "Navigator", "Sensors"]
        }
        
        roots = [t for t in techs if "Basic" in t or "Tier 1" in t or techs[t] <= 1000]
        if not roots: roots = list(techs.keys())[:1]
        
        # ... (Existing Generic Generation) ...
        for cat_name, subcats in categories.items():
            prev_tech = self.rng.choice(roots) if roots else None
            for tier in range(1, 11):
                for sub in subcats:
                    if self.rng.random() < 0.2: # Reduced chance for generics to make room for Weapons 
                        name = self._generate_tech_name(faction_name, cat_name, sub, tier)
                        t_id = f"Tech_{faction_name}_{name.replace(' ', '_')}"
                        cost = int(1000 * (tier ** 1.5))
                        techs[t_id] = cost
                        if prev_tech:
                            prereqs.setdefault(t_id, []).append(prev_tech)
                        
                        effect_val = 1 + (tier * 1)
                        effect_type = self._get_effect_type(sub)
                        effects[t_id] = [f"+{effect_val}% {effect_type}"]
                        if self.rng.random() < 0.5:
                            prev_tech = t_id
                            
        # 2. Universal & Procedural Weaponry Integration (Grand Sci-Fi Unification)
        component_paths = [
            os.path.join("universes", "void_reckoning", "factions", "weapon_registry.json"),
            os.path.join("universes", "base", "weapons", "base_land_equipment.json"),
            os.path.join("src", "data", "universal_weaponry.json"),
            os.path.join("data", "ships", "procedural_components.json")
        ]
        
        for reg_path in component_paths:
            if os.path.exists(reg_path):
                try:
                    with open(reg_path, 'r') as f:
                        comp_db = json.load(f)
                        
                    # Handle different registry formats
                    items = []
                    if isinstance(comp_db, dict) and "components" in comp_db:
                        items = comp_db["components"]
                    elif isinstance(comp_db, dict):
                        # Registry format: { "id": { data } }
                        for k, v in comp_db.items():
                            if isinstance(v, dict):
                                item = v.copy()
                                if "id" not in item: item["id"] = k
                                items.append(item)
                    
                    for item in items:
                        # Determine Cost & Tier
                        tier = item.get("tier") or item.get("tech_tier") or item.get("tech_level") or 1
                        # Research costs scale with tier
                        cost = int(800 * (tier ** 1.8))
                        
                        name = item.get("name") or item.get("id", "Unknown")
                        tech_key = f"Tech_Unlock_{item.get('id', name).replace(' ', '_')}"
                        
                        # Add to Tree
                        techs[tech_key] = cost
                        effects[tech_key] = [f"Unlocks: {name}"]
                        
                        # Prerequisite Logic
                        if tier == 1:
                            if roots:
                                prereqs.setdefault(tech_key, []).append(self.rng.choice(roots))
                        else:
                            # Link to a relevant tech of lower tier
                            candidates = [t for t, c in techs.items() if c < cost and c > cost * 0.1 and t != tech_key]
                            if candidates:
                                prereqs.setdefault(tech_key, []).append(self.rng.choice(candidates))
                                
                except Exception as e:
                    print(f"[TechFactory] Failed to load components from {reg_path}: {e}")

        # 3. Ship Hull Integration (Class Unlocks)
        try:
            hull_path = os.path.join("data", "ships", "hulls.json")
            if os.path.exists(hull_path):
                with open(hull_path, 'r') as f:
                    hull_db = json.load(f)
                    
                for hull in hull_db.get("hulls", []):
                    unlock_key = hull.get("unlock_tech")
                    if not unlock_key: continue
                    
                    tier = hull.get("tech_tier", 1)
                    # Hull research is expensive
                    cost = int(2500 * (tier ** 1.8))
                    
                    # Add to Tree
                    techs[unlock_key] = cost
                    effects[unlock_key] = [f"Unlocks Class: {hull['name']}"]
                    
                    # Prerequisites
                    # Link to lower tier hulls if possible?
                    # E.g. Destroyer needs Corvette? No, Corvette is default.
                    # Link to Generic Engineering to keep it clean.
                    
                    # Simple Tier-based Prereq (Link to Generic Tier-1 improvement)
                    # Or force linear progression: Battlecruiser needs Cruiser?
                    # The JSON doesn't define linear path.
                    # Let's link to RANDOM known tech of comparable cost/tier.
                    candidates = [t for t, c in techs.items() if c < cost and c > cost * 0.2]
                    if candidates:
                        prereqs.setdefault(unlock_key, []).append(self.rng.choice(candidates))

        except Exception as e:
            print(f"[TechFactory] Failed to load hull tech: {e}")

        # 4. Ground Unit Integration (Class Unlocks)
        try:
            ground_path = os.path.join("data", "ground", "unit_classes.json")
            if os.path.exists(ground_path):
                with open(ground_path, 'r') as f:
                    ground_db = json.load(f)
                    
                for u_class in ground_db.get("classes", []):
                    unlock_key = u_class.get("unlock_tech")
                    if not unlock_key: continue
                    
                    tier = u_class.get("tech_tier", 1)
                    # Ground unit research costs
                    cost = int(1500 * (tier ** 1.7))
                    
                    # Add to Tree
                    techs[unlock_key] = cost
                    effects[unlock_key] = [f"Unlocks Class: {u_class['name']}"]
                    
                    # Prerequisites - Link to RANDOM known tech of comparable cost/tier
                    candidates = [t for t, c in techs.items() if c < cost and c > cost * 0.1]
                    if candidates:
                        prereqs.setdefault(unlock_key, []).append(self.rng.choice(candidates))

        except Exception as e:
            print(f"[TechFactory] Failed to load ground unit tech: {e}")

        # 5. Utility Technology Integration (Tractor Beam / Interdiction)
        utils = [
            ("Tech_Unlock_Tractor_Beam", "Tractor Beam", 4, 4500),
            ("Tech_Unlock_Interdiction", "Interdiction Field", 5, 8000)
        ]
        for tech_id, name, tier, cost in utils:
            techs[tech_id] = cost
            effects[tech_id] = [f"Enables {name} Utility Modules"]
            
            # Link to RANDOM mid-high tier tech
            candidates = [t for t, c in techs.items() if c < cost and c > cost * 0.2]
            if candidates:
                prereqs.setdefault(tech_id, []).append(self.rng.choice(candidates))

        return {
            "techs": techs,
            "prerequisites": prereqs,
            "effects": effects
        }

    def _generate_tech_name(self, faction: str, category: str, subcat: str, tier: int) -> str:
        roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
        prefixes = {
            "Aurelian_Hegemony": ["Aurelian", "Standard", "Heavy", "Mars-Pattern", "Solar", "Terra", "High Arbiter's", "Crusade", "High", "Utimate"],
            "SteelBound_Syndicate": ["Reinforced", "Iron", "Siege", "Trench", "Bunker", "Heavy", "Artillery", "Fortified", "Unbroken", "Eternal"],
            "Default": ["Advanced", "Improved", "Experimental", "Optimized", "Quantum", "Hyper", "Ultra", "Mega", "Giga", "Omega"]
        }
        f_key = "Default"
        for k in prefixes:
             if k in faction: f_key = k
        if faction in prefixes: f_key = faction
        
        prefix = prefixes[f_key][(tier - 1) % len(prefixes[f_key])]
        return f"{prefix} {subcat} {roman[tier-1]}"

    def _get_effect_type(self, subcat: str) -> str:
        mapping = {
            "Laser": "Energy Damage", "Plasma": "AP Damage", "Kinetic": "Ballistic Damage",
            "Missile": "Explosive Damage", "Melee": "Melee Damage",
            "Shield": "Shield Cap", "Armor": "Armor Value", "Hull": "Hit Points",
            "Mining": "Mineral Income", "Trade": "Trade Income",
            "Engine": "Speed", "Flux": "Flux Speed"
        }
        return mapping.get(subcat, "Efficiency")
