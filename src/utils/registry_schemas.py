
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

@dataclass
class RegistrySchema:
    name: str
    registry_file: str  # e.g. "building_registry.json"
    source_dirs: List[str]  # e.g. ["infrastructure"]
    required_fields: List[str]
    
    # regex patterns for markdown parsing
    # Key = Field Name, Value = Regex Pattern
    # If list, multiple patterns attempted
    regex_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # specific logic hooks
    standardizer: Callable[[Dict], Dict] = None
    
    # Hooks for universe-specific integrations
    # e.g. "star_wars" -> function to parse XML
    integrations: Dict[str, Callable] = field(default_factory=dict)

# --- Standardizers moved from registry_builder.py ---

def _standardize_building_entry(data: dict) -> dict:
    return {
        "id": data.get("id", "unknown"),
        "name": data.get("name", "Unknown"),
        "tier": int(data.get("tier", 1)),
        "cost": int(data.get("cost", 0)),
        "maintenance": int(data.get("maintenance", 0)),
        "prerequisites": data.get("prerequisites", []),
        "unlocks": data.get("unlocks", []),
        "effects": data.get("effects", {}),
        "faction": data.get("faction"),
        "category": data.get("category", "infrastructure"),
        "source_file": data.get("source_file", "unknown"),
        "source_format": data.get("source_format", "unknown"),
        "capacity": data.get("capacity")
    }

def _standardize_tech_entry(data: dict) -> dict:
    return {
        "id": data.get("id", "unknown"),
        "name": data.get("name", "Unknown"),
        "tier": int(data.get("tier", 1)),
        "cost": int(data.get("cost", 0)),
        "prerequisites": data.get("prerequisites", []),
        "unlocks_buildings": data.get("unlocks_buildings", []),
        "unlocks_ships": data.get("unlocks_ships", []),
        "faction": data.get("faction"),
        "area": data.get("area", "engineering"),
        "category": data.get("category", []),
        "source_file": data.get("source_file", "unknown"),
        "source_format": data.get("source_format", "unknown")
    }

# --- Schema Definitions ---

BUILDING_SCHEMA = RegistrySchema(
    name="Building",
    registry_file="infrastructure/building_registry.json",
    source_dirs=["infrastructure"],
    required_fields=["id", "name", "tier", "cost"],
    regex_patterns={
        "simple_tier": r'\*\s+\*\*Tier\s+(\d+):\s+(.*?)\*\*',  # * **Tier 1: Mine**
        "complex_block": r'### Tier\s+(\d+):\s+(.*?)\n(.*?)(?=\n###|\Z)', # ### Tier 1: Mine ... body ...
        # Field extractors for complex block body
        "body_fields": {
             "cost": r'-\s+\*\*Cost:\*\*\s+(\d+)',
             "maintenance": r'-\s+\*\*Maintenance:\*\*\s+(\d+)',
             "effects": r'-\s+\*\*Effects:\*\*\s*(.*?)(?=- \*\*|- Lore:|\Z)',
             "unlocks": r'-\s+\*\*Unlocks:\*\*\s*(.*?)(?=\n-|\Z)',
             "capacity": r'-\s+\*\*Capacity:\*\*\s*(.*?)(?=\n-|\Z)',
             "prerequisites": r'-\s+\*\*Prerequisites:\*\*\s*(.*?)(?=\n-|\Z)'
        }
    },
    standardizer=_standardize_building_entry
)

TECH_SCHEMA = RegistrySchema(
    name="Technology",
    registry_file="technology/technology_registry.json",
    source_dirs=["technology"],
    required_fields=["id", "name", "tier", "cost"],
    regex_patterns={
        # Tech files are often structure differently: Headers define scope.
        # ## Tier 1 
        # ### Tech Name
        # We might need improved logic in the builder to handle stateful parsing (Tier Header -> Items)
        # For now, we define the regexes used for that stateful parsing.
        "tier_header": r'^##\s+Tier\s+(\d+)',
        "item_header": r'^###\s+(.*)',
        "body_fields": {
            "cost": r'-\s+\*\*Cost:\*\*\s+(\d+)',
            "description": r'-\s+\*\*Description:\*\*\s*(.*)',
            "effects": r'-\s+\*\*Effects:\*\*\s*(.*)',
            "unlocks_inference": r'[Uu]nlocks\s+([^.,;]*)' # Logic needs to handle this specific case
        }
    },
    standardizer=_standardize_tech_entry
)
