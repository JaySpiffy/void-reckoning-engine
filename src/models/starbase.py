from typing import List, Dict, Optional, Any
from src.models.unit import Unit, Component
import src.core.balance as bal

class Starbase(Unit):
    def __init__(self, name, faction, system, tier=1, blueprint_id=None, hp=2500, shield=1000, 
                 damage=50, armor=20, abilities=None, under_construction=False):
        """
        Represents a static Space Station / Starbase.
        Inherits from Unit to participate in combat as a 'super-heavy' entity.
        
        Args:
            name (str): Display Name (e.g. "Alpha Base")
            faction (str): Owner Faction
            system (StarSystem): Parent System
            tier (int): Upgrade Level (1-5)
        """
        self.tier = tier
        # print(f"DEBUG: Starbase.__init__ sets self.tier = {self.tier}")
        ma = 60 # High Accuracy
        md = 10 # 0 Evasion (Static)
        
        super().__init__(
            name=name,
            ma=ma,
            md=md,
            hp=hp,
            armor=armor,
            damage=damage,
            abilities=abilities or {"Turrets": 5 + (tier * 2), "Tags": ["Starbase", "Static", "Massive"]},
            faction=faction,
            cost=1000 * tier,
            shield=shield,
            movement_points=0, # Static
            blueprint_id=blueprint_id or f"starbase_{faction.lower()}_t{tier}",
            unit_class="Starbase",
            domain="space",
            tier=tier
        )
        
        self.system = system
        self.modules = [] # List of Strings (Module IDs) or Objects
        self.hangar_capacity = 0
        self.docked_fleets = []
        self.naval_slots = 0 # Shipyard capacity (Phase 14 Improvement)
        self.unit_queue = [] # List of {'bp': UnitBlueprint, 'turns_left': int, 'type': 'fleet'} (Phase 16)
        
        # [PHASE 18] Starbase Construction
        self.turns_left = 5 if under_construction and tier == 1 else 0
        self.is_under_construction = under_construction
        self.is_destroyed = False
        
        # [PHASE 14] Starbase Economics
        # Override unit upkeep with a heavier stationary cost
        # T1: 250, T2: 500, T3: 1000, T4: 1500, T5: 2500
        self.upkeep = int(self.cost * 0.25)
        
        # Starbase Properties
        self.ftl_inhibitor = False # If True, blocks enemy movement
        self.sensor_range = 2 # System-wide usually
        
        # Initialize Logic
        self.recalc_tier_stats(reset_hp=(hp == 2500)) # Only reset if using default constructor val
        # self.generate_components() is called by Unit.__init__
        
    def recalc_tier_stats(self, reset_hp=True):
        """Updates stats based on current Tier."""
        # Multipliers per Tier
        # Tier 1: Baseline
        # Tier 5: Fortress
        mult = self.tier
        
        self.base_hp = 2000 * mult
        if reset_hp:
            self.current_hp = self.base_hp
            
        self.shield_max = 1000 * mult
        if reset_hp:
            self.shield_current = self.shield_max
        self.base_damage = 50 * mult
        self.armor = 20 + (mult * 5)
        
        self.hangar_capacity = (mult - 1) * 2 # T1=0, T2=2, T3=4...
        
        # Modules slots = Tier + 2?
        self.module_slots = self.tier + 2
        
        # Enable Inhibitor at Tier 2+
        self.ftl_inhibitor = (self.tier >= 2)
        
        # Enable Shipyard at Tier 1+ (Phase 26: Deep Space Shipyards)
        # User requested Deep Space Stations be able to build ships immediately.
        if self.tier == 1:
             self.naval_slots = 2 # Basic functional shipyard
        elif self.tier == 2:
             self.naval_slots = 4
        elif self.tier >= 3:
             self.naval_slots = (self.tier - 2) * 5 + 5 # T3=10, T4=15, T5=20
        else:
             self.naval_slots = 0
            
        # Update Upkeep (scales with firepower and shipyard)
        self.upkeep = int(self.cost * 0.25) + (self.naval_slots * 10)
        
        self.invalidate_strength_cache()

    def process_queue(self, engine):
        """Advances production of ships within the Starbase (Phase 16)."""
        if not self.unit_queue: return
        
        # Shipyard throughput (Number of ships that can progress in parallel)
        max_parallel = max(1, self.naval_slots // 2) if self.naval_slots > 0 else 1
        
        # High Wealth Throughput Boost (Phase 16)
        if self.faction in engine.factions:
            f_mgr = engine.factions[self.faction]
            if f_mgr.requisition > 100000:
                # [FIX] Massive Boost for "Infinite Money" scenario
                # Allow parallel construction of 10 ships if wealthy
                max_parallel = max(max_parallel * 4, 10)

        slots_used = 0
        completed_indices = []
        
        for i, job in enumerate(self.unit_queue):
            if slots_used < max_parallel:
                job["turns_left"] -= 1
                slots_used += 1
                if job["turns_left"] <= 0:
                    completed_indices.append(i)
        
        for i in completed_indices:
            self._finalize_naval_job(self.unit_queue[i], engine)
            
        for i in sorted(completed_indices, reverse=True):
            self.unit_queue.pop(i)

    def _finalize_naval_job(self, job, engine):
        """Places the finished ship into a fleet at the Starbase location."""
        bp = job["bp"]
        print(f"  > [STATION] NAVAL PRODUCTION COMPLETE: {bp.name} at {self.name}")

        # Starbases usually exist at the Primary Node of a system
        primary_node = self.system.get_primary_node()
        if not primary_node: return

        target_fleet = None
        target_id = job.get("target_fleet_id")

        if target_id:
            for f in engine.fleets:
                if f.id == target_id and not f.is_destroyed:
                    target_fleet = f
                    break

        if not target_fleet:
            # Look for friendly fleet in orbit
            for f in engine.fleets:
                if f.faction == self.faction and f.location == primary_node and not f.destination:
                    if len(f.units) < engine.max_fleet_size:
                        target_fleet = f
                        break

        if not target_fleet:
            target_fleet = engine.create_fleet(self.faction, primary_node, [], fid=target_id)
            
        target_fleet.add_unit(bp)
        
    def upgrade(self):
        """Starts the upgrade process to the next tier."""
        if self.tier < 5 and not self.is_under_construction:
            self.is_under_construction = True
            # Build time scales with target tier
            target_tier = self.tier + 1
            self.turns_left = 3 + (target_tier * 2) # T2=7, T3=9, T4=11, T5=13
            print(f"  > [STATION] Upgrade started for {self.name} to Tier {target_tier} ({self.turns_left} turns)")

    def finalize_construction(self):
        """Applied when construction/upgrade finishes."""
        if self.is_under_construction:
            self.is_under_construction = False
            self.turns_left = 0
            self.tier += 1
            self.name = f"{self.name.split(' (Tier')[0]} (Tier {self.tier})"
            self.recalc_tier_stats()
            self.generate_components()
            print(f"  > [STATION] CONSTRUCTION COMPLETE: {self.name}")
            
    def generate_components(self):
        """Generates components based on tier. Overrides Unit.generate_components."""
        # print(f"DEBUG: Starbase.generate_components called. self.tier = {self.tier}")
        self.components = []
        
        # 1. Hull
        self.components.append(Component(f"Starbase Core T{self.tier}", self.base_hp, "Hull"))
        
        # 2. Shields
        if self.shield_max > 0:
            self.components.append(Component(f"Void Shield Generator T{self.tier}", self.shield_max, "Shield"))
            
        # 3. Weapons (Abstracted batteries)
        # Add 'Macro Batteries' component
        w_stats = {
            "Str": 6 + self.tier, # Escaling Strength
            "AP": -1 - (self.tier // 2), 
            "D": 2, 
            "Attacks": 4 * self.tier, 
            "Range": 60 # Long range
        }
        self.components.append(Component(f"Defense Batteries T{self.tier}", 100, "Weapon", weapon_stats=w_stats))
        
        if self.tier >= 3:
             # Add Lance/Torpedo
             l_stats = {"Str": 10, "AP": -4, "D": d6_avg(), "Attacks": self.tier, "Range": 100}
             self.components.append(Component("Orbital Lance", 50, "Weapon", weapon_stats=l_stats))

    def is_ship(self):
        return True # Treated as a ship for combat resolution steps (shields, etc) but static
        
    def to_dict(self) -> Dict[str, Any]:
        """Serializes starbase state for Save V2."""
        data = super().to_dict()
        data["extra_data"].update({
            "unit_type": "Starbase",
            "tier": self.tier,
            "system_name": self.system.name if hasattr(self.system, "name") else str(self.system),
            "is_under_construction": self.is_under_construction,
            "turns_left": self.turns_left,
            "sensors": self.sensor_range,
            "ftl_inhibitor": self.ftl_inhibitor
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], system: Any) -> 'Starbase':
        """Hydrates a Starbase from a dictionary (Save V2)."""
        ed = data.get("extra_data", {})
        stats = data.get("stats", {})
        
        starbase = cls(
            name=data["name"],
            faction=data["faction"],
            system=system,
            tier=ed.get("tier", 1),
            blueprint_id=ed.get("blueprint_id"),
            hp=stats.get("hp", 2500),
            shield=stats.get("shield", 1000),
            damage=stats.get("damage", 50),
            armor=stats.get("armor", 20),
            abilities=data.get("abilities"),
            under_construction=ed.get("is_under_construction", False)
        )
        starbase.current_hp = stats.get("current_hp", starbase.current_hp)
        starbase.shield_current = stats.get("shield_current", starbase.shield_current)
        starbase.turns_left = ed.get("turns_left", 0)
        starbase.sensor_range = ed.get("sensors", 2)
        starbase.ftl_inhibitor = ed.get("ftl_inhibitor", False)
        
        return starbase
        
    def regenerate_shields(self):
        """Starbases have fast shield regen."""
        if self.shield_max <= 0: return 0
        if self.shield_current >= self.shield_max: return 0
        
        regen = int(self.shield_max * 0.20) # 20% per round
        missing = self.shield_max - self.shield_current
        actual = min(missing, regen)
        self.shield_current += actual
        return actual

    @property
    def power(self):
        return self.strength

def d6_avg():
    return 3.5
