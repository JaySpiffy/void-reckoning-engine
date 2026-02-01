from typing import Any
from src.commands.base_command import Command

class AttackCommand(Command):
    """
    Command to initiate an attack.
    - If target is a Fleet: Intercept and engage (Set AGGRESSIVE stance).
    - If target is a Planet: Move to and Invade (Land Armies).
    """
    
    def __init__(self, fleet: Any, target: Any, engine: Any):
        self.fleet = fleet
        self.target = target
        self.engine = engine
        
        # State for Undo
        self._executed = False
        self._prev_directive = None
        self._prev_destination = None
        self._prev_route = None

    def can_execute(self) -> bool:
        if not self.fleet or getattr(self.fleet, 'is_destroyed', True):
            return False
            
        # Can't attack if already engaged (unless we allow changing targets in melee?)
        # For now, simplistic check
        return True

    def execute(self) -> Any:
        # Capture State
        self._prev_directive = getattr(self.fleet, 'tactical_directive', "HOLD_GROUND")
        self._prev_destination = self.fleet.destination
        self._prev_route = list(self.fleet.route) if self.fleet.route else []
        
        # Determine Target Type
        # Duck typing or class check
        is_planet = hasattr(self.target, 'provinces') or hasattr(self.target, 'building_slots') # Planet-ish
        is_fleet = hasattr(self.target, 'units') and not is_planet # Fleet-ish
        
        if is_planet:
            if self.fleet.location == self.target:
                # We are at the planet -> Initiate Invasion
                # Ensure we have armies
                if hasattr(self.fleet, 'cargo_armies') and self.fleet.cargo_armies:
                     if hasattr(self.engine, 'battle_manager'):
                         self.engine.battle_manager.invasion_manager.land_armies(self.fleet, self.target)
                         self._executed = "INVASION"
                         return True
                else:
                    print(f"Fleet {self.fleet.id} has no armies to invade {self.target.name}.")
                    return False
            else:
                # Move to planet
                self.fleet.move_to(self.target, force=True, engine=self.engine)
                self._executed = "MOVE_TO_INVADE"
                return True
                
        elif is_fleet:
            # Set Aggressive Stance
            self.fleet.tactical_directive = "CHARGE"
            
            # Move to target location
            target_loc = getattr(self.target, 'location', None)
            if target_loc:
                self.fleet.move_to(target_loc, force=True, engine=self.engine)
                self._executed = "INTERCEPT"
                return True
                
        return False

    def undo(self) -> None:
        if not self._executed:
            return
            
        if self._executed == "INVASION":
            # Hard to undo invasion once armies landed (merged).
            # We would need to re-embark them.
            # For Phase 7, we might accept that Invasion is non-undoable easily without complex state snapshots.
            print("Undo not fully supported for Invasion action yet.")
            pass
            
        elif self._executed in ["INTERCEPT", "MOVE_TO_INVADE"]:
            # Revert Movement
            self.fleet.destination = self._prev_destination
            self.fleet.route = self._prev_route
            # Revert Stance
            self.fleet.tactical_directive = self._prev_directive
