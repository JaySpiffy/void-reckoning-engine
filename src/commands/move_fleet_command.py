from typing import Optional, List, Any
from src.commands.base_command import Command
# from src.models.fleet import Fleet
# from src.models.planet import Planet

class MoveFleetCommand(Command):
    """
    Command to order a fleet to move to a target destination.
    Encapsulates pathfinding initiation and route setting.
    """
    
    def __init__(self, fleet: Any, target: Any, engine: Any, force: bool = False):
        self.fleet = fleet
        self.target = target
        self.engine = engine
        self.force = force
        
        # State for Undo
        self._previous_destination = None
        self._previous_route = None
        self._executed = False

    def can_execute(self) -> bool:
        if not self.fleet or getattr(self.fleet, 'is_destroyed', True):
            return False
            
        # If engaged, can only move if forced (retreat)
        if getattr(self.fleet, 'is_engaged', False) and not self.force:
            return False
            
        return True

    def execute(self) -> Any:
        # Capture state
        self._previous_destination = self.fleet.destination
        self._previous_route = list(self.fleet.route) if self.fleet.route else []
        
        # Perform action
        result = self.fleet.move_to(self.target, force=self.force, engine=self.engine)
        self._executed = True
        return result

    def undo(self) -> None:
        if not self._executed:
            return
            
        # Revert
        self.fleet.destination = self._previous_destination
        self.fleet.route = self._previous_route
        
        # Assuming we haven't advanced time yet, this restores the "Order" status.
        # If pathfinding involved side effects (cache), those are harmless.
