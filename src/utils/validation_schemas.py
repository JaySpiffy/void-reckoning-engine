from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)

class UnitStateSchema(BaseModel):
    """Schema for validating individual Unit state packets."""
    blueprint_id: Optional[str] = None
    name: str = "Unknown Unit"
    faction: str = "Unknown"
    unit_class: Optional[str] = None
    domain: Optional[str] = None
    traits: List[str] = []
    rank: int = 0
    xp: int = 0
    service_record: List[Dict[str, Any]] = []
    tier: int = 1
    source_universe: Optional[str] = None
    is_translated: bool = False
    active_universe: Optional[str] = None

class FleetPackageSchema(BaseModel):
    """Schema for validating the fleet package during portal handoffs."""
    fleet_id: str
    faction: str
    portal_exit_coords: Optional[Tuple[float, float]] = None
    units: List[Dict[str, Any]]
    origin_universe: str
    destination_universe: str

class PortalCommandSchema(BaseModel):
    """Schema for validating inter-process portal commands."""
    action: str = Field(..., pattern="^(INJECT_FLEET|REMOVE_FLEET)$")
    package: Optional[FleetPackageSchema] = None
    fleet_id: Optional[str] = None

def validate_portal_command(data: Dict[str, Any]) -> Optional[PortalCommandSchema]:
    """
    Validates a portal command dictionary against the PortalCommandSchema.
    Returns the validated schema object or None if invalid (after logging error).
    """
    try:
        return PortalCommandSchema(**data)
    except ValidationError as e:
        logger.error(f"Portal Command Validation Failed: {e}")
        return None

def validate_unit_state(data: Dict[str, Any]) -> Optional[UnitStateSchema]:
    """
    Validates a unit state packet.
    """
    try:
        return UnitStateSchema(**data)
    except ValidationError as e:
        logger.error(f"Unit State Validation Failed: {e}")
        return None
