from typing import Dict, Any, List, Optional
import random
from src.models.unit import Ship, Component
from src.core import balance as bal

class ShipDesignService:
    """
    Intelligent Designer for procedural ships.
    Dynamically generates ship blueprints based on available technology and strategic needs.
    """

    def __init__(self, ai_manager):
        self.ai = ai_manager
        self.engine = ai_manager.engine
        self._design_cache = {} # {(faction, hull_class, role): Design}

    def generate_design(self, faction: str, hull_class: str, role: str) -> Dict[str, Any]:
        """
        Generates a ship design for the given faction, hull size, and strategic role.
        Returns a dict that can be used to instantiate a Ship.
        """
        f_mgr = self.engine.factions[faction]
        techs = f_mgr.unlocked_techs
        best_components = self._select_best_components(faction, hull_class, role)
        
        name = self._generate_name(faction, hull_class, role)
        
        # Calculate Cost
        base_cost = 100 # TODO: Get from Hull
        stats = self._aggregate_stats(best_components)
        cost = base_cost + stats['cost']
        
        design = {
            "name": name,
            "class": hull_class,
            "role": role,
            "cost": cost,
            "components": best_components,
            "stats": stats
        }
        
        return design

    def _select_best_components(self, faction: str, hull_class: str, role: str) -> List[Dict[str, Any]]:
        """
        Selects optimal components based on role and unlocked tech.
        This includes weapons, shields, engines, etc.
        """
        components = []
        
        # 1. Hull - Assuming implicit for now, but could be a component
        
        # 2. Weapons
        # Opponent Adaptive Logic: define 'target_profile' (e.g. anti-shield)
        mandates = self.ai.turn_cache.get('mandates', {}).get(faction, {})
        
        target_trait = "General"
        # If any mandate is "Aggressive", stick to general high DPS
        # If mandate suggest "Tech Stealing" -> Ion Weapons?
        # Future: Check mandates to see if we need Anti-Shield or Anti-Armor
        
        if role == "Constructor":
            # Constructors have 0 weapons, only Engines and specialized support (Defense)
            # We can represent the constructor module as a high-cost component or just hull trait.
            slots = ["Engine", "Defense", "Engine"]
        else:
            slots = self._get_slots_for_hull(hull_class)
            
        for slot in slots:
            if slot == "Weapon":
                w = self._pick_weapon(faction, role)
                if w: components.append(w)
            elif slot == "Defense":
                d = self._pick_defense(faction, role)
                if d: components.append(d)
                
        return components

    def _get_slots_for_hull(self, hull_class: str) -> List[str]:
        # Simple configuration for now
        if hull_class == "Escort":
            return ["Weapon", "Defense", "Engine"]
        elif hull_class == "Cruiser":
            return ["Weapon", "Weapon", "Defense", "Defense", "Engine"]
        elif hull_class == "Battleship":
            return ["Weapon", "Weapon", "Weapon", "Defense", "Defense", "Defense", "Engine", "Engine"]
        return ["Weapon"]

    def _pick_weapon(self, faction: str, role: str) -> Dict[str, Any]:
        """
        Selects the best available weapon for the role from the faction's registry.
        Prioritizes procedural/invented weapons over stock defaults.
        """
        f_mgr = self.engine.factions[faction]
        candidates = []
        
        # 1. Gather Candidates from Faction Registry (Invented/Stolen)
        if hasattr(f_mgr, 'weapon_registry'):
            for w_id, stats in f_mgr.weapon_registry.items():
                candidates.append(stats)
                
        # 2. Add Base Candidates (Stock) - Only if unlocked (simplified check)
        # For now, we assume basic lasers/macros are always available or check techs
        # This is a placeholder for a proper Tech->Weapon map lookup
        defaults = [
             {"Name": "Macro-Cannon", "Range": 24, "S": 6, "AP": 1, "D": 2, "cost": 30},
             {"Name": "Lance Battery", "Range": 60, "S": 8, "AP": 3, "D": 4, "cost": 60},
             {"Name": "Plasma Battery", "Range": 24, "S": 7, "AP": 3, "D": 2, "cost": 50},
             {"Name": "Defense Lasers", "Range": 12, "S": 3, "AP": 0, "D": 1, "cost": 10}
        ]
        candidates.extend(defaults)
        
        # 3. Filter & Score
        best_weapon = None
        best_score = -1
        
        pref = getattr(f_mgr, 'design_preference', 'BALANCED')
        
        for w in candidates:
            # Check availability (e.g. if we strictly require tech, we'd filter here)
            # For now, we assume anything in weapon_registry is available.
            
            score = 0
            rng = w.get("Range", 24)
            dps = (w.get("S", 4) * w.get("D", 1)) # Very rough heuristic
            
            # Phase 8: Counter-Building Logic
            if pref == "ANTI_SHIELD":
                # Lances and Shield-breakers (S > 7 or AP >= 3)
                if w.get("AP", 0) >= 3 or w.get("S", 0) >= 8:
                    score += 20
            elif pref == "ANTI_ARMOR":
                # High Damage, high strength (D > 2)
                if w.get("D", 1) >= 3:
                    score += 20
            elif pref == "AREA_EFFECT":
                # Rapid fire or Blast (Simulated by high S or specific tags)
                if "Blast" in w.get("Tags", []) or "Rapid" in w.get("Tags", []):
                    score += 20
            
            if role == "Sniper":
                if rng >= 60: score += dps * 2.0
                elif rng >= 45: score += dps * 1.0
                else: score = -999 # Reject short range
            elif role == "Brawler":
                if rng <= 30: score += dps * 2.0
                else: score += dps * 0.5 
            else: # General
                score += dps
                
            if score > best_score:
                best_score = score
                best_weapon = w
                
        if best_weapon:
            # Return in component format
            return {
                "name": best_weapon.get("Name", "Unknown Weapon"),
                "type": "Weapon", 
                "stats": {
                    "range": best_weapon.get("Range", 24),
                    "damage": best_weapon.get("D", 1) * 3, # Scale to component stats
                    "cost": best_weapon.get("cost", 50)
                },
                "weapon_stats": best_weapon # Store full stats for Unit instantiation
            }
            
        return {"name": "Macro-Cannon", "type": "Weapon", "stats": {"range": 24, "damage": 20, "cost": 30}}

    def _pick_defense(self, faction: str, role: str) -> Dict[str, Any]:
        # Placeholder: Check for shield tech
        f_mgr = self.engine.factions[faction]
        if "Void Shields" in f_mgr.unlocked_techs or "Tech_None 3" in f_mgr.unlocked_techs: # Legacy Check
            return {"name": "Void Shield Generator", "type": "Defense", "stats": {"shield": 200, "cost": 100}}

        # Correct ID Check (header-based)
        expected_id = f"Tech_{faction.replace(' ', '_')}_Planetary Shielding"
        if expected_id in f_mgr.unlocked_techs:
             return {"name": "Void Shield Generator", "type": "Shield", "stats": {"shield": 200, "cost": 100}}
             
        return {"name": "Reinforced Plating", "type": "Defense", "stats": {"hp": 50, "cost": 20}}

    def _generate_name(self, faction: str, hull: str, role: str) -> str:
        # e.g. "Hegemony Mk4 Brawler"
        # Add flavor based on faction
        prefix = "Mk1"
        if faction == "Hegemony": prefix = "Invictus"
        elif faction == "Hierarchs": prefix = "Dynastic"
        elif faction == "Marauders": prefix = "Krump"
        
        if role == "Constructor":
            return f"{prefix} Construction Platform"
            
        return f"{prefix}-{hull} ({role})"

    def _aggregate_stats(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats = {"cost": 0, "damage": 0, "hp": 0, "shield": 0}
        for c in components:
            s = c.get('stats', {})
            stats['cost'] += s.get('cost', 0)
            stats['damage'] += s.get('damage', 0)
            stats['shield'] += s.get('shield', 0)
        return stats
