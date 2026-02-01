from typing import List, Dict, Any, Optional, TYPE_CHECKING
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
        # Compatibility support
        result = {}
        for f in self.repository.get_all():
            if f.faction not in result:
                result[f.faction] = []
            result[f.faction].append(f)
        return result

    def get_all_fleets(self) -> List['Fleet']:
        """Returns all registered fleets."""
        return self.repository.get_all()

    def get_fleets_by_faction(self, faction_name: str) -> List['Fleet']:
        """Returns active (not destroyed) fleets for a specific faction."""
        return [f for f in self.repository.get_by_faction(faction_name) if not f.is_destroyed]

    @profile_method
    def add_fleet(self, fleet: 'Fleet') -> None:
        """Central method to register a fleet in the engine state."""
        self.repository.save(fleet)
        fleet.engine = self.engine

    @profile_method
    def remove_fleet(self, fleet: 'Fleet') -> None:
        """Central method to unregister a fleet from the engine state."""
        fid = getattr(fleet, 'id', str(id(fleet)))
        self.repository.delete(fid)

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
        Iterates through systems/planets and merges idle fleets of the same faction.
        """
        merges_count = 0
        
        # Build location index: {planet_obj: {faction: [fleets]}}
        loc_index = {}
        
        # Filter source fleets
        source_fleets = self.fleets
        if faction_filter:
            source_fleets = [f for f in self.fleets if f.faction == faction_filter]
        
        for f in source_fleets:
            if f.is_destroyed or f.is_engaged or f.destination is not None: 
                continue # Skip moving or fighting fleets
            
            loc = f.location
            if not loc: continue
            
            if loc not in loc_index: loc_index[loc] = {}
            if f.faction not in loc_index[loc]: loc_index[loc][f.faction] = []
            loc_index[loc][f.faction].append(f)
            
        # Execute Merges
        for loc, faction_map in loc_index.items():
            for faction, fleets in faction_map.items():
                if len(fleets) < 2: continue
                
                # Sort by size descending (Merge small into big)
                fleets.sort(key=lambda x: len(x.units), reverse=True)
                
                target_fleet = fleets[0]
                
                for i in range(1, len(fleets)):
                    candidate = fleets[i]
                    
                    # Check size limit
                    current_size = len(target_fleet.units)
                    candidate_size = len(candidate.units)
                    
                    if current_size + candidate_size <= max_size:
                        if target_fleet.merge_with(candidate):
                            merges_count += 1
                            # Candidate automatically marked destroyed by merge_with
                            # Remove from engine via manager
                            self.remove_fleet(candidate)
                            
        if merges_count > 0 and self.engine and self.engine.logger:
             self.engine.logger.campaign(f"[FLEET] Consolidated {merges_count} fleets into larger battle groups.")
             
        return merges_count
