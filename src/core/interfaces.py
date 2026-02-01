from typing import Protocol, List, Dict, Optional, Any, Union

# Forward references for models to avoid circular imports
# We use Any here for models in Protocol typing where strict type checking 
# acts as a barrier, or strings for forward refs if using TYPE_CHECKING.
# For runtime simplicity in Protocols, Any is often acceptable for 
# complex domain objects unless specific structural subtyping is needed.

class IFaction(Protocol):
    name: str
    requisition: float
    home_planet_name: Optional[str]
    unlocked_techs: List[str]
    # Add other critical faction properties here

class IPlanet(Protocol):
    name: str
    owner: str
    # Add other critical planet properties here

class IFleet(Protocol):
    id: str
    faction: str
    location: Any

class ITechManager(Protocol):
    def analyze_tech_tree(self, faction_name: str) -> Dict[str, float]: ...
    def unlock_tech(self, faction: Any, tech_name: str) -> bool: ...

class IEconomyManager(Protocol):
    def get_faction_economic_report(self, faction_name: str) -> Dict[str, Any]: ...

class IBattleManager(Protocol):
    log_dir: Optional[str]
    def resolve_battles_at(self, location: Any, update_indices: bool = True, force_domain: Optional[str] = None) -> None: ...

class IEngine(Protocol):
    """
    Protocol defining the public interface of the CampaignEngine 
    that other Managers should depend on.
    """
    turn_counter: int
    logger: Any
    
    # Manager Access
    tech_manager: ITechManager
    economy_manager: IEconomyManager
    battle_manager: IBattleManager
    
    # State Accessors (from Item 5.4)
    def get_faction(self, faction_name: str) -> Optional[Any]: ...
    def get_planet(self, planet_name: str) -> Optional[Any]: ...
    def get_all_factions(self) -> List[Any]: ...
    def get_all_planets(self) -> List[Any]: ...
    def get_all_fleets(self) -> List[Any]: ...
    def get_fleets_by_faction(self, faction_name: str) -> List[Any]: ...
    
    # State Mutation (from Item 5.4)
    def add_fleet(self, fleet: Any) -> None: ...
    def remove_fleet(self, fleet: Any) -> None: ...
    def update_faction_territory(self, faction_name: str, planet: Any, removal: bool = False) -> None: ...
    def add_faction(self, faction: Any) -> None: ...

class ICombatPhase(Protocol):
    name: str
    def execute(self, context: Dict[str, Any]) -> None: ...

class IRepository(Protocol):
    """Generic repository interface."""
    def get_by_id(self, entity_id: str) -> Optional[Any]: ...
    def get_all(self) -> List[Any]: ...
    def save(self, entity: Any) -> None: ...
    def delete(self, entity_id: str) -> None: ...

class IManager(Protocol):
    """Generic manager interface."""
    def initialize(self) -> None: ...
    def shutdown(self) -> None: ...

