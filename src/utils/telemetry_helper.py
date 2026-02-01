from typing import Optional, Dict, Any

class TelemetryHelper:
    """
    Helper class to safely log telemetry events without repetitive None checks.
    Wraps an engine instance or telemetry object.
    """
    
    def __init__(self, engine):
        self.engine = engine

    @property
    def _telemetry(self):
        return getattr(self.engine, 'telemetry', None)

    def log_event(self, category: str, event_name: str, data: Dict[str, Any], turn: Optional[int] = None, faction: Optional[str] = None):
        """Safe wrapper for telemetry.log_event."""
        tm = self._telemetry
        if tm:
            # Import category dynamically to avoid circular imports if possible,
            # or map string category to Enum if Telemetry expects Enum.
            # Assuming Telemetry.log_event takes (category, name, data, turn, faction)
            
            # Note: The existing code uses EventCategory.TECHNOLOGY etc. 
            # We should probably accept strings and convert, or pass through.
            
            # If category is string, try to resolve to EventCategory
            cat_obj = category
            if isinstance(category, str):
                try:
                    from src.reporting.telemetry import EventCategory
                    # Try to match name (case insensitive?)
                    # For now, assume usage passes valid enum or compatible type
                    if hasattr(EventCategory, category.upper()):
                        cat_obj = getattr(EventCategory, category.upper())
                except ImportError:
                    pass

            current_turn = turn if turn is not None else getattr(self.engine, 'turn_counter', 0)
            tm.log_event(cat_obj, event_name, data, turn=current_turn, faction=faction)

    def log_resource_spend(self, faction: str, amount: float, category: str, source_planet: str = "Unknown"):
        """Specialized logger for resource spending."""
        tm = self._telemetry
        if tm and hasattr(tm, 'record_resource_spend'):
            tm.record_resource_spend(faction, amount, category=category, source_planet=source_planet)

    def log_recruitment(self, faction: str, unit_name: str, cost: float, location: str):
        """Log unit recruitment."""
        self.log_resource_spend(faction, cost, category="Recruitment", source_planet=location)
        
        # Also log generic event?
        # self.log_event("ECONOMY", "unit_recruited", {"unit": unit_name, "cost": cost}, faction=faction)

    def log_combat_enc(self, faction: str, enemies: list, location: str):
        """Log combat encounter start."""
        self.log_event("COMBAT", "engagement_started", 
                       {"location": location, "enemies": enemies}, 
                       faction=faction)

    def log_tech_unlock(self, faction: str, tech_id: str):
         self.log_event("TECHNOLOGY", "tech_unlocked", {"tech_id": tech_id}, faction=faction)
