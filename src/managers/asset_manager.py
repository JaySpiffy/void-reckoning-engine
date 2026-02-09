
import random
from typing import Optional, List, Any, TYPE_CHECKING
from src.utils.profiler import profile_method
from src.utils.profiler import profile_method
import src.core.constants as constants
from src.core.constants import BUILD_TIME_DIVISOR, MAX_BUILD_TIME
from src.models.unit import Unit
from src.models.fleet import Fleet
from src.models.army import ArmyGroup

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.models.planet import Planet
    from src.core.interfaces import IEngine

class AssetManager:
    """
    Manages the lifecycle of game assets: Fleets, Armies, and Planet Ownership.
    Operates on the CampaignEngine state.
    """
    def __init__(self, engine: 'IEngine') -> None:
        self.engine = engine
        self.fleet_counters = {}
        self.army_counters = {}
        self.fleet_counters = {}
        self.army_counters = {}

    def __getstate__(self):
        """Exclude engine from pickling."""
        state = self.__dict__.copy()
        if 'engine' in state: del state['engine']
        return state

    def __setstate__(self, state):
        """Restore state."""
        self.__dict__.update(state)
        self.engine = None # Re-injected by SnapshotManager


    def register_fleet(self, fleet: 'Fleet') -> None:
        """Adds fleet to master list and faction index."""
        self.engine.add_fleet(fleet)

    def unregister_fleet(self, fleet: 'Fleet') -> None:
        """Removes fleet from master list and faction index."""
        self.engine.remove_fleet(fleet)

    def create_fleet(self, faction: str, location: Any, units: Optional[List[Unit]] = None, fid: Optional[str] = None) -> Fleet:
        if units is None: units = []
        if fid is None:
            if faction not in self.fleet_counters: self.fleet_counters[faction] = 0
            self.fleet_counters[faction] += 1
            fid = f"{faction} Fleet {self.fleet_counters[faction]}"
        
        f = Fleet(fid, faction, location)
        for u in units:
            f.add_unit(u)
        
        self.register_fleet(f)
        
        # [FIX] Register with Faction
        f_mgr = self.engine.get_faction(faction)
        if f_mgr and hasattr(f_mgr, 'fleets'):
            f_mgr.fleets.append(f)
            
        return f

    def create_army(self, faction: str, location: Any, units: Optional[List[Unit]] = None, aid: Optional[str] = None) -> ArmyGroup:
        # location can be Planet or GraphNode
        if units is None: units = []
        if aid is None:
            if faction not in self.army_counters: self.army_counters[faction] = 0
            self.army_counters[faction] += 1
            aid = f"{faction} Army {self.army_counters[faction]}"
        
        target_node = location
        if hasattr(location, 'provinces') and location.provinces:
             # Default to Capital if not specified
             target_node = next((n for n in location.provinces if n.type == "Capital"), None)
             if not target_node: target_node = location.provinces[0]
             
        a = ArmyGroup(aid, faction, units, target_node)
        
        # [FIX] Add to Node armies (Physical Location)
        if hasattr(target_node, 'armies'):
            target_node.armies.append(a)
        elif hasattr(location, 'armies'):
             # Fallback to Planet if Node has no army list (e.g. abstract planet)
             location.armies.append(a)
        else:
             print(f"Warning: Location {location} has no 'armies' list.")
             
        # [FIX] Also add to Planet armies (Abstract Container) for ease of lookup
        if target_node != location and hasattr(location, 'armies'):
            location.armies.append(a)

        # [FIX] Register with Faction
        f_mgr = self.engine.get_faction(faction)
        if f_mgr and hasattr(f_mgr, 'armies'):
            f_mgr.armies.append(a)
             
        return a

    def calculate_build_time(self, bp: Any) -> int:
        cost = getattr(bp, 'requisition_cost', 100)
        turns = max(1, int(cost / BUILD_TIME_DIVISOR))
        return min(turns, MAX_BUILD_TIME)

    @profile_method
    def update_planet_ownership(self, planet: Any, new_owner: str) -> None:
        """Updates planet owner and maintains faction indices."""
        old_owner = planet.owner
        
        # 1. Update Repository Index (Central State)
        # Needs to handle both adding to new owner and removing from old owner
        self.engine.galaxy_manager.update_planet_ownership(planet, old_owner or "Neutral", new_owner)
        
        # 2. Update Object
        planet.owner = new_owner
        
        # 3. CONQUEST LOGIC: Clear old infrastructure projects
        planet.construction_queue = [] 
        
        # Optionally destroy faction-specific buildings
        remaining_buildings = []
        for b_name in planet.buildings:
             if b_name in constants.get_building_database():
                 b_faction = constants.get_building_database()[b_name].get("faction", "All")
                 if b_faction == "All" or new_owner == b_faction or new_owner.startswith(b_faction):
                     remaining_buildings.append(b_name)
                 else:
                     if random.random() < 0.5:
                         remaining_buildings.append(b_name)
        
        planet.buildings = remaining_buildings

        # 4. Update Index: Add to new owner (Handled by single call above? No, update_ownership handles both removal and addition)
        # However, we called it prematurely above with 'new_owner' while planet.owner was still 'old_owner'?
        # PlanetRepository.update_ownership doesn't check planet.owner attribute, it trusts the args.
        # But wait, looking at my implementation of update_ownership:
        # It removes from old_owner bucket and adds to new_owner bucket.
        # So we only need to call it ONCE.
        
        # In step 1, I called it. So step 4 is redundant.
        # But let's verify if I should call it AFTER mutation to be safe?
        # Actually proper order:
        # Move index logic to AFTER mutation or BEFORE? 
        # PlanetRepository doesn't care about the object state for the index manipulation, it trusts the string args.
        # So calling it once is enough.
        
        # Let's clean up:
        # 1. I replaced the first call.
        # 2. I need to remove this second call.
        pass
        
        # 5. INITIALIZE INFRASTRUCTURE: Only for new colonies (Neutral -> Faction)
        if old_owner == "Neutral" and new_owner != "Neutral":
             self._initialize_planetary_infrastructure(planet)
        
        # 5. Log to Faction Reporter
        if old_owner and old_owner != "Neutral":
            self.engine.faction_reporter.log_event(old_owner, "territory", f"Lost control of planet {planet.name} to {new_owner}", {"planet": planet.name, "captor": new_owner})
        if new_owner != "Neutral":
            self.engine.faction_reporter.log_event(new_owner, "territory", f"Captured planet {planet.name} from {old_owner}", {"planet": planet.name, "previous_owner": old_owner})
            
            # [LEARNING] Update Target Outcome
            f_mgr = self.engine.get_faction(new_owner)
            if f_mgr and hasattr(f_mgr, 'learning_history'):
                for entry in reversed(f_mgr.learning_history.get('target_outcomes', [])):
                    if entry['target_name'] == planet.name and not entry['success']:
                        entry['captured_turn'] = self.engine.turn_counter
                        entry['success'] = True
                        break

        # 6. Telemetry: Conquest Gain
        if self.engine.telemetry and new_owner != "Neutral":
            conquest_value = planet.generate_resources().get("req", 0)
            self.engine.telemetry.metrics.record_resource_gain(
                new_owner,
                float(conquest_value),
                category="Conquest",
                source_planet=planet.name
            )

    def _initialize_planetary_infrastructure(self, planet: Any) -> None:
        """Synthesizes starting infrastructure (Capitals/Cities) for a newly colonized planet."""
        if not hasattr(planet, 'provinces') or not planet.provinces:
            # For abstract planets, just add a basic capital if empty
            if not planet.buildings:
                capital_id = "Planetary Capital"
                if capital_id in constants.get_building_database():
                     planet.buildings.append(capital_id)
            return

        for node in planet.provinces:
            target_building = None
            if node.type == "Capital":
                target_building = "Planetary Capital"
            elif node.type == "ProvinceCapital":
                target_building = "Province City"

            if target_building and target_building in constants.get_building_database():
                if target_building not in node.buildings:
                    node.buildings.append(target_building)

    @profile_method
    def prune_empty_armies(self) -> int:
        """Phase 36: Removes 0-strength armies from all locations to prevent Ghost Army explosion."""
        count = 0
        for p in self.engine.all_planets:
            # 1. Planet Level
            if hasattr(p, 'armies'):
                original_len = len(p.armies)
                p.armies = [ag for ag in p.armies if ag.units and not ag.is_destroyed]
                removed = original_len - len(p.armies)
                if removed > 0: count += removed
                
            # 2. Province Level
            if hasattr(p, 'provinces') and p.provinces:
                for node in p.provinces:
                    if hasattr(node, 'armies'):
                        node_len = len(node.armies)
                        node.armies = [ag for ag in node.armies if ag.units and not ag.is_destroyed]
                        removed = node_len - len(node.armies)
                        if removed > 0: count += removed
        return count
