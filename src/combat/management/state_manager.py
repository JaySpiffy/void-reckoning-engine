from typing import List, Dict, Set, Optional, Any, TYPE_CHECKING, Union
from src.managers.combat.active_battle import ActiveBattle

if TYPE_CHECKING:
    from src.models.fleet import Fleet
    from src.models.army_group import ArmyGroup
    from src.core.interfaces import IEngine

class BattleStateManager:
    """
    Extracted component for maintaining active battle states and presence indices.
    Manages O(1) lookups for fleets, armies, and factions at locations.
    """
    def __init__(self, context: Optional['IEngine'] = None) -> None:
        self.context = context
        self.active_battles: Dict[Any, ActiveBattle] = {} # Map Location -> ActiveBattle
        
        # Performance Indices
        self._fleets_by_location: Dict[Any, List['Fleet']] = {}
        self._armies_by_location: Dict[Any, List['ArmyGroup']] = {}
        self._fleet_index: Dict[str, 'Fleet'] = {}
        self._army_index: Dict[str, 'ArmyGroup'] = {}
        self._presence_index: Dict[tuple, bool] = {} # (faction, location) -> True
        self._location_factions: Dict[Any, Set[str]] = {} # location -> Set[faction]

    def update_indices(self):
        """Rebuilds location-based indices for fast lookup."""
        if not self.context:
            return

        self._fleets_by_location = {}
        self._fleet_index = {}
        for f in self.context.get_all_fleets():
            if not f.is_destroyed:
                loc = f.location
                if loc not in self._fleets_by_location: 
                    self._fleets_by_location[loc] = []
                self._fleets_by_location[loc].append(f)
                self._fleet_index[f.id] = f
                
        self._armies_by_location = {}
        self._army_index = {}
        for p in self.context.get_all_planets():
            if hasattr(p, 'armies'):
                for ag in p.armies:
                    # Exclude EMBARKED (on ships) or DESTROYED units
                    if not ag.is_destroyed and getattr(ag, 'state', '') != "EMBARKED":
                        loc = ag.location if ag.location else p
                        if loc not in self._armies_by_location: 
                            self._armies_by_location[loc] = []
                        self._armies_by_location[loc].append(ag)
                        self._army_index[ag.id] = ag
        
        # Rebuild Presence Index
        self._presence_index = {}
        self._location_factions = {}
        
        for loc, fleets in self._fleets_by_location.items():
            if loc not in self._location_factions: 
                self._location_factions[loc] = set()
            for f in fleets:
                self._location_factions[loc].add(f.faction)
                self._presence_index[(f.faction, loc)] = True
                
        for loc, armies in self._armies_by_location.items():
            if loc not in self._location_factions: 
                self._location_factions[loc] = set()
            for ag in armies:
                self._location_factions[loc].add(ag.faction)
                self._presence_index[(ag.faction, loc)] = True

    def get_factions_at(self, location: Any) -> Set[str]:
        """O(1) lookup for all factions at a location."""
        return self._location_factions.get(location, set())

    def is_faction_at(self, faction: str, location: Any) -> bool:
        """O(1) check if a faction is present at a location."""
        return (faction, location) in self._presence_index

    def get_fleet(self, fleet_id: str) -> Optional['Fleet']:
        """O(1) fleet lookup by ID."""
        return self._fleet_index.get(fleet_id)

    def get_army_group(self, army_id: str) -> Optional['ArmyGroup']:
        """O(1) army group lookup by ID."""
        return self._army_index.get(army_id)
        
    def get_fleets_at(self, location: Any) -> List['Fleet']:
        return self._fleets_by_location.get(location, [])
        
    def get_armies_at(self, location: Any) -> List['ArmyGroup']:
        return self._armies_by_location.get(location, [])

    def register_battle(self, location: Any, battle: ActiveBattle):
        self.active_battles[location] = battle

    def remove_battle(self, location: Any):
        if location in self.active_battles:
            del self.active_battles[location]

    def get_active_battle(self, location: Any) -> Optional[ActiveBattle]:
        return self.active_battles.get(location)
