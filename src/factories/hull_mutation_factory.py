import random
import copy
from typing import Dict, List, Any, Optional

class HullMutationFactory:
    """
    Applies evolutionary mutations to ship hulls during simulation.
    Mutations are driven by Faction DNA and technological progress.
    """
    
    def __init__(self):
        self.rng = random.Random()
        
        # Mutation Templates
        self.mutation_traits = {
            "Void-Forged": {
                "base_hp_mult": 0.8,
                "base_speed_mult": 1.3,
                "hardpoint_bonus": {"module_utility": 1},
                "dna_affinity": "atom_frequency"
            },
            "Iron-Clad": {
                "base_hp_mult": 1.4,
                "base_speed_mult": 0.7,
                "hardpoint_bonus": {"module_defense": 1},
                "dna_affinity": "atom_mass"
            },
            "Reactive-Plated": {
                "base_hp_mult": 1.1,
                "base_speed_mult": 1.0,
                "hardpoint_bonus": {"module_defense": 1},
                "dna_affinity": "atom_cohesion"
            },
            "Crest-Hulled": {
                "base_hp_mult": 1.0,
                "base_speed_mult": 1.1,
                "hardpoint_bonus": {"module_utility": 1},
                "dna_affinity": "atom_focus"
            },
            "Living-Biomass": {
                "base_hp_mult": 1.2,
                "base_speed_mult": 1.1,
                "hardpoint_bonus": {},
                "dna_affinity": "atom_volatility",
                "traits": ["Regenerative"]
            }
        }

    def mutate_hull(self, faction_name: str, base_id: str, base_hull: Dict, faction_dna: Dict[str, float]) -> Dict:
        """Creates a unique mutated variant of a base hull."""
        
        # 1. Select Mutation based on DNA affinity
        primary_dna = max(faction_dna, key=faction_dna.get)
        
        # Filter traits that match DNA or pick random matching
        candidates = [k for k, v in self.mutation_traits.items() if v.get("dna_affinity") == primary_dna]
        if not candidates:
            candidates = list(self.mutation_traits.keys())
            
        trait_name = self.rng.choice(candidates)
        trait_data = self.mutation_traits[trait_name]
        
        # 2. Apply Stats
        mutated = copy.deepcopy(base_hull)
        mutated["name"] = f"{trait_name} {base_hull['name']}"
        mutated["id"] = f"{base_id}_{trait_name.lower().replace('-', '_')}"
        
        mutated["base_hp"] = int(mutated["base_hp"] * trait_data.get("base_hp_mult", 1.0))
        mutated["base_speed"] = int(mutated["base_speed"] * trait_data.get("base_speed_mult", 1.0))
        
        # 3. Add Hardpoints
        hp_bonus = trait_data.get("hardpoint_bonus", {})
        for hp_type, count in hp_bonus.items():
            if "hardpoints" not in mutated: mutated["hardpoints"] = {}
            mutated["hardpoints"][hp_type] = mutated["hardpoints"].get(hp_type, 0) + count
            
        # 4. Inject Traits
        if "base_traits" not in mutated: mutated["base_traits"] = []
        mutated["base_traits"].extend(trait_data.get("traits", []))
        mutated["base_traits"].append(f"Evolution: {trait_name}")
        
        return mutated
