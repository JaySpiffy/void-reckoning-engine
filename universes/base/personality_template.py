from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FactionPersonality:
    """
    Universe-agnostic profile for AI faction behavior.
    
    Attributes:
        name: The name of the faction.
        aggression: Multiplier for power checks (High = Attack when weaker).
        expansion_bias: Preference for taking new land vs developing.
        cohesiveness: Preference for large fleets vs many small ones.
        retreat_threshold: Retreat if Power < Enemy * Threshold.
        description: User-friendly description of the AI behavior.
        strategic_doctrine: The high-level strategic goal (e.g., AGGRESSIVE_EXPANSION).
        retreat_flexibility: How much strategic value affects retreat (0.0-1.0).
        planning_horizon: How many turns ahead the AI plans.
        adaptation_speed: How quickly the AI switches strategies (0.0-1.0).
        rally_point_preference: Preferred location for regrouping.
        combat_doctrine: Optional universe-specific tactical doctrine.
        doctrine_intensity: How strongly the combat doctrine affects behavior.
        tech_focus: List of technology categories to prioritize.
        fleet_composition_balance: Dict defining capital/screen/carrier ratios.
        turtling_tendency: Tendency to prioritize defense (0.0-1.0).
        quirks: Dictionary of custom quirks and their parameters.
        tech_doctrine: Cross-universe tech policy (RADICAL, PURITAN, PRAGMATIC, XENOPHOBIC, ADAPTIVE).
    """
    name: str
    aggression: float = 1.0
    expansion_bias: float = 1.0
    cohesiveness: float = 1.0
    retreat_threshold: float = 0.5
    description: str = "Balanced"
    
    strategic_doctrine: str = "BALANCED"
    retreat_flexibility: float = 0.5
    planning_horizon: int = 5
    adaptation_speed: float = 0.5
    rally_point_preference: str = "NEAREST_SAFE"
    
    combat_doctrine: Optional[str] = "STANDARD"
    doctrine_intensity: float = 1.0
    
    # --- Advanced Strategy Fields ---
    tech_focus: Optional[list] = field(default_factory=list)
    fleet_composition_balance: Optional[dict] = field(default_factory=dict)
    turtling_tendency: float = 0.5
    quirks: Optional[dict] = field(default_factory=dict)
    tech_doctrine: Optional[str] = "PRAGMATIC"  # RADICAL, PURITAN, PRAGMATIC, XENOPHOBIC, ADAPTIVE
    
    # --- Data-Driven Quirks (Multi-Universe Support) ---
    threat_affinity: float = 0.0      # Positive = Likes fighting strong enemies (e.g. Orks)
    biomass_hunger: float = 0.0       # Weight for resource-rich planets (e.g. Tyranids)
    diplomacy_bonus: int = 0          # Bonus to diplomatic relations (e.g. Federation)
    on_kill_effect: Optional[str] = None # e.g. "assimilate" for Borg
    retreat_threshold_mod: float = 0.0 # Shift retreat threshold (e.g. Orks -0.2)
    navy_recruitment_mult: float = 1.0
    army_recruitment_mult: float = 1.0
    casualty_plunder_ratio: float = 0.0
    evasion_rating: float = 0.0

    def to_dict(self) -> dict:
        """Serializes the personality to a dictionary."""
        return self.__dict__

    @classmethod
    def from_dict(cls, data: dict) -> 'FactionPersonality':
        """Deserializes a personality from a dictionary."""
        return cls(**data)
