
from typing import Dict, List, Any, Optional
import random
import json
import os
from src.core.trait_system import TraitSystem, Trait
from src.core.expanded_stats import ExpandedStats
from src.core.ship_design_system import ShipDesigner, ShipHull, ShipComponent, ShipDesign
from src.core.ground_combat_system import GroundUnitClass, Regiment

class TraitBasedGenerator:
    """
    Generates procedural factions, units, and weapons using the Trait System.
    """
    def __init__(self, trait_system: TraitSystem, data_dir: str = "data"):
        self.trait_system = trait_system
        self.data_dir = data_dir
        
        # Deep Simulation Systems
        self.hulls: Dict[str, ShipHull] = {}
        self.components: Dict[str, ShipComponent] = {}
        self.ground_classes: Dict[str, GroundUnitClass] = {}
        self.ship_designer: Optional[ShipDesigner] = None
        
        self._load_deep_data()

    def _load_deep_data(self):
        """Loads Hulls, Components, and UnitClasses."""
        # 1. Ships
        try:
            with open(os.path.join(self.data_dir, "ships/hulls.json"), 'r') as f:
                for h in json.load(f)["hulls"]:
                    self.hulls[h["id"]] = ShipHull(**h)
            
            with open(os.path.join(self.data_dir, "ships/components.json"), 'r') as f:
                for c in json.load(f)["components"]:
                    self.components[c["id"]] = ShipComponent(**c)
            
            self.ship_designer = ShipDesigner(self.components)
        except Exception as e:
            print(f"Warning: Failed to load ship data: {e}")

        # 2. Ground
        try:
            with open(os.path.join(self.data_dir, "ground/unit_classes.json"), 'r') as f:
                for u in json.load(f)["classes"]:
                    # Deserialize stats manually since it's nested
                    stats_data = u.pop("stats")
                    from src.core.ground_combat_system import GroundStats
                    gstats = GroundStats(**stats_data)
                    self.ground_classes[u["id"]] = GroundUnitClass(stats=gstats, **u)
        except Exception as e:
             print(f"Warning: Failed to load ground data: {e}")
        
    def generate_faction(self, name: str = "Unknown Faction") -> Dict[str, Any]:
        """
        Generates a complete faction profile with Traits, Civics, and Ethics.
        """
        # 1. Select Base Traits (Physical, Mental)
        # using a safer selection method that respects conflicts
        traits = []
        traits.extend(self._safe_select_traits("physical", 1, traits))
        traits.extend(self._safe_select_traits("mental", 1, traits))
        traits.extend(self._safe_select_traits("economic", 1, traits))
        traits.extend(self._safe_select_traits("combat", 1, traits))
        
        # 2. Select Ethics
        ethics = self._generate_ethics(traits)
        
        # 3. Select Civics
        civics = self._generate_civics(traits, ethics)
        
        # 4. Determine Origin (Future)
        origin = "prosperous_unification" 

        trait_ids = [t.id for t in traits]
        
        return {
            "name": name,
            "traits": trait_ids,
            "ethics": ethics,
            "civics": civics,
            "origin": origin,
            "description": self._generate_description(traits, ethics, civics)
        }

    def _safe_select_traits(self, category: str, count: int, current_traits: List[Trait]) -> List[Trait]:
        """Selects traits respecting conflicts and requirements."""
        pool = self.trait_system.pools.get(category)
        if not pool: return []
        
        candidates = list(pool.traits.values())
        selected = []
        
        # Convert current_traits to ID list for easy checking
        current_ids = {t.id for t in current_traits}
        
        attempts = 0
        while len(selected) < count and attempts < 20:
            attempts += 1
            candidate = random.choice(candidates)
            
            # Check if already picked
            if candidate.id in current_ids or candidate in selected:
                continue
                
            # Check Conflicts
            if candidate.conflicts:
                conflict_found = False
                for c_id in candidate.conflicts:
                    if c_id in current_ids or any(s.id == c_id for s in selected):
                        conflict_found = True
                        break
                if conflict_found: continue
                
            # Check Requirements (if any)
            if candidate.requirements:
                reqs_met = all(r in current_ids for r in candidate.requirements)
                if not reqs_met: continue
                
            selected.append(candidate)
            
        return selected

    def _generate_ethics(self, traits: List[Trait]) -> List[str]:
        """Selects ethics based on trait weights/flavor."""
        # For now, random but we should bias based on 'Aggressive' -> 'Militarist'
        available = list(self.trait_system.ethics.available_ethics.keys())
        if not available: return []
        return random.sample(available, min(2, len(available)))

    def _generate_civics(self, traits: List[Trait], ethics: List[str]) -> List[str]:
        """Selects civics compatible with ethics."""
        available = list(self.trait_system.civics.available_civics.keys())
        if not available: return []
        return random.sample(available, min(2, len(available)))


    def generate_unit(self, faction_traits: List[str], role: str = "infantry") -> Dict[str, Any]:
        """
        Generates a Unit profile. Automatically determines if Space or Ground based on role.
        """
        
        # A. Space Unit (Hull Check)
        if role in self.hulls:
            return self._generate_ship(faction_traits, role)
            
        # B. Ground Unit (Class Check)
        # Mapping common role names to IDs if needed
        role_map = {
            "infantry": "line_infantry",
            "tank": "battle_tank",
            "titan": "war_titan",
            "marines": "assault_marines"
        }
        class_id = role_map.get(role, role)
        
        if class_id in self.ground_classes:
            return self._generate_ground_regiment(faction_traits, class_id)
            
        # C. Fallback (Legacy)
        return self._generate_legacy_unit(faction_traits, role)

    def _generate_ship(self, faction_traits: List[str], hull_id: str) -> Dict[str, Any]:
        hull = self.hulls[hull_id]
        
        # 1. Design Ship
        design = self.ship_designer.create_design(hull, f"{hull.name} Class")
        
        # 2. Apply Traits to Final Stats
        # Convert design.stats to something apply_traits_to_stats likes?
        # design.stats has {hp, evasion, armor, speed, damage, etc.}
        
        active_traits = [self.trait_system.get_trait(t) for t in faction_traits if self.trait_system.get_trait(t)]
        final_stats = self.trait_system.apply_traits_to_stats(design.stats, active_traits)
        
        # 3. Apply Synergies
        synergies = self.trait_system.check_synergies(faction_traits)
        for stat, val in synergies.items():
            if stat in final_stats:
                final_stats[stat] *= (1.0 + val)
        
        return {
            "name": design.name,
            "role": hull_id,
            "stats": final_stats,
            "components": design.to_dict()["components"],
            "type": "ship"
        }

    def _generate_ground_regiment(self, faction_traits: List[str], class_id: str) -> Dict[str, Any]:
        unit_class = self.ground_classes[class_id]
        
        # 1. Base Stats
        stats = unit_class.stats.to_dict()
        
        # 2. Apply Traits
        # Note: GroundStats has specific keys (melee_attack) that core_traits might not catch yet.
        # But core_traits has 'hp', 'damage', 'morale'.
        active_traits = [self.trait_system.get_trait(t) for t in faction_traits if self.trait_system.get_trait(t)]
        
        # We need a custom apply because GroundStats structure implies different keys?
        # Actually our Trait system keys are loose strings.
        # If trait has "melee_attack": 0.1, it works if stats has "melee_attack".
        
        final_stats = self.trait_system.apply_traits_to_stats(stats, active_traits)
        
        return {
            "name": unit_class.name,
            "role": class_id,
            "stats": final_stats,
            "type": "regiment",
            "entity_count": unit_class.stats.entity_count
        }

    def _generate_legacy_unit(self, faction_traits: List[str], role: str) -> Dict[str, Any]:
        """Legacy fallback."""
        base_stats = self._get_base_template(role)
        active_traits = [self.trait_system.get_trait(t) for t in faction_traits if self.trait_system.get_trait(t)]
        final_stats_dict = self.trait_system.apply_traits_to_stats(base_stats, active_traits)
        estats = ExpandedStats.from_dict(final_stats_dict)
        return {
            "name": f"{role.capitalize()} Unit",
            "stats": estats.to_dict(),
            "role": role,
            "type": "legacy"
        }

    def _get_base_template(self, role: str) -> Dict[str, float]:
        """Hardcoded base templates for now."""
        if role == "infantry":
            return {"hp": 10.0, "damage": 2.0, "armor": 0.0, "speed": 6.0, "cost": 100.0}
        elif role == "tank":
            return {"hp": 50.0, "damage": 12.0, "armor": 5.0, "speed": 8.0, "cost": 300.0}
        elif role == "titan":
            return {"hp": 500.0, "damage": 100.0, "armor": 20.0, "speed": 12.0, "cost": 2000.0}
        else:
            return {"hp": 5.0, "damage": 1.0, "cost": 50.0}

    def _generate_description(self, traits: List[Trait], ethics: List[str] = None, civics: List[str] = None) -> str:
        desc = "A faction defined by: "
        desc += ", ".join([t.name for t in traits])
        
        if ethics:
            desc += f". Ethics: {', '.join(ethics)}"
        if civics:
            desc += f". Civics: {', '.join(civics)}"
            
        return desc + "."
