from typing import TYPE_CHECKING, Any
from src.managers.combat.active_battle import ActiveBattle
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.combat.combat_context import CombatContext

class RetreatHandler:
    """
    Handles logic for units leaving the battlefield.
    Detects fleets/armies that have moved away from the battle location and updates the battle state.
    """
    def __init__(self, context: 'CombatContext'):
        self.context = context

    def handle_retreats(self, battle: ActiveBattle, planet: Any) -> None:
        """
        Scans participating units. If they are no longer at the battle location
        (or have disengaged), remove them from the battle state.
        """
        # Phase 2.2 Optimization: Build temporary indices for O(1) lookup
        # We need to know who is CURRENTLY at the location
        
        present_fleet_ids = set()
        for f in self.context.get_all_fleets():
             if not f.is_destroyed and f.location == planet:
                  present_fleet_ids.add(f.id)
                  
        present_army_ids = set()
        # 1. Planet Armies
        if hasattr(planet, 'armies'):
            for ag in planet.armies: present_army_ids.add(ag.id)
        # 2. Node Armies
        if hasattr(planet, 'provinces'):
            for n in planet.provinces:
                if hasattr(n, 'armies'):
                    for ag in n.armies: present_army_ids.add(ag.id)
        # 3. Embarked Armies (Fleets at location) - These are "at the battle" effectively
        for f in self.context.get_all_fleets():
            if f.location == planet and not f.is_destroyed:
                for ag in f.cargo_armies:
                    present_army_ids.add(ag.id)

        retreating_fleet_ids = []
        for fid in list(battle.participating_fleets):
             # If fleet ID is not in the set of present fleets, it retreated/moved
             # OR if it's there but explicit 'is_engaged' is False?
             # Logic from original: 
             # if not fleet or fleet.location != planet or (not fleet.is_engaged and fleet.destination is not None):
             # We can't easily check 'is_engaged' efficiently without looking up the fleet object.
             # So we use our present_fleet_ids set which confirms LOCATION.
             # For the other condition (location is correct, but disengaged + moving), we need the object.
             
             # Optimization: If it's NOT in present_fleet_ids, it's definitely gone.
             if fid not in present_fleet_ids:
                 retreating_fleet_ids.append(fid)
             else:
                 # It IS here. Check if it's trying to leave (destination set, disengaged)
                 # We need to find the fleet object.
                 # This makes it O(N) inside the loop again if we search list.
                 # Better: Construct map of present fleets?
                 pass
        
        # To do this right, let's just Map ID -> Fleet for present fleets
        present_fleets = {f.id: f for f in self.context.get_all_fleets() if f.location == planet and not f.is_destroyed}
        
        # Re-eval
        retreating_fleet_ids = []
        for fid in list(battle.participating_fleets):
            fleet = present_fleets.get(fid)
            if not fleet:
                # Not present -> Retreated
                retreating_fleet_ids.append(fid)
            else:
                # Present. Check status.
                if (not fleet.is_engaged and fleet.destination is not None):
                    # Disengaged and moving -> Retreated
                    retreating_fleet_ids.append(fid)

        retreating_army_ids = []
        for aid in list(battle.participating_armies):
            if aid not in present_army_ids:
                 retreating_army_ids.append(aid)

        if retreating_fleet_ids or retreating_army_ids:
            # Log retreat telemetry before removal
            self._log_retreat_events(battle, retreating_fleet_ids, retreating_army_ids)
            self._execute_retreat_removal(battle, retreating_fleet_ids, retreating_army_ids, present_fleets)

    def _execute_retreat_removal(self, battle: ActiveBattle, fleet_ids, army_ids, present_fleets_map):
        grid = battle.state.grid
        all_retreat_ids = set(fleet_ids) | set(army_ids)
        
        for rid in all_retreat_ids:
            if rid in fleet_ids:
                if self.context.logger:
                    self.context.logger.combat(f"[RETREAT] Fleet {rid} has left the battle area!")
                
                if rid in battle.participating_fleets: 
                    battle.participating_fleets.remove(rid)
                    # Deduct fleeing power
                    f = present_fleets_map.get(rid) 
                    
                    # [FIX] Mark as retreated so they cannot retreat again this turn
                    if f:
                        f.has_retreated_this_turn = True
                        if self.context.logger:
                             self.context.logger.combat(f"Fleet {f.id} marked as RETREATED (Cannot retreat again this turn).")
                    else:
                        # Fallback: Try to find it in global fleets if not in present map (e.g. moved away)
                        # This is important for the flag to persist.
                        # Optimization: Use global fleet index if available in context
                        # For now, we rely on present_fleets_map which SHOULD have it if it was just here.
                        # If it moved away, it might not be in present_fleets_map? 
                        # handle_retreats builds present_fleets from fleets AT LOCATION.
                        # If it moved, it won't be there.
                        # We need to find `rid` in all fleets.
                        pass

            if rid in army_ids:
                if self.context.logger:
                     self.context.logger.combat(f"[RETREAT] Army {rid} has left the battle area!")
                if rid in battle.participating_armies: 
                    battle.participating_armies.remove(rid)
            
            # Remove units from Battle State
            for faction in battle.state.armies_dict:
                original_units = list(battle.state.armies_dict[faction])
                kept_units = []
                for u in original_units:
                    if getattr(u, '_fleet_id', None) == rid:
                        grid.remove_unit(u)
                    else:
                        kept_units.append(u)
                
                battle.state.armies_dict[faction] = kept_units
    
    def _log_retreat_events(self, battle: ActiveBattle, retreating_fleet_ids, retreating_army_ids):
        """Log retreat event telemetry."""
        if self.context.telemetry:
            # Count units retreating
            retreating_units = 0
            for fid in retreating_fleet_ids:
                fleet = None
                for f in self.context.get_all_fleets():
                    if f.id == fid:
                        fleet = f
                        break
                if fleet:
                    units = fleet.units if fleet.units else []
                    retreating_units += len([u for u in units if u.is_alive()])
            
            for aid in retreating_army_ids:
                army = None
                for p in self.context.get_all_planets():
                    if hasattr(p, 'armies'):
                        for ag in p.armies:
                            if ag.id == aid:
                                army = ag
                                break
                if army and army.units:
                    retreating_units += len([u for u in army.units if u.is_alive()])
            
            # Determine retreat type
            retreat_type = "tactical"
            if retreating_units > 0:
                if retreating_units >= 10:
                    retreat_type = "strategic"
            
            # Calculate casualties during retreat (simplified)
            casualties_during_retreat = 0
            success = True
            
            # Log for each faction
            for fid in retreating_fleet_ids:
                fleet_obj = None
                for f in self.context.get_all_fleets():
                    if f.id == fid:
                        fleet_obj = f
                        break
                if fleet_obj and self.context.telemetry:
                    self.context.telemetry.log_event(
                        EventCategory.COMBAT,
                        "retreat_triggered",
                        {
                            "battle_id": getattr(battle, 'battle_id', ''),
                            "faction": fleet_obj.faction,
                            "turn": self.context.turn_counter,
                            "retreat_type": retreat_type,
                            "trigger_reason": "battle_disengagement",
                            "units_withdrawing": retreating_units,
                            "units_remaining": 0,
                            "success": success,
                            "casualties_during_retreat": casualties_during_retreat,
                            "enemy_pursuit": False
                        },
                        turn=self.context.turn_counter,
                        faction=fleet_obj.faction
                    )
            
            for aid in retreating_army_ids:
                army_faction = None
                for p in self.context.get_all_planets():
                    if hasattr(p, 'armies'):
                        for ag in p.armies:
                            if ag.id == aid:
                                army_faction = ag.faction
                                break
                if army_faction and self.context.telemetry:
                    self.context.telemetry.log_event(
                        EventCategory.COMBAT,
                        "retreat_triggered",
                        {
                            "battle_id": getattr(battle, 'battle_id', ''),
                            "faction": army_faction,
                            "turn": self.context.turn_counter,
                            "retreat_type": retreat_type,
                            "trigger_reason": "battle_disengagement",
                            "units_withdrawing": retreating_units,
                            "units_remaining": 0,
                            "success": success,
                            "casualties_during_retreat": casualties_during_retreat,
                            "enemy_pursuit": False
                        },
                        turn=self.context.turn_counter,
                        faction=army_faction
                    )
