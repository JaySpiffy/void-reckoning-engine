from fastapi import Query, Depends, HTTPException
from typing import Optional, Tuple
import logging
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service

logger = logging.getLogger(__name__)

class FilterParams:
    """
    Encapsulates filter parameters and provides resolution logic.
    """
    def __init__(
        self,
        faction: str,
        min_turn: Optional[int],
        max_turn: Optional[int],
        downsample: Optional[int]
    ):
        self.faction = faction
        self.min_turn = min_turn
        self.max_turn = max_turn
        self.downsample = downsample

    def resolve(self, service) -> Tuple[str, str, Optional[str], list, Optional[Tuple[int, int]], Optional[int]]:
        """
        Resolve filters against the dashboard service context.
        Returns: (universe, run_id, batch_id, active_factions, turn_range, downsample)
        """
        universe = service.universe
        run_id = service.run_id
        batch_id = service.batch_id

        # Handle faction filter
        valid_factions = service.data_provider.get_active_factions(universe, run_id, batch_id)
        active_factions = []
        
        if self.faction and self.faction.lower() != "all":
            requested_factions = [f.strip() for f in self.faction.split(',')]
            for f in requested_factions:
                if f in valid_factions:
                    active_factions.append(f)
                else:
                    logger.warning(f"Requested invalid faction: {f}")
        else:
            active_factions = valid_factions

        # Handle turn range
        turn_range = None
        if self.min_turn is not None or self.max_turn is not None:
             if self.min_turn is not None and self.max_turn is not None:
                  turn_range = (self.min_turn, self.max_turn)
             elif self.min_turn is not None:
                  turn_range = (self.min_turn, 999999) # open ended
             elif self.max_turn is not None:
                  turn_range = (0, self.max_turn)
        else:
            # Default to full range if not specified to prevent unpacking errors in data provider
            # Ideally we would call service.get_max_turn() but a safe large integer works for SQL "BETWEEN"
            turn_range = (0, 999999)

        return (universe, run_id, batch_id, active_factions, turn_range, self.downsample)

async def get_filter_params(
    faction: Optional[str] = Query("all", description="Faction filter, 'all' for no filter"),
    min_turn: Optional[int] = Query(None, description="Minimum turn number"),
    max_turn: Optional[int] = Query(None, description="Maximum turn number"),
    downsample: Optional[int] = Query(None, description="Downsample factor")
) -> FilterParams:
    """
    Dependency to extract standard filter parameters.
    Returns a FilterParams instance which can be resolved later with the service.
    """
    return FilterParams(faction, min_turn, max_turn, downsample)
