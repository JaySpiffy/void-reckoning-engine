from typing import List, Dict, Optional, Any
from src.models.unit import Unit, Component
import src.core.balance as bal

class Starbase(Unit):
    def __init__(self, name, faction, system, tier=1, blueprint_id=None, hp=2500, shield=1000, 
                 damage=50, armor=20, abilities=None, under_construction=False, design_data=None):
        """
        Represents a static Space Station / Starbase.
        Inherits from Unit to participate in combat as a 'super-heavy' entity.
        """
        self.tier = tier
        self.design_data = design_data
        
        # Override name if design provided
        if design_data:
            name = design_data.get("name", name)
            
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
            cost=design_data.get("cost", 1000 * tier) if design_data else 1000 * tier,
            shield=shield,
            movement_points=0, # Static
            blueprint_id=blueprint_id or f"starbase_{faction.lower()}_t{tier}",
            unit_class="Starbase",
            domain="space",
            tier=tier
        )
        
        self.system = system
        self.modules = [] 
        self.hangar_capacity = 0
        self.docked_fleets = []
        self.naval_slots = 0 
        self.unit_queue = [] 
        
        self.turns_left = 5 if under_construction and tier == 1 else 0
        self.is_under_construction = under_construction
        self.is_destroyed = False
        
        # Override upkeep based on design if available
        self.upkeep = int(self.cost * 0.25)
        
        # Starbase Properties
        self.ftl_inhibitor = False 
        self.sensor_range = 2 
        
        # Initialize Logic
        self.recalc_tier_stats(reset_hp=(hp == 2500)) 
        self.generate_components()
        
    def recalc_tier_stats(self, reset_hp=True):
        """Updates stats based on current Tier."""
        # Multipliers per Tier
        # Tier 1: Baseline
        # Tier 5: Fortress
        mult = self.tier
        
        self.base_hp = 3000 * mult
        if reset_hp:
            self.current_hp = self.base_hp
            
        self.shield_max = 2000 * mult
        if reset_hp:
            self.shield_current = self.shield_max
        self.base_damage = 75 * mult
        self.armor = 25 + (mult * 10)
        
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
        self.components = []
        
        # 1. Hull & Shields (Always present)
        self.components.append(Component(f"Starbase Core T{self.tier}", self.base_hp, "Hull"))
        if self.shield_max > 0:
            self.components.append(Component(f"Void Shield Generator T{self.tier}", self.shield_max, "Shield"))

        # 2. AI-Designed Faction Weapons
        if self.design_data and "components" in self.design_data:
            print(f"  > [STATION] Applying AI Design for {self.faction} ({self.name})")
            for comp_data in self.design_data["components"]:
                # Wrap dict into Component object
                name = comp_data.get("name", "Unknown System")
                ctype = comp_data.get("type", "Weapon")
                stats = comp_data.get("stats", {})
                w_stats = comp_data.get("weapon_stats")
                
                # Check for Hangar type
                if ctype == "Hangar":
                    self.hangar_capacity += 5 # Bonus capacity from hangar modules
                
                self.components.append(Component(name, stats.get("hp", 100), ctype, weapon_stats=w_stats))
                
        else:
            # 3. Fallback: Generic High-Power Batteries
            macro_stats = {
                "Str": 6 + self.tier, 
                "AP": -1 - (self.tier // 2), 
                "D": 2, 
                "Attacks": 6 * self.tier, 
                "Range": 60 
            }
            self.components.append(Component(f"Macro-Cannon Grid T{self.tier}", 100, "Weapon", weapon_stats=macro_stats))
            
            if self.tier >= 2:
                pd_stats = {"Str": 4, "AP": 0, "D": 1, "Attacks": 10, "Range": 20}
                self.components.append(Component(f"Point Defense Grid T{self.tier}", 50, "Weapon", weapon_stats=pd_stats))

            if self.tier >= 3:
                h_stats = {"Str": 5, "AP": -2, "D": 3, "Attacks": 2 * self.tier, "Range": 150}
                self.components.append(Component(f"Heavy Hangar Bay T{self.tier}", 100, "Hangar", weapon_stats=h_stats))
            
            if self.tier >= 4:
                 is_t5 = (self.tier == 5)
                 l_name = "Exterminatus Array" if is_t5 else "Orbital Lance"
                 l_str = 15 if is_t5 else 10
                 l_ap = -6 if is_t5 else -4
                 l_stats = {"Str": l_str, "AP": l_ap, "D": d6_avg() * (2 if is_t5 else 1), "Attacks": self.tier - 2, "Range": 120}
                 self.components.append(Component(l_name, 50, "Weapon", weapon_stats=l_stats))

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
