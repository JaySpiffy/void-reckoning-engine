import os
import json
from typing import Dict, Any, Callable, Optional, List

class PayloadRegistry:
    """Registry for Ability Logic Payloads (Standard Stat Version)"""
    
    MOBILITY = "mobility"
    CONTROL = "control"
    DAMAGE = "damage"
    UTILITY = "utility"
    EXOTIC = "exotic"
    
    _instance = None
    
    def __init__(self):
        self._payloads: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._register_base_payloads()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_payload(self, ability_type: str, category: str, 
                          execute_fn: Callable, universe: str = "generic"):
        """Register a new logic payload for a specific universe"""
        if universe not in self._payloads:
            self._payloads[universe] = {}
            
        self._payloads[universe][ability_type] = {
            "category": category,
            "execute_fn": execute_fn
        }

    def execute_payload(self, ability_type: str, source: Any, 
                        target: Optional[Any] = None, 
                        context: Optional[Dict[str, Any]] = None,
                        universe: str = "generic") -> Dict[str, Any]:
        """Execute a payload by type and universe using Unit objects."""
        context = context or {}
        lookup_universes = [universe, "generic"] if universe != "generic" else ["generic"]
        
        for u in lookup_universes:
            if u in self._payloads and ability_type in self._payloads[u]:
                payload = self._payloads[u][ability_type]
                return payload["execute_fn"](source, target, context)
                
        return {
            "effect_type": "none",
            "magnitude": 0,
            "description": f"Payload not found: {ability_type}"
        }

    def _register_base_payloads(self):
        for u in ["generic", "void_reckoning"]:
            # Standard
            self.register_payload("tractor_beam", self.CONTROL, execute_tractor_beam, universe=u)
            self.register_payload("emp", self.CONTROL, execute_emp_blast, universe=u)
            self.register_payload("phase_jump", self.MOBILITY, execute_phase_jump, universe=u)
            self.register_payload("antimatter_torpedo", self.DAMAGE, execute_antimatter_torpedo, universe=u)
            self.register_payload("shield_harmonics", self.UTILITY, execute_shield_harmonics, universe=u)
            
            # Exotic (User Requested)
            self.register_payload("acidic_burn", self.DAMAGE, execute_acidic_burn, universe=u)
            self.register_payload("black_hole", self.CONTROL, execute_black_hole, universe=u)
            self.register_payload("logic_virus", self.CONTROL, execute_logic_virus, universe=u)
            self.register_payload("gravimetric_anchor", self.CONTROL, execute_gravimetric_anchor, universe=u)
            
            # Phase 5: Expanded Arsenal (Ability Versions)
            self.register_payload("ion_pulse", self.CONTROL, execute_ion_pulse, universe=u)
            self.register_payload("tesla_arc", self.DAMAGE, execute_tesla_arc, universe=u)
            self.register_payload("melta_blast", self.DAMAGE, execute_melta_blast, universe=u)
            self.register_payload("nanite_swarm", self.EXOTIC, execute_nanite_swarm, universe=u)

# --- Execution Functions (Stat-Based) ---

def execute_tractor_beam(source, target, context):
    """Refactored Tractor Beam using Ship/Unit weight heuristic."""
    if not target: return {"effect_type": "none"}
    source_power = getattr(source, 'hp', 100) / 10.0
    target_resist = getattr(target, 'hp', 100) / 20.0
    pull_force = source_power / (target_resist + 1)
    mobility_reduction = min(pull_force / 5.0, 0.9)
    return {
        "effect_type": "mobility_debuff",
        "magnitude": mobility_reduction,
        "description": f"Tractor Beam: {mobility_reduction*100:.0f}% speed reduction"
    }

def execute_emp_blast(source, target, context):
    """Refactored EMP Blast."""
    if not target: return {"effect_type": "none"}
    stun_chance = 0.5
    return {
        "effect_type": "stun",
        "chance": stun_chance,
        "description": f"EMP: {stun_chance*100:.0f}% stun chance"
    }

def execute_phase_jump(source, target, context):
    """Refactored Phase Jump."""
    jump_dist = 50.0 
    return {
        "effect_type": "teleport",
        "distance": jump_dist,
        "description": f"Phase Jump: {jump_dist} units"
    }

def execute_antimatter_torpedo(source, target, context):
    """Refactored Antimatter Torpedo."""
    if not target: return {"effect_type": "none"}
    damage = 100.0
    return {
        "effect_type": "damage",
        "magnitude": damage,
        "description": f"Antimatter Torpedo: {damage} damage"
    }

def execute_shield_harmonics(source, target, context):
    """Refactored Shield Harmonics."""
    regen = 20.0
    return {
        "effect_type": "buff",
        "type": "shield_regen",
        "magnitude": regen,
        "description": f"Shield Harmonics: +{regen} regen"
    }

# --- NEW Exotic Payloads ---

def execute_acidic_burn(source, target, context):
    """Corrosive effect: Armor reduction over time."""
    if not target: return {"effect_type": "none"}
    armor_shred = 5.0
    return {
        "effect_type": "armor_debuff",
        "magnitude": armor_shred,
        "duration": 3,
        "description": f"Acidic Burn: -{armor_shred} Armor for 3 turns"
    }

def execute_black_hole(source, target, context):
    """Black Hole/Vortex: Massive damage and immobilization."""
    if not target: return {"effect_type": "none"}
    vortex_dmg = 500.0
    return {
        "effect_type": "area_denial",
        "magnitude": vortex_dmg,
        "duration": 1,
        "description": "Vortex: Sub-space singularity detected! Massive damage imminent."
    }

def execute_logic_virus(source, target, context):
    """Cyber-warfare: Turns unit against its faction for 1 turn."""
    if not target: return {"effect_type": "none"}
    return {
        "effect_type": "corruption",
        "duration": 1,
        "description": "Logic Virus: Targeting heuristics compromised. Faction alignment scrambled!"
    }

def execute_gravimetric_anchor(source, target, context):
    """Gravimetric Projector: Immobilization and evasion penalty."""
    if not target: return {"effect_type": "none"}
    return {
        "effect_type": "immobilize",
        "duration": 2,
        "description": "Gravimetric Anchor: Local gravity localized. Movement impossible."
    }

def execute_ion_pulse(source, target, context):
    """Ion Pulse: Disables shields and systems."""
    if not target: return {"effect_type": "none"}
    
    # 50% chance to stun
    stun_chk = 0.5
    
    # Shield damage
    shield_dmg = 50.0
    
    return {
        "effect_type": "ion_damage",
        "shield_damage": shield_dmg,
        "stun_chance": stun_chk,
        "description": f"Ion Pulse: {shield_dmg} shield dmg + {stun_chk*100:.0f}% Stun"
    }

def execute_tesla_arc(source, target, context):
    """Tesla Arc: Chain lightning."""
    dmg = 30.0
    return {
        "effect_type": "chain_damage",
        "damage": dmg,
        "chains": 2,
        "description": f"Tesla Arc: {dmg} damage (Chains to 2 targets)"
    }

def execute_melta_blast(source, target, context):
    """Melta Blast: High anti-armor damage."""
    dmg = 80.0
    ap = -4
    return {
        "effect_type": "armor_piercing_damage",
        "damage": dmg,
        "ap": ap,
        "description": "Melta Blast: Thermal annihilation."
    }

def execute_nanite_swarm(source, target, context):
    """Nanite Swarm: Consumes target."""
    return {
        "effect_type": "consumption",
        "duration": 5,
        "description": "Nanite Swarm: Target is being consumed."
    }
