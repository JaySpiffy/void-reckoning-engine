from typing import Any
import os
import json
import random

class ProductionPlanner:
    def __init__(self, ai_manager: Any):
        self.ai = ai_manager
        self.engine = ai_manager.engine

    def process_innovation_cycle(self, faction_name: str):
        """
        Periodically triggers technological innovation for a faction.
        Can result in a Hull Mutation or a Weapon Paradigm Shift.
        """
        from src.core.config import UNIVERSE_ROOT
        f_obj = self.engine.factions.get(faction_name)
        if not f_obj: return
        
        # 1. Determine Innovation Type
        # 70% Hull Mutation, 30% Weapon Invention
        innovation_roll = random.random()
        dna = self.ai.personality_manager.get_faction_dna(faction_name)
        
        if innovation_roll < 0.70:
            self._handle_hull_mutation(faction_name, f_obj, dna, UNIVERSE_ROOT)
        else:
            self._handle_weapon_invention(faction_name, f_obj, dna, UNIVERSE_ROOT)

        # Always trigger a design refresh after innovation
        self.ai.update_ship_designs(faction_name)

    def _handle_hull_mutation(self, faction_name: str, f_obj: Any, dna: Any, universe_root: str):
        """Logic for evolving a new ship hull."""
        from src.factories.hull_mutation_factory import HullMutationFactory
        mutator = HullMutationFactory()
        
        hulls_path = os.path.join(universe_root, "base", "units", "base_ship_hulls.json")
        if os.path.exists(hulls_path):
            with open(hulls_path, 'r', encoding='utf-8') as f:
                hulls = json.load(f)
            
            base_id = random.choice(list(hulls.keys()))
            base_hull = hulls[base_id]
            
            mutated = mutator.mutate_hull(faction_name, base_id, base_hull, dna)
            
            if not hasattr(f_obj, 'custom_hulls'): f_obj.custom_hulls = {}
            f_obj.custom_hulls[mutated["id"]] = mutated
            
            if self.engine.logger:
                self.engine.logger.campaign(f"[INNOVATION] {faction_name} evolved a new ship hull: {mutated['name']}!")

    def _handle_weapon_invention(self, faction_name: str, f_obj: Any, dna: Any, universe_root: str):
        """Logic for inventing a new weapon paradigm."""
        from src.factories.weapon_factory import ProceduralWeaponFactory
        
        paradigms = [
            {"id": "singularity_projector", "name": "Singularity Projector", "dna": "atom_mass", "prefixes": ["Gravitic", "Collapse", "Event-Horizon"]},
            {"id": "chrono_beam", "name": "Chrono-Beam", "dna": "atom_information", "prefixes": ["Timeless", "Recursive", "Delayed"]},
            {"id": "aether_lance", "name": "Aether Lance", "dna": "atom_aether", "prefixes": ["Spirit", "Ghost", "Hallowed"]},
            {"id": "bio_electric_ray", "name": "Bio-Electric Ray", "dna": "atom_volatility", "prefixes": ["Synaptic", "Viral", "Neural"]}
        ]
        
        paradigm = random.choice(paradigms)
        base_bp_path = os.path.join(universe_root, "base", "weapons", "base_weapon_blueprints.json")
        
        if os.path.exists(base_bp_path):
            with open(base_bp_path, 'r', encoding='utf-8') as f:
                blueprints = json.load(f)
            
            factory = ProceduralWeaponFactory(blueprints)
            
            new_base = {
                "name": paradigm["name"],
                "category": "Experimental",
                "elemental_signature": {paradigm["dna"]: 50.0},
                "power_multiplier": 1.5,
                "cost": 500
            }
            
            factory.inject_paradigm(paradigm["id"], new_base)
            new_arsenal = factory.generate_arsenal(faction_name, dna, count=3, custom_prefixes=paradigm["prefixes"])
            
            f_obj.weapon_registry.update(new_arsenal)
            
            if self.engine.logger:
                self.engine.logger.campaign(f"[INNOVATION] {faction_name} invented a new weapon paradigm: {paradigm['name']}!")
