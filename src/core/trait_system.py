
from typing import Dict, List, Any, Optional
import json
import random
import os

class Trait:
    """
    Represents a distinctive characteristic that modifies stats or behavior.
    Inspired by Stellaris species traits.
    """
    def __init__(self, id: str, name: str, category: str, 
                 modifiers: Dict[str, float], 
                 description: str = "",
                 rarity: str = "common",
                 requirements: List[str] = None,
                 conflicts: List[str] = None):
        self.id = id
        self.name = name
        self.category = category  # physical, mental, economic, combat, special
        self.modifiers = modifiers  # e.g., {"hp": 0.2, "damage": -0.1}
        self.description = description
        self.rarity = rarity
        self.requirements = requirements or []
        self.conflicts = conflicts or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "modifiers": self.modifiers,
            "description": self.description,
            "rarity": self.rarity,
            "requirements": self.requirements,
            "conflicts": self.conflicts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trait':
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            modifiers=data["modifiers"],
            description=data.get("description", ""),
            rarity=data.get("rarity", "common"),
            requirements=data.get("requirements"),
            conflicts=data.get("conflicts")
        )

class TraitPool:
    """
    A collection of traits within a specific category, weighted by rarity.
    """
    def __init__(self, category: str):
        self.category = category
        self.traits: Dict[str, Trait] = {}
        # Rarity weights for random selection
        self.rarity_weights = {
            "common": 60,
            "uncommon": 25,
            "rare": 10,
            "unique": 5
        }

    def add_trait(self, trait: Trait):
        if trait.category != self.category:
            # We allow flexible pools, but warn typically
            pass 
        self.traits[trait.id] = trait

    def select_random(self, count: int = 1, exclude_ids: List[str] = None) -> List[Trait]:
        """Selects N unique traits from the pool based on rarity weights."""
        available = [t for t in self.traits.values() if t.id not in (exclude_ids or [])]
        if not available:
            return []
            
        selected = []
        for _ in range(count):
            if not available: break
            
            # Weighted choice
            weights = [self.rarity_weights.get(t.rarity, 20) for t in available]
            choice = random.choices(available, weights=weights, k=1)[0]
            
            selected.append(choice)
            available.remove(choice)
            
            # Filter conflicts immediately? 
            # Ideally done by the caller, but simple exclusion helps consistency
            if choice.conflicts:
                available = [t for t in available if t.id not in choice.conflicts]
                
        return selected

class TraitSystem:
    """
    Manager for loading, storing, and applying traits.
    """
    def __init__(self):
        self.pools: Dict[str, TraitPool] = {
            "physical": TraitPool("physical"),
            "mental": TraitPool("mental"),
            "economic": TraitPool("economic"),
            "combat": TraitPool("combat"),
            "special": TraitPool("special")
        }
        self.all_traits: Dict[str, Trait] = {}

    def register_trait(self, trait: Trait):
        self.all_traits[trait.id] = trait
        
        # Add to appropriate pool (create if missing)
        cat = trait.category.lower()
        if cat not in self.pools:
            self.pools[cat] = TraitPool(cat)
        self.pools[cat].add_trait(trait)

    def load_traits_from_directory(self, directory: str = "data/traits"):
        """Loads all JSON trait files from a directory."""
        import os
        import json
        
        if not os.path.exists(directory):
            print(f"Warning: Trait directory {directory} not found.")
            return

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                try:
                    self.load_traits_from_file(filepath)
                except Exception as e:
                    print(f"Error loading traits from {filename}: {e}")

    def load_traits_from_file(self, filepath: str):
        """Loads traits from a JSON file and registers them."""
        import json
        import os
        
        if not os.path.exists(filepath):
             print(f"Warning: Trait file {filepath} not found.")
             return
             
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
                # Supports list of traits or dict with "traits" key
                trait_list = data.get("traits", []) if isinstance(data, dict) else data
                
                count = 0
                for trait_data in trait_list:
                    # Create generic Trait object
                    t = Trait(**trait_data)
                    self.register_trait(t)
                    count += 1
                # print(f"Loaded {count} traits from {filepath}")
            except json.JSONDecodeError as e:
                print(f"Error parsing {filepath}: {e}")

    def get_trait(self, trait_id: str) -> Optional[Trait]:
        return self.all_traits.get(trait_id)
        
    def apply_traits_to_stats(self, base_stats: Dict[str, float], traits: List[Trait]) -> Dict[str, float]:
        """
        Applies a list of traits modifiers to a dictionary of base stats.
        Formula: Final = Base * (1 + sum(percent_mods)) + sum(flat_mods)
        """
        final_stats = base_stats.copy()
        multipliers = {}
        
        # 1. Aggregate Modifiers
        for t in traits:
            for stat, value in t.modifiers.items():
                if stat.endswith("_flat"):
                    # Apply flat immediately? Or summarize?
                    # Summarize first
                    base_key = stat.replace("_flat", "")
                    final_stats[base_key] = final_stats.get(base_key, 0) + value
                else:
                    # Multiplier
                    multipliers[stat] = multipliers.get(stat, 0.0) + value
                    
        # 2. Apply Multipliers
        for stat, mult in multipliers.items():
            if stat in final_stats:
                final_stats[stat] *= (1.0 + mult)
                
        # 3. Integer Rounding (Game Logic)
        for k, v in final_stats.items():
            if k in ["hp", "armor", "damage", "cost"]:
                final_stats[k] = int(v) if v > 0 else 0
                
        return final_stats
        
    # --- Integration of New Sub-Systems ---
    
    def initialize_subsystems(self):
        """Lazy load sub-systems to avoid circular imports during init if needed."""
        from src.core.trait_tree import TraitTree
        from src.core.trait_synergy import TraitSynergy
        from src.core.civic_system import CivicSystem
        from src.core.ethics_system import EthicsSystem
        from src.core.origin_system import OriginSystem
        from src.core.ascension_system import AscensionSystem
        
        self.civics = CivicSystem()
        self.ethics = EthicsSystem()
        self.origins = OriginSystem()
        self.ascension = AscensionSystem()
        self.synergies = [] # List[TraitSynergy]
        self.trees = {} # Dict[str, TraitTree]
        
    def register_synergy(self, synergy):
        if not hasattr(self, 'synergies'): self.initialize_subsystems()
        self.synergies.append(synergy)

    def check_synergies(self, current_traits: List[str]) -> Dict[str, float]:
        """Calculates total bonuses from all active synergies."""
        if not hasattr(self, 'synergies'): return {}
        
        total_bonuses = {}
        for syn in self.synergies:
            bonus = syn.calculate_synergy_bonus(current_traits)
            for k, v in bonus.items():
                total_bonuses[k] = total_bonuses.get(k, 0.0) + v
        return total_bonuses
