import random
import json
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
        """
        techs = base_tree.get("techs", {}).copy()
        prereqs = base_tree.get("prerequisites", {}).copy()
        effects = {}
        
        categories = {
            "Offense": ["Laser", "Plasma", "Kinetic", "Missile", "Melee"],
            "Defense": ["Shield", "Armor", "Hull", "Point-Defense", "Stealth"],
            "Economy": ["Mining", "Manufacturing", "Trade", "Logistics", "Energy"],
            "Mobility": ["Engine", "Flux", "Thruster", "Navigator", "Sensors"]
        }
        
        roots = [t for t in techs if "Basic" in t or "Tier 1" in t or techs[t] <= 1000]
        if not roots: roots = list(techs.keys())[:1]
        
        for cat_name, subcats in categories.items():
            prev_tech = self.rng.choice(roots) if roots else None
            for tier in range(1, 11):
                for sub in subcats:
                    if self.rng.random() < 0.7: 
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
