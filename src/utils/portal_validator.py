
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class PortalValidator:
    """
    Utility for validating portal configurations and cross-universe consistency.
    """
    
    @staticmethod
    def validate_portal_config(config_path: Path) -> Dict[str, Any]:
        """
        Validates a portal_config.json file against basic structural requirements.
        In a full implementation, this would use the JSON schema.
        """
        if not config_path.exists():
            return {"valid": False, "error": f"Config file not found: {config_path}"}
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "enable_portals" not in data:
                return {"valid": False, "error": "Missing 'enable_portals' key"}
            if "portals" not in data or not isinstance(data["portals"], list):
                return {"valid": False, "error": "Missing or invalid 'portals' array"}
                
            for i, p in enumerate(data["portals"]):
                required = ["portal_id", "source_coords", "dest_universe", "dest_coords"]
                for field in required:
                    if field not in p:
                        return {"valid": False, "error": f"Portal at index {i} missing '{field}'"}
                
                if not isinstance(p["source_coords"], list) or len(p["source_coords"]) != 2:
                    return {"valid": False, "error": f"Portal {p['portal_id']} has invalid source_coords"}
                if not isinstance(p["dest_coords"], list) or len(p["dest_coords"]) != 2:
                    return {"valid": False, "error": f"Portal {p['portal_id']} has invalid dest_coords"}
            
            return {"valid": True, "data": data}
        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"JSON Decode Error: {e}"}
        except Exception as e:
            return {"valid": False, "error": f"Unexpected Error: {e}"}

    @staticmethod
    def validate_bidirectional_portals(universe_a_name: str, universe_b_name: str, universes_root: Path) -> List[str]:
        """
        Ensures that portals defined in Universe A targeting Universe B 
        have matching definitions in Universe B targeting Universe A.
        """
        errors = []
        path_a = universes_root / universe_a_name / "portal_config.json"
        path_b = universes_root / universe_b_name / "portal_config.json"
        
        cfg_a = PortalValidator.validate_portal_config(path_a)
        cfg_b = PortalValidator.validate_portal_config(path_b)
        
        if not cfg_a["valid"]:
            return [f"Universe {universe_a_name}: {cfg_a['error']}"]
        if not cfg_b["valid"]:
            return [f"Universe {universe_b_name}: {cfg_b['error']}"]
            
        portals_a = {p["portal_id"]: p for p in cfg_a["data"]["portals"] if p["dest_universe"] == universe_b_name}
        portals_b = {p["portal_id"]: p for p in cfg_b["data"]["portals"] if p["dest_universe"] == universe_a_name}
        
        # Check A -> B
        for pid, p in portals_a.items():
            if pid not in portals_b:
                errors.append(f"Portal '{pid}' in {universe_a_name} targets {universe_b_name}, but no matching portal exists in {universe_b_name}")
            else:
                # Check coordinates match (A.source == B.dest and A.dest == B.source)
                pb = portals_b[pid]
                if p["source_coords"] != pb["dest_coords"]:
                    errors.append(f"Portal '{pid}': {universe_a_name} source {p['source_coords']} does not match {universe_b_name} dest {pb['dest_coords']}")
                if p["dest_coords"] != pb["source_coords"]:
                    errors.append(f"Portal '{pid}': {universe_a_name} dest {p['dest_coords']} does not match {universe_b_name} source {pb['source_coords']}")
        
        # Check B -> A
        for pid in portals_b:
            if pid not in portals_a:
                errors.append(f"Portal '{pid}' in {universe_b_name} targets {universe_a_name}, but no matching portal exists in {universe_a_name}")
                
        return errors

    @staticmethod
    def validate_coordinates(coords: List[float], galaxy_size: float = 100.0) -> bool:
        """Checks if coordinates are within galaxy bounds."""
        return 0 <= coords[0] <= galaxy_size and 0 <= coords[1] <= galaxy_size

    @staticmethod
    def generate_portal_report(universes_root: Path) -> str:
        """Generates a summary of all configured portals."""
        lines = ["# Multiverse Portal Network Report", ""]
        
        universes = [d.name for d in universes_root.iterdir() if d.is_dir() and (d / "portal_config.json").exists()]
        
        if not universes:
            return "No universe portal configurations found."
            
        for uni in sorted(universes):
            cfg = PortalValidator.validate_portal_config(universes_root / uni / "portal_config.json")
            if cfg["valid"]:
                data = cfg["data"]
                lines.append(f"## Universe: {uni} ({'Enabled' if data['enable_portals'] else 'Disabled'})")
                for p in data["portals"]:
                    lines.append(f"- **{p['portal_id']}**: {p['source_coords']} -> {p['dest_universe']} {p['dest_coords']} ({p.get('placement_strategy', 'nearest_system')})")
                lines.append("")
            else:
                lines.append(f"## Universe: {uni} (Error: {cfg['error']})")
                
        return "\n".join(lines)
