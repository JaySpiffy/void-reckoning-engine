from typing import Any
from src.commands.base_command import Command
# from src.models.faction import Faction
# from src.models.planet import Planet

class BuildCommand(Command):
    """
    Command to queue construction of a building on a planet.
    """
    
    def __init__(self, faction: Any, planet: Any, building_id: str, cost: int, engine: Any):
        self.faction = faction
        self.planet = planet
        self.building_id = building_id
        self.cost = cost
        self.engine = engine
        
        self._executed = False
        self._queued_item_ref = None # To identify item in queue for undo

    def can_execute(self) -> bool:
        if self.planet.owner != self.faction.name:
            return False
        if not self.faction.can_afford(self.cost):
            return False
        # Slot check is complex (nodes vs planet), assuming caller triggered valid command
        return True

    def execute(self) -> bool:
        # Note: faction.construct_building usually returns True if queued successfully
        if self.faction.construct_building(self.planet, self.building_id):
            self.faction.deduct_cost(self.cost)
            self.faction.track_construction(self.cost)
            self._executed = True
            
            # Capture the last item in queue as the one we just added
            # This is slightly risky if concurrency exists, but we are single threaded here usually
            if self.planet.construction_queue:
                self._queued_item_ref = self.planet.construction_queue[-1]
            return True
        return False

    def undo(self) -> None:
        if not self._executed:
            return
            
        # Refund
        self.faction.requisition += self.cost
        
        # Remove from Queue
        # We try to remove the specific item instance
        if self._queued_item_ref and self._queued_item_ref in self.planet.construction_queue:
            self.planet.construction_queue.remove(self._queued_item_ref)
        else:
            # Fallback: remove last matching building_id
            for i in reversed(range(len(self.planet.construction_queue))):
                if self.planet.construction_queue[i].get("id") == self.building_id:
                    self.planet.construction_queue.pop(i)
                    break
