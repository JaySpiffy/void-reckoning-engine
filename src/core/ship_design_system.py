
from typing import Dict, List, Any, Optional

class ShipComponent:
    def __init__(self, id: str, name: str, slot_type: str, stats: Dict[str, float], 
                 cost: float, power: float, tech_level: int = 0):
        self.id = id
        self.name = name
        self.slot_type = slot_type # S, M, L, X, H, P, G, REACTOR, THRUSTER, FTL, SENSOR, COMPUTER
        self.stats = stats # damage, range, accuracy, shield, armor, evasion
        self.cost = cost
        self.power = power # Negative for usage, Positive for generation
        self.tech_level = tech_level
    
    def to_dict(self):
        return self.__dict__

class ShipHull:
    def __init__(self, id: str, name: str, size: int, base_stats: Dict[str, float], 
                 slots: Dict[str, int], sections: List[str] = None):
        self.id = id
        self.name = name
        self.size = size # Corvette=1, Destroyer=2, etc.
        self.base_stats = base_stats # hp, evasion, armor, speed
        self.slots = slots # {"S": 3, "M": 1, "REACTOR": 1, ...}
        self.sections = sections or ["core"] # Simplified sections for now

    def to_dict(self):
        return self.__dict__

class ShipDesign:
    def __init__(self, name: str, hull: ShipHull, components: Dict[str, List[ShipComponent]]):
        self.name = name
        self.hull = hull
        self.components = components # Keyed by slot type? Or flat list mapped to slots?
                                     # Mapping: {"S": [Laser, Laser, Railgun], "M": [Missile]}
        self.stats = self._calculate_stats()
        self.valid = self._validate_design()

    def _calculate_stats(self) -> Dict[str, float]:
        stats = self.hull.base_stats.copy()
        current_power = 0
        cost = 0
        
        for slot_type, component_list in self.components.items():
            for comp in component_list:
                cost += comp.cost
                current_power += comp.power
                for stat, val in comp.stats.items():
                    stats[stat] = stats.get(stat, 0.0) + val
                    
        stats["cost"] = cost
        stats["power_balance"] = current_power
        return stats

    def _validate_design(self) -> bool:
        # Check Slot Counts
        for slot_type, component_list in self.components.items():
            max_slots = self.hull.slots.get(slot_type, 0)
            if len(component_list) > max_slots:
                return False
        
        # Check Power
        if self.stats.get("power_balance", 0) < 0:
            return False
            
        return True

    def to_dict(self):
        return {
            "name": self.name,
            "hull": self.hull.id,
            "components": {k: [c.id for c in v] for k,v in self.components.items()},
            "stats": self.stats,
            "valid": self.valid
        }

class ShipDesigner:
    """
    Auto-generates ship designs.
    """
    def __init__(self, component_registry: Dict[str, ShipComponent]):
        self.registry = component_registry # All available components

    def create_design(self, hull: ShipHull, name: str, faction: Any = None, tech_level: int = 1) -> ShipDesign:
        """
        Creates a valid design for the hull using best available tech.
        Strategy: Fill core slots (Reactor/Thruster) first to ensure power/speed, then weapons/defense.
        Args:
            hull: The hull to design for.
            name: Design name.
            faction: Faction object (for tech unlocks).
            tech_level: Fallback general tech level.
        """
        design_components = {}
        
        # Determine Unlocked Techs
        unlocked_techs = set()
        if faction and hasattr(faction, 'unlocked_techs'):
            unlocked_techs = set(faction.unlocked_techs)
            
        # 1. Essential Components (Reactor, Thruster, FTL, Sensor, Computer)
        # Assuming Hull has slots for these specifically named
        essentials = ["REACTOR", "THRUSTER", "FTL", "SENSOR", "COMPUTER"]
        power_gen = 0
        power_usage = 0
        
        # Fill Essentials (Greedy: Best available)
        for slot in essentials:
            if slot in hull.slots:
                # Find best component
                comp = self._get_best_component(slot, tech_level, unlocked_techs)
                if comp:
                    design_components[slot] = [comp] * hull.slots[slot]
                    power_gen += comp.power if comp.power > 0 else 0
                    power_usage -= comp.power if comp.power < 0 else 0
        
        # 2. Weapons & Defense (S, M, L, X, H, P, G)
        weapon_slots = ["S", "M", "L", "X", "H", "P", "G"]
        
        # Simple Logic: Fill all slots with best available weapon/defense
        # TODO: Balance Shield/Armor based on Power
        
        for slot in weapon_slots:
            if slot in hull.slots:
                count = hull.slots[slot]
                comps_for_slot = []
                for _ in range(count):
                    # Check Power Budget
                    # This is complex. Simplified: Just pick best and see if it fails later?
                    # Better: Pick best weapon, assume standard power costs.
                    comp = self._get_best_component(slot, tech_level, unlocked_techs)
                    if comp:
                        comps_for_slot.append(comp)
                        power_usage -= comp.power if comp.power < 0 else 0
                design_components[slot] = comps_for_slot

        # 3. Check Power & Upgrade Reactor if needed (or downgrade weapons)
        # For now, just return what we have (Design validation will catch negative power)
        
        return ShipDesign(name, hull, design_components)

    def _get_best_component(self, slot_type: str, max_tech: int, unlocked_techs: set = None) -> Optional[ShipComponent]:
        candidates = []
        for c in self.registry.values():
            if c.slot_type != slot_type:
                continue
                
            # 1. Tech Level Hard Cap
            if c.tech_level > max_tech:
                continue
                
            # 2. Specific Tech Unlock Check
            # If we know the required tech (e.g. "Tech_Unlock_{ID}"), check it.
            # We assume the convention from ProceduralTechGenerator: `Tech_Unlock_{c.id}`
            # OR if the component is "Basic" (Tier 0/1) it might be auto-unlocked.
            
            if unlocked_techs is not None:
                # Check if this component requires a specific tech
                # Convention: We generated "Tech_Unlock_{c.id}"
                tech_key = f"Tech_Unlock_{c.id}"
                
                # Logic:
                # If c.tech_level <= 1: Always available (Basic Tech)
                # Else: Must have unlocked specific tech OR have "Tech_Unlock_ALL_TIER_X"?
                # For now, strict check:
                if c.tech_level > 1:
                     if tech_key not in unlocked_techs:
                         # Check strictness: what if it's a vanity weapon?
                         # If it's in the registry, we demand the tech.
                         continue
            
            candidates.append(c)
            
        if not candidates: return None
        # Sort by Tech Level Descending, then Cost
        candidates.sort(key=lambda x: (x.tech_level, x.cost), reverse=True)
        return candidates[0]
