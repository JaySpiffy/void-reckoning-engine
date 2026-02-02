from typing import Dict, Set, List, Optional, Any, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from src.models.fleet import Fleet

class FleetIndex:
    """
    High-performance index for Fleet lookups.
    Provides O(1) access by ID and Faction.
    """
    def __init__(self):
        self._by_id: Dict[str, 'Fleet'] = {}
        self._by_faction: Dict[str, Set['Fleet']] = defaultdict(set)
        self._by_location: Dict[str, Set['Fleet']] = defaultdict(set)
        
    def add(self, fleet: 'Fleet') -> None:
        """Adds a fleet to the index."""
        if not fleet: return
        
        # Use existing fleet.id or memory address if none (fallback)
        fid = getattr(fleet, 'id', str(id(fleet)))
        
        self._by_id[fid] = fleet
        if fleet.faction:
            self._by_faction[fleet.faction].add(fleet)
            
        # Location Indexing
        loc = getattr(fleet, 'location', None)
        if loc:
            # We index by location name or ID if available, or just the object hash
            # Ideally consistent. Let's use name if available, else object.
            # But consolidating uses equality check. Let's try to index by the object itself if hashable?
            # Or better, a robust key. 
            # Given StarSystem/Planet usually have names that are unique enough for this context, 
            # let's use a safe key generator.
            loc_key = self._get_loc_key(loc)
            if loc_key:
                self._by_location[loc_key].add(fleet)

    def remove(self, fleet: 'Fleet') -> None:
        """Removes a fleet from the index."""
        if not fleet: return
        
        fid = getattr(fleet, 'id', str(id(fleet)))
        
        if fid in self._by_id:
            del self._by_id[fid]
            
        if fleet.faction and fleet.faction in self._by_faction:
            # Use discard to avoid KeyError if set doesn't contain it
            self._by_faction[fleet.faction].discard(fleet)
            if not self._by_faction[fleet.faction]:
                del self._by_faction[fleet.faction]

        # Location Cleanup
        loc = getattr(fleet, 'location', None)
        if loc:
            loc_key = self._get_loc_key(loc)
            if loc_key and loc_key in self._by_location:
                 self._by_location[loc_key].discard(fleet)
                 if not self._by_location[loc_key]:
                     del self._by_location[loc_key]

    def get(self, fleet_id: str) -> Optional['Fleet']:
        return self._by_id.get(fleet_id)
        
    def get_by_faction(self, faction_name: str) -> List['Fleet']:
        """Returns a list of fleets for the given faction."""
        return list(self._by_faction.get(faction_name, []))

    def get_by_location(self, location: Any) -> List['Fleet']:
        """Returns a list of fleets at a specific location."""
        loc_key = self._get_loc_key(location)
        if loc_key:
             return list(self._by_location.get(loc_key, []))
        return []

    def get_all(self) -> List['Fleet']:
        return list(self._by_id.values())

    def clear(self):
        self._by_id.clear()
        self._by_faction.clear()
        self._by_location.clear()

    def _get_loc_key(self, location: Any) -> Optional[str]:
        """Helper to derive a consistent key from a location object."""
        if hasattr(location, 'id'): return str(location.id)
        if hasattr(location, 'name'): return str(location.name)
        return str(location) # Fallback
