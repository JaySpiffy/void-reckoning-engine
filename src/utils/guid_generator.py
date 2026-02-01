"""
GUID Generator Module for PPS (Persistent Procedural Sandbox)

This module provides utilities for generating unique persistent identifiers
for game entities, supporting the dual-passport system for backward compatibility.
"""

import uuid
import time


def generate_entity_guid(entity_type: str, prefix: str = "") -> str:
    """
    Generates a unique persistent ID.
    
    Format: TYPE_PREFIX_TIMESTAMP_UUID
    Example: FACTION_NEON_20260120_A1B2C3
    
    Args:
        entity_type: The type of entity (e.g., "FACTION", "UNIT", "PLANET")
        prefix: Optional prefix to add to the GUID (e.g., faction name)
    
    Returns:
        A unique GUID string in the format TYPE_PREFIX_TIMESTAMP_UUID
    
    Examples:
        >>> generate_entity_guid("FACTION", "NEON")
        'FACTION_NEON_1737360000_A1B2C3'
        
        >>> generate_entity_guid("UNIT", "Augmented Legionnaire")
        'UNIT_SPACE_MARINE_1737360000_D4E5F6'
    """
    timestamp = int(time.time())
    unique_str = str(uuid.uuid4())[:6].upper()
    
    clean_prefix = prefix.upper().replace(" ", "_")
    return f"{entity_type}_{clean_prefix}_{timestamp}_{unique_str}"


def generate_legacy_guid(entity_type: str, original_name: str, suffix: str = "001") -> str:
    """
    Generates a GUID for legacy entities using a predictable format.
    
    This is used for existing entities that need a GUID but should maintain
    a consistent, predictable identifier for backward compatibility.
    
    Args:
        entity_type: The type of entity (e.g., "FACTION")
        original_name: The original name of the entity
        suffix: A suffix to ensure uniqueness (default: "001")
    
    Returns:
        A predictable GUID string
    
    Examples:
        >>> generate_legacy_guid("FACTION", "Hegemony")
        'FACTION_LEGACY_IMPERIUM_001'
    """
    clean_name = original_name.upper().replace(" ", "_")
    return f"{entity_type}_LEGACY_{clean_name}_{suffix}"


def validate_guid(guid: str) -> bool:
    """
    Validates that a string is in the expected GUID format.
    
    Args:
        guid: The GUID string to validate
    
    Returns:
        True if the GUID appears valid, False otherwise
    """
    if not guid or not isinstance(guid, str):
        return False
    
    parts = guid.split("_")
    # GUIDs should have at least 4 parts: TYPE_PREFIX_TIMESTAMP_UUID or TYPE_LEGACY_NAME_SUFFIX
    return len(parts) >= 4


def extract_entity_type(guid: str) -> str:
    """
    Extracts the entity type from a GUID.
    
    Args:
        guid: The GUID string
    
    Returns:
        The entity type (first part of the GUID)
    
    Examples:
        >>> extract_entity_type("FACTION_NEON_1737360000_A1B2C3")
        'FACTION'
    """
    if not guid:
        return ""
    return guid.split("_")[0] if "_" in guid else guid
