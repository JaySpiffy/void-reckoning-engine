import hashlib
import random
from typing import Optional, TYPE_CHECKING, Any
from src.reporting.telemetry import EventCategory
from src.models.army import ArmyGroup
from src.core.constants import COLONIZATION_REQ_COST, BUILDING_DATABASE
from src.core import balance as bal
from src.utils.profiler import profile_method

if TYPE_CHECKING:
    from src.combat.combat_context import CombatContext
    from src.models.fleet import Fleet

class InvasionManager:
    """
    Handles ground invasion logistics:
    - Embarking/Disembarking armies
    - Automated invasion processing
    - Unopposed conquest (Colonization)
    - Post-conquest cleanup (Tech Lock)
    """
    def __init__(self, context: 'CombatContext'):
        self.context = context
        self._manager_rng = random.Random()

    @profile_method
    def process_invasions(self, faction_filter: Optional[str] = None) -> None:
        """Checks fleets for invasion orders or auto-drops."""
            
        for fleet in self.context.fleets:
            if not fleet.is_destroyed:
                if faction_filter and fleet.faction != faction_filter:
                    continue
                
                if not fleet.cargo_armies:
                    continue
                
                loc_owner = "Neutral"
                if hasattr(fleet.location, 'owner'):
                    loc_owner = fleet.location.owner
                
                # Check for enemies on ground
                enemies_on_ground = False
                if hasattr(fleet.location, 'armies'):
                    if any(a.faction != fleet.faction for a in fleet.location.armies):
                        enemies_on_ground = True

                if (loc_owner != fleet.faction) or (loc_owner == fleet.faction and enemies_on_ground):
                    # PHASE 10: Invasion Prep (1-turn delay)
                    # Hostile landings require the fleet to remain in orbit for 1 turn
                    if getattr(fleet, 'arrived_this_turn', False):
                        if self.context.logger:
                            self.context.logger.combat(f"[PREP] {fleet.id} preparing invasion of {fleet.location.name} (Ready next turn).")
                        continue

                    # PHASE 17: Orbital Blockade Check
                    if self._check_orbital_blockade(fleet, fleet.location):
                        continue
                        
                    self.land_armies(fleet, fleet.location)

    def _check_orbital_blockade(self, fleet: 'Fleet', location: Any) -> bool:
        """Checks if hostile space units are in orbit preventing landings."""
        if not hasattr(self.context, 'fleets'):
            return False
            
        loc_name = getattr(location, 'name', 'node')
        
        # PHASE 17: If there is an active space battle here, it's contested by default!
        if hasattr(self.context, 'battle_manager'):
            if location in self.context.battle_manager.active_battles:
                # If there's an active battle, check if it's already resolved in favor of the current faction
                # or if it's just starting.
                battle = self.context.battle_manager.active_battles[location]
                if not battle.is_finished:
                    return True
            
        for other_fleet in self.context.fleets:
            if not other_fleet or other_fleet.is_destroyed or other_fleet.id == fleet.id:
                continue
                
            loc_match = (other_fleet.location == location)
            if not loc_match and hasattr(other_fleet.location, 'id') and hasattr(location, 'id'):
                loc_match = (other_fleet.location.id == location.id)
                
            if loc_match:
                is_hostile = False
                if hasattr(self.context, '_is_hostile_target'):
                    is_hostile = self.context._is_hostile_target(fleet.faction, other_fleet.faction)
                elif hasattr(location, 'owner') and location.owner == other_fleet.faction:
                    is_hostile = (fleet.faction != other_fleet.faction)
                
                if is_hostile:
                    has_combat_ships = any(u.is_ship() for u in other_fleet.units)
                    if has_combat_ships:
                        if self.context.logger:
                             pass # self.context.logger.combat(f"[BLOCKADE] {fleet.id} blocked by {other_fleet.id} at {loc_name}!")
                        return True
        return False

    def land_armies(self, fleet: 'Fleet', planet: Any) -> None:
        """Wrapper for AI invasion logic."""
        if not hasattr(planet, 'provinces') or not planet.provinces:
            return

        # 1. Check if we have cargo
        if fleet.cargo_armies:
                lzs = [n for n in planet.provinces if n.type == "LandingZone"]
                if not lzs: lzs = [planet.provinces[0]]
                
                # Seed Manager RNG for this specific landing (determinism check)
                self._seed_manager_rng(planet)
                
                # Land ALL armies in one turn (Fast Deployment)
                while fleet.cargo_armies:
                    target = self._manager_rng.choice(lzs)
                    self.disembark_army(fleet, target)
                
        # 2. Check for legacy loose units (Migration Phase)
        ground_units = [u for u in fleet.units if not u.is_ship()]
        if ground_units:
                lz = planet.provinces[0]
                fleet.units = [u for u in fleet.units if u.is_ship()]
                
                ag_id = f"Force {fleet.id} Ground"
                ag = ArmyGroup(ag_id, fleet.faction, ground_units, lz)
                planet.armies.append(ag)
                lz.armies.append(ag)
                if self.context.logger:
                    self.context.logger.combat(f"[RAPID] RAPID DEPLOYMENT: {len(ground_units)} units from {fleet.id} landed at {lz.name}")

    def embark_army(self, fleet: 'Fleet', army_group: 'ArmyGroup') -> bool:
        """Army boards a Fleet (Transport)."""
        if army_group.state != "IDLE": return False
        
        if hasattr(army_group.location, 'type') and army_group.location.type not in ["Capital", "LandingZone", "Spaceport"]:
                return False
                
        army_size = army_group.get_total_size()
        if fleet.used_capacity + army_size > fleet.transport_capacity:
            if self.context.logger:
                self.context.logger.combat(f"[LOGISTICS] FAIL: {army_group.id} cannot board {fleet.id} (Capacity {fleet.used_capacity}/{fleet.transport_capacity} vs Need {army_size})")
            return False

        if army_group.location and hasattr(army_group.location, 'armies'):
            if army_group in army_group.location.armies:
                army_group.location.armies.remove(army_group)
            
        army_group.state = "EMBARKED"
        army_group.transport_fleet = fleet
        fleet.cargo_armies.append(army_group)
        fleet.invalidate_used_capacity()
        if self.context.logger:
            self.context.logger.combat(f"[EMBARK] {army_group.id} boarded {fleet.id} (Load: {fleet.used_capacity}/{fleet.transport_capacity})")
        
        if self.context.telemetry:
            self.context.telemetry.log_event(
                EventCategory.MOVEMENT,
                "embarkation",
                {"army_id": army_group.id, "fleet_id": fleet.id},
                turn=self.context.turn_counter,
                faction=fleet.faction
            )
        return True

    def disembark_army(self, fleet: 'Fleet', target_node: Any) -> None:
        """Army unloads from Fleet to Planet Node."""
        if not fleet.cargo_armies: return
        
        planet = fleet.location
        if hasattr(planet, 'provinces') and target_node not in planet.provinces:
            if self.context.logger:
                self.context.logger.error(f"Error: Invalid drop zone {target_node.name} for planet {planet.name}")
            return
            
        ag = fleet.cargo_armies.pop(0)
        fleet.invalidate_used_capacity()
        # MERGE LOGIC: Check for existing friendly army at LZ
        target_army = None
        if hasattr(target_node, 'armies'):
            for existing_ag in target_node.armies:
                if existing_ag.faction == ag.faction and existing_ag != ag and not existing_ag.is_destroyed:
                    target_army = existing_ag
                    break
                    
        if target_army:
                # Merge AG into Target
                if self.context.logger:
                    self.context.logger.combat(f"[INVASION] {ag.id} LANDED and MERGED with {target_army.id} on {target_node.name}")
                target_army.merge_with(ag)
                
                # ARMY SIZE CAP & REBALANCE
                max_size = 50
                if hasattr(self.context, 'game_config'):
                    max_size = self.context.game_config.get("units", {}).get("max_land_army_size", 50)
                    
                if target_army.get_total_size() > max_size:
                    capped_army = target_army.split_off(max_size)
                    if capped_army:
                        # Register new army
                        if hasattr(planet, 'armies'): planet.armies.append(capped_army)
                        if hasattr(target_node, 'armies'): target_node.armies.append(capped_army)
                        if self.context.logger:
                            self.context.logger.combat(f"[LOGISTICS] Army {target_army.id} exceeded cap ({max_size}). Rebalanced into {capped_army.id}.")
        else:
            # Standalone Landing
            ag.state = "IDLE"
            ag.transport_fleet = None
            ag.location = target_node
            
            target_node.armies.append(ag)
            
            if hasattr(planet, 'armies') and ag not in planet.armies:
                    planet.armies.append(ag)
    
            if self.context.logger:
                self.context.logger.combat(f"[INVASION] {ag.id} landed at {target_node.name} on {planet.name} from {fleet.id}")
            
            if self.context.telemetry:
                self.context.telemetry.log_event(
                    EventCategory.COMBAT,
                    "ground_invasion",
                    {"army_id": ag.id, "planet": planet.name, "node": target_node.name},
                    turn=self.context.turn_counter,
                    faction=ag.faction
                )

    def handle_conquest(self, location: Any, conqueror: str, method: str = "conquest") -> None:
        """
        Generic handler for planet ownership transfer.
        Triggers: Ownership flip, Tech Lock (Scorched Earth), Siege Clear, Logging.
        """
        old_owner = getattr(location, 'owner', 'Neutral')
        loc_name = getattr(location, 'name', str(location))
        
        # 1. Update Ownership
        if hasattr(self.context, 'update_planet_ownership'):
            self.context.update_planet_ownership(location, conqueror)
        elif hasattr(location, 'owner'):
            location.owner = conqueror # Fallback
            
        # 2. Clear Siege Status
        if hasattr(location, 'is_sieged'):
            location.is_sieged = False
            
        # 3. Enforce Tech Lock (Scorched Earth)
        self.enforce_tech_lock(location, conqueror)
        
        # 4. Logging & Telemetry
        if self.context.logger:
            self.context.logger.campaign(f"[CONQUEST] {conqueror} has captured {loc_name} from {old_owner} via {method}!")
            
        if self.context.telemetry:
            self.context.telemetry.log_event(
                EventCategory.CAMPAIGN,
                "planet_annexed",
                {"planet": loc_name, "by": conqueror, "from": old_owner, "method": method},
                turn=self.context.turn_counter,
                faction=conqueror
            )
            
        # 5. Diplomacy Trigger (Grudge)
        if getattr(self.context, 'diplomacy', None) and old_owner != "Neutral":
             self.context.diplomacy.add_grudge(old_owner, conqueror, 35, f"Lost {loc_name} to {method}")

    def handle_unopposed_conquest(self, location, occupier):
        """Phase 21: Handles peaceful annexation of neutral worlds."""
        loc_owner = location.owner if hasattr(location, 'owner') else "Neutral"
        
        # Check if we should allow conquest (either Neutral or at War with owner)
        is_hostile = False
        if loc_owner != "Neutral" and hasattr(self.context, 'diplomacy'):
            if self.context.diplomacy.get_treaty(occupier, loc_owner) == "War":
                is_hostile = True

        if (loc_owner == "Neutral" or is_hostile) and hasattr(location, 'owner'):
            loc_name = getattr(location, 'name', 'Unknown Node')
            
            f_mgr = self.context.get_faction(occupier)
            # Phase 102: Config-driven Colonization Cost
            col_cost = self.context.game_config.get("economy", {}).get("colonization_cost", COLONIZATION_REQ_COST)
            
            # Occupation is free if hostile; Colonization costs requisition
            cost = col_cost
            method = "colonization"
            if is_hostile:
                # Phase 10: Consolidation Cost
                cost = bal.PACIFICATION_COST
                method = "occupation"
                
            # [FIX] Relaxed Colonization Check (Prevent Stagnation)
            # Match OffensiveStrategy logic: Allow colonization if Req >= 200, even if cost is higher (debt).
            has_funds = False
            if f_mgr:
                if method == "colonization":
                    has_funds = f_mgr.requisition >= 200
                else:
                    has_funds = f_mgr.requisition >= cost
            
            if has_funds:
                if cost > 0:
                    f_mgr.deduct_cost(cost)
                
                # Delegate to generic handler
                self.handle_conquest(location, occupier, method=method)
                
                # Record Spend (only if colonization)
                if cost > 0 and self.context.telemetry:
                    self.context.telemetry.record_resource_spend(
                        occupier,
                        cost,
                        category="Colonization",
                        source_planet=loc_name
                    )
            elif cost > 0:
                loc_name = location.name if hasattr(location, 'name') else str(location)
                if self.context.logger:
                    self.context.logger.campaign(f"[EXPANSION] {occupier} presence at {loc_name} but cannot afford colonization cost ({cost} Req, Has {f_mgr.requisition}).")

    def enforce_tech_lock(self, planet: Any, new_owner: str) -> None:
        """
        Destroys buildings that do not belong to the new owner (Scorched Earth).
        """
        destroyed_count = 0
        surviving_buildings = []
        for b_id in planet.buildings:
            b_data = BUILDING_DATABASE.get(b_id, {})
            b_faction = b_data.get("faction", "Neutral")
            if b_faction == new_owner or b_faction == "Neutral":
                surviving_buildings.append(b_id)
            else:
                destroyed_count += 1
        planet.buildings = surviving_buildings
        
        if hasattr(planet, 'provinces'):
            for node in planet.provinces:
                # ... (scanning nodes)
                surviving_node_b = []
                for b_id in node.buildings:
                    b_data = BUILDING_DATABASE.get(b_id, {})
                    b_faction = b_data.get("faction", "Neutral")
                    if b_faction == new_owner or b_faction == "Neutral":
                        surviving_node_b.append(b_id)
                    else:
                        destroyed_count += 1
                node.buildings = surviving_node_b
                
        if destroyed_count > 0:
            if self.context.logger:
                self.context.logger.campaign(f"[SCORCHED EARTH] {new_owner} incompatible upgrade purge: {destroyed_count} structures destroyed on {planet.name}.")

    def _seed_manager_rng(self, location: Any):
        """Seeds the manager RNG based on context and location."""
        base_seed = getattr(self.context, 'game_config', {}).get("seed")
        if base_seed is not None:
             loc_str = getattr(location, 'name', str(location))
             loc_seed_int = int(hashlib.md5(loc_str.encode()).hexdigest(), 16) & 0xFFFFFFFF
             
             # Use safe turn counter
             turn = self.context.turn_counter if hasattr(self.context, 'turn_counter') else 0
             manager_seed = base_seed + turn + loc_seed_int
             self._manager_rng.seed(manager_seed + 20) # Significant offset
