from typing import Dict, Any, List, Optional
import random
from src.models.unit import Ship, Component
import os
import json
from src.core import balance as bal
from src.core import ship_sections as sections
from src.utils.game_logging import GameLogger, LogCategory

class ShipDesignService:
    """
    Intelligent Designer for modular procedural ships.
    Generates blueprints using Bow, Core, and Stern sections inspired by Stellaris/Thrawn.
    """

    def __init__(self, ai_manager):
        self.ai = ai_manager
        self.engine = ai_manager.engine
        self.logger = GameLogger()
        self._design_cache = {} # {(faction, hull_class, role): Design}
        self.hull_registry = {} 
        self._load_hull_registry()

    def _load_hull_registry(self):
        try:
            path = os.path.join("data", "ships", "hulls.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    for h in data.get("hulls", []):
                        # Key by ID (lowercase, e.g. "corvette") AND Name (Title Case, e.g. "Corvette")
                        # RecruitmentService often uses Title Case "Cruiser"
                        self.hull_registry[h["id"]] = h
                        self.hull_registry[h["name"]] = h
            else:
                 self.logger.error("[ShipDesignService] hulls.json not found.")
        except Exception as e:
            self.logger.error(f"[ShipDesignService] Failed to load hulls: {e}")

    def get_available_hulls(self, faction_name: str) -> List[str]:
        """
        Returns a list of hull class names (e.g. ['Corvette', 'Destroyer']) available to the faction.
        """
        f_mgr = self.engine.get_faction(faction_name)
        if not f_mgr: return ["Corvette"] # Fallback

        available = []
        # We want to return NAMES because RecruitmentService uses 'Cruiser', 'Battleship' as keys.
        # So iterate distinct values in registry or just known types.
        
        # Iterate unique definitions (by looking at 'id' keys only to avoid dupes)
        seen_ids = set()
        for key, data in self.hull_registry.items():
            h_id = data["id"]
            if h_id in seen_ids: continue
            seen_ids.add(h_id)
            
            # Check Unlock
            h_name = data["name"]
            req_tech = data.get("unlock_tech")
            
            # 1. Check direct tech ID if specified in hulls.json (Legacy/Hardcoded)
            if req_tech and req_tech in f_mgr.unlocked_techs:
                available.append(h_name)
                continue
                
            # 2. Check name-based unlock via TechManager (handles faction-specific registry mapping)
            if hasattr(self.engine, 'tech_manager') and self.engine.tech_manager.is_unit_unlocked(faction_name, h_name, f_mgr.unlocked_techs):
                available.append(h_name)
                continue
                
            # 3. If no tech required, it's a starter hull (Tier 1)
            if not req_tech:
                available.append(h_name)
                
        # Sort by size to be nice?
        # Ensure at least one thing is returned
        if not available: return ["Corvette"]
        return available

    def generate_design(self, faction: str, hull_class: str, role: str) -> Dict[str, Any]:
        """
        Generates a ship design for the given faction, hull size, and strategic role.
        """
        best_components = self._select_best_components(faction, hull_class, role)
        name = self._generate_name(faction, hull_class, role)
        stats = self._aggregate_stats(best_components, hull_class)
        
        design = {
            "name": name,
            "class": hull_class,
            "role": role,
            "cost": 100 + stats['cost'],
            "components": best_components,
            "stats": stats
        }

        # Logging and Persistence
        self.logger.log(LogCategory.AI, f"Generated {hull_class} ({role}): {name} for {faction}")
        self._persist_design(design, faction)
        
        return design

    def _persist_design(self, design: Dict[str, Any], faction: str):
        """Saves the design to the active run's report directory for integrated inspection."""
        # Use the logger's log_dir which points to the active run (reports/runs/run_ID)
        # Fallback to local logs/designs only if logger isn't initialized with a path
        base_dir = self.logger.log_dir if hasattr(self.logger, 'log_dir') else os.path.join("logs", "designs")
        
        design_dir = os.path.join(base_dir, "designs", faction.replace(" ", "_"))
        if not os.path.exists(design_dir):
            os.makedirs(design_dir, exist_ok=True)
            
        filename = f"{design['name'].replace(' ', '_')}_{design['role']}.json"
        filepath = os.path.join(design_dir, filename)
        
        try:
            with open(filepath, "w") as f:
                json.dump(design, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to persist design {design['name']} to reporting system: {e}")

    def generate_starbase_design(self, faction: str, tier: int) -> Dict[str, Any]:
        """
        [NEW] Generates a specialized Starbase design for a faction.
        Uses faction-specific weapons from their registry.
        """
        f_mgr = self.engine.get_faction(faction)
        prefix = faction.split("_")[0]
        
        # Scaling Slots (Sync with Starbase.py)
        w_slots = int(20 * (1.25 ** (tier - 1)))
        d_slots = int(10 * (1.25 ** (tier - 1)))
        
        design = {
            "name": f"{prefix}-{tier} Fortress",
            "tier": tier,
            "components": [],
            "stats": {"cost": 0, "damage": 0, "shield": 0}
        }
        
        # Distribution: 40% Main, 40% PD, 20% Special (Hangar/Lance)
        main_count = max(1, int(w_slots * 0.4))
        pd_count = max(1, int(w_slots * 0.4))
        special_count = w_slots - main_count - pd_count
        
        # 1. Select Main Battery
        main_w = self._pick_weapon(faction, "Brawler", size="L") 
        if main_w:
            for i in range(main_count):
                comp = main_w.copy()
                comp["name"] = f"Heavy {comp['name']} {i+1}"
                comp["stats"]["attacks"] = max(4, comp["weapon_stats"].get("Attacks", 1) * 2 * tier)
                design["components"].append(comp)
            
        # 2. Select Point Defense
        pd_w = self._pick_weapon(faction, "General", size="P") 
        if pd_w:
            for i in range(pd_count):
                comp = pd_w.copy()
                comp["name"] = f"Integrated PD {comp['name']} {i+1}"
                comp["stats"]["attacks"] = 10 + (tier * 2)
                design["components"].append(comp)
            
        # 3. Add Special Systems (Hangar prioritized then Lance)
        h_count = special_count // 2 if tier >= 3 else 0
        l_count = special_count - h_count if tier >= 4 else 0
        
        for i in range(h_count):
            design["components"].append({
                "name": f"Heavy Hangar Bay {i+1} T{tier}",
                "type": "Hangar",
                "stats": {"range": 150, "damage": 15, "cost": 200, "hp": 100}
            })
            
        if l_count > 0:
            lance = self._pick_weapon(faction, "Sniper", size="L")
            if lance:
                for i in range(l_count):
                    comp = lance.copy()
                    comp["name"] = "Orbital Exterminatus" if tier == 5 else f"Heavy {comp['name']} {i+1}"
                    comp["stats"]["range"] = 120
                    design["components"].append(comp)
                    
        # 4. Defense Modules
        for i in range(d_slots):
             design["components"].append({
                 "name": f"Reinforced Composite T{tier}",
                 "type": "Defense",
                 "stats": {"hp": 500 * tier, "cost": 100 * tier}
             })
                
        # Aggregate Cost
        stats = self._aggregate_stats(design["components"])
        design["stats"] = stats
        design["cost"] = 5000 * tier + stats["cost"]
        
        return design

    def _select_best_components(self, faction: str, hull_class: str, role: str) -> List[Dict[str, Any]]:
        """
        Selects optimal components based on Sections and Slot types.
        """
        components = []
        
        if role == "Constructor":
            return [
                {"name": "Standard Engine", "type": "Engine", "stats": {"cost": 20}},
                {"name": "Reinforced Hull", "type": "Defense", "stats": {"hp": 100, "cost": 30}}
            ]

        # 1. Determine Sections for this Hull
        section_names = sections.get_sections_for_hull(hull_class)
        
        # 2. Map high-level Role to Section Roles (Simplified)
        # Role mapping for variety
        # Cruiser Sniper -> Bow: Artillery, Core: Artillery, Stern: Engine
        # Cruiser Carrier -> Bow: Carrier, Core: Hangar, Stern: Engine
        
        for pos in section_names:
            section_role = role # Default
            # Custom mapping for variety
            if pos == "Bow" and role == "General": section_role = "Artillery"
            elif pos == "Core" and role == "General": section_role = "Broadside"
            
            section_data = sections.select_section(hull_class, pos, section_role)
            slots = section_data["slots"]
            
            for slot_type in slots:
                if slot_type in ["S", "M", "L", "X"]:
                    w = self._pick_weapon(faction, role, size=slot_type)
                    if w: components.append(w)
                elif slot_type == "P":
                    pd = self._pick_weapon(faction, "General", size="P")
                    if pd: components.append(pd)
                elif slot_type == "G":
                    g = self._pick_weapon(faction, "General", size="G")
                    if g: components.append(g)
                elif slot_type == "H":
                    components.append({"name": "Hangar Bay", "type": "Hangar", "stats": {"cost": 100, "damage": 10}})
                elif slot_type == "D":
                    d = self._pick_defense(faction, role)
                    if d: components.append(d)
                elif slot_type == "E":
                    components.append({"name": "Standard Engine", "type": "Engine", "stats": {"cost": 20}})
                elif slot_type == "T":
                    t = self._pick_weapon(faction, role, size="T")
                    if t: components.append(t)
                elif slot_type == "I":
                    i = self._pick_weapon(faction, role, size="I")
                    if i: components.append(i)
                
        return components

    def _pick_weapon(self, faction: str, role: str, size: str = "M") -> Dict[str, Any]:
        """
        Selects the best available weapon for the role and slot size.
        """
        f_mgr = self.engine.factions[faction]
        candidates = []
        
        # 1. Gather Candidates from Faction Registry
        if hasattr(f_mgr, 'weapon_registry'):
            for w_id, stats in f_mgr.weapon_registry.items():
                candidates.append(stats)
                
        # 2. Add size-aware defaults
        defaults = [
             {"Name": "Light Laser", "Range": 15, "S": 3, "AP": 1, "D": 1, "cost": 10, "Size": "S"},
             {"Name": "Macro-Cannon", "Range": 24, "S": 6, "AP": 1, "D": 2, "cost": 30, "Size": "M"},
             {"Name": "Heavy Turbolaser", "Range": 45, "S": 9, "AP": 3, "D": 5, "cost": 80, "Size": "L"},
             {"Name": "Spinal Lance", "Range": 80, "S": 12, "AP": 5, "D": 15, "cost": 250, "Size": "X"},
             {"Name": "Point Defense", "Range": 10, "S": 2, "AP": 0, "D": 1, "cost": 5, "Size": "P", "Tags": ["PD"]},
             {"Name": "Torpedo Launcher", "Range": 60, "S": 8, "AP": 4, "D": 10, "cost": 100, "Size": "G", "Tags": ["Guided"]},
             {"Name": "Tractor Beam", "Range": 50, "S": 0, "AP": 0, "D": 0, "cost": 50, "Size": "T", "Tags": ["Utility"]},
             {"Name": "Interdiction Field", "Range": 200, "S": 0, "AP": 0, "D": 0, "cost": 200, "Size": "I", "Tags": ["Utility"]}
        ]
        candidates.extend(defaults)
        
        best_weapon = None
        best_score = -1
        
        for w in candidates:
            score = 0
            w_size = w.get("Size", "M")
            
            # Size matching is critical
            if w_size == size:
                score += 1000
            elif size in ["T", "I"]:
                score -= 10000 # Strict exclusion for utility slots
            elif size == "M" and w_size in ["S", "L"]: 
                score += 10 # Some cross-compatibility
            else: 
                score -= 50 # Penalize mismatch
            
            # Special Utility Matching
            if size in ["T", "I"] and "Utility" in w.get("Tags", []):
                score += 500
            
            rng = w.get("Range", 24)
            dps = (w.get("S", 4) * w.get("D", 1))
            
            # Role mapping
            if role == "Sniper" and rng >= 45: score += 20
            elif role == "Brawler" and rng <= 30: score += 20
            
            score += dps
            
            if score > best_score:
                best_score = score
                best_weapon = w
                
        if best_weapon:
            # Scale damage for internal balancing (component stats are higher than unit stats usually)
            mult = 2 if size in ["S", "P"] else 4
            if size == "L": mult = 6
            if size == "X": mult = 15
            
            return {
                "name": best_weapon.get("Name", "Weapon"),
                "type": "Weapon",
                "size": size,
                "stats": {
                    "range": best_weapon.get("Range", 24),
                    "damage": best_weapon.get("D", 1) * mult,
                    "cost": best_weapon.get("cost", 50)
                },
                "weapon_stats": best_weapon
            }
            
        return None

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

    def _aggregate_stats(self, components: List[Dict[str, Any]], hull_class: Optional[str] = None) -> Dict[str, Any]:
        base = bal.HULL_BASE_STATS.get(hull_class, {"hp": 0, "armor": 0, "cost": 0, "shield": 0}) if hull_class else {"hp": 0, "armor": 0, "cost": 0, "shield": 0}
        
        stats = {
            "cost": base.get("cost", 0), 
            "damage": 0, 
            "hp": base.get("hp", 0), 
            "armor": base.get("armor", 0),
            "shield": base.get("shield", 0)
        }
        for c in components:
            s = c.get('stats', {})
            stats['cost'] += s.get('cost', 0)
            stats['damage'] += s.get('damage', 0)
            stats['hp'] += s.get('hp', 0) # Component HP bonuses (e.g. Reinforced Plating)
            stats['shield'] += s.get('shield', 0)
        return stats
