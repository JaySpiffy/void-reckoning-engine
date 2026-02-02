from typing import List, Dict, Any, Optional, TYPE_CHECKING
from collections import defaultdict
from src.utils.profiler import profile_method
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.models.fleet import Fleet

from src.core.service_locator import ServiceLocator

class FleetManager:
    """
    Manages fleet registration, master list maintenance, and faction-based indexing.
    Separates fleet state management from the central CampaignEngine.
    """
    def __init__(self, engine: 'CampaignEngine'):
        self.engine = engine
        self._repo = None
        self._index = None # Lazy loaded FleetIndex

    @property
    def index(self):
        if self._index is None:
            from src.utils.fleet_index import FleetIndex
            self._index = FleetIndex()
            # Hydrate from repository to be safe
            for f in self.repository.get_all():
                self._index.add(f)
        return self._index

    @property
    def repository(self):
        if self._repo is None:
            self._repo = ServiceLocator.get("FleetRepository")
        return self._repo

    @property
    def fleets(self) -> List['Fleet']:
        return self.repository.get_all()

    @property
    def fleets_by_faction(self) -> Dict[str, List['Fleet']]:
        # Optimization: Use Index
        # Construct dict from index
        return {f: list(fleets) for f, fleets in self.index._by_faction.items()}

    def get_all_fleets(self) -> List['Fleet']:
        """Returns all registered fleets."""
        return self.repository.get_all()

    def get_fleets_by_faction(self, faction_name: str) -> List['Fleet']:
        """Returns active (not destroyed) fleets for a specific faction using Index."""
        return [f for f in self.index.get_by_faction(faction_name) if not f.is_destroyed]

    @profile_method
    def add_fleet(self, fleet: 'Fleet') -> None:
        """Central method to register a fleet in the engine state."""
        self.repository.save(fleet)
        fleet.engine = self.engine
        self.index.add(fleet)

    @profile_method
    def remove_fleet(self, fleet: 'Fleet') -> None:
        """Central method to unregister a fleet from the engine state."""
        fid = getattr(fleet, 'id', str(id(fleet)))
        self.repository.delete(fid)
        self.index.remove(fleet)

    def register_fleet(self, fleet: 'Fleet') -> None:
        """Adds fleet to master list and faction index via AssetManager (Compatibility)."""
        # Note: In the future, AssetManager should probably call FleetManager directly.
        # For now, we maintain the delegation chain if needed, or point directly to add_fleet.
        self.add_fleet(fleet)

    def unregister_fleet(self, fleet: 'Fleet') -> None:
        """Removes fleet from master list and faction index (Compatibility)."""
        self.remove_fleet(fleet)

    def consolidate_fleets(self, max_size=500, faction_filter: Optional[str] = None) -> int:
        """
        [DEATHBALL_LOGIC] Agnostic: Merges fleets in the same system to form larger battle groups.
        Optimization 3.1: Uses FleetIndex for O(1) location indexing.
        """
        merges_count = 0
        
        # New Logic: Iterate through locations present in the index
        # This skips empty space and reduces O(N) linear scan
        
        # Snapshot keys to avoid runtime error if dictionary changes during iteration (though consolidation shouldn't change location keys immediately)
        locations_with_fleets = list(self.index._by_location.keys())
        
        for loc_key in locations_with_fleets:
            fleets_at_loc = self.index._by_location.get(loc_key, set())
            
            # Convert to list for stable iteration and filtering
            fleets = list(fleets_at_loc)
            
            # Simple grouping by faction
            fleets_by_faction = defaultdict(list)
            for f in fleets:
                if f.is_destroyed or f.is_engaged or f.destination is not None:
                     continue
                if faction_filter and f.faction != faction_filter:
                     continue
                fleets_by_faction[f.faction].append(f)
                
            # Perform Merges
            for faction, faction_fleets in fleets_by_faction.items():
                if len(faction_fleets) < 2: continue
                
                # Sort by size (largest first - merging into the largest)
                faction_fleets.sort(key=lambda x: len(x.units), reverse=True)
                
                target_fleet = faction_fleets[0]
                
                for i in range(1, len(faction_fleets)):
                    source_fleet = faction_fleets[i]
                    
                    if len(target_fleet.units) >= max_size:
                        # Target full, switch target to this one (next largest)
                        target_fleet = source_fleet
                        continue
                     
                    # Optimization 3.3: Use Set-Based Merge
                    # merge_with handles unit transfer, duplicate checks, and resource merging
                    if target_fleet.merge_with(source_fleet):
                        merges_count += 1
                        # Source fleet is cleared and marked destroyed by merge_with
                        # Remove from engine via manager
                        self.remove_fleet(source_fleet)
                        
        return merges_count
