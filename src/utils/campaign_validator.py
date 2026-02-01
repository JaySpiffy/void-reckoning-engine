
import json
import os
from typing import Dict, List, Tuple
from pathlib import Path

class CampaignValidator:
    """Validates campaign configuration files against schema and logical consistency."""
    
    SCHEMA_PATH = os.path.join(Path(__file__).parent.parent.parent, "universes", "base", "campaign_config_schema.json")
    
    def __init__(self):
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict:
        if os.path.exists(self.SCHEMA_PATH):
            with open(self.SCHEMA_PATH, 'r') as f:
                return json.load(f)
        return {}

    def validate_campaign_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """Validates config against schema and logic checks."""
        errors = []
        
        # 1. Manual Schema Validation (No jsonschema dep)
        required_fields = ["campaign_id", "name", "factions", "victory_conditions"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
                
        if "missions" in config:
            if not isinstance(config["missions"], list):
                errors.append("Field 'missions' must be a list")
            else:
                for idx, m in enumerate(config["missions"]):
                    if not isinstance(m, dict):
                        errors.append(f"Mission at index {idx} is not an object")
                        continue
                    if "id" not in m or "name" not in m:
                        errors.append(f"Mission at index {idx} missing id or name")
                        
        if "victory_conditions" in config:
             if not isinstance(config["victory_conditions"], list):
                  errors.append("Field 'victory_conditions' must be a list")
             else:
                  for idx, vc in enumerate(config["victory_conditions"]):
                      if not isinstance(vc, dict):
                          errors.append(f"Victory Condition at index {idx} is not an object")
                          continue
                      if "type" not in vc or "description" not in vc:
                          errors.append(f"Victory Condition at index {idx} missing type or description")

        if errors:
            return False, errors
            
        # 2. Logical Validation
        # Check Factions
        if not config.get("factions") and not config.get("scenarios"):
             # Stellaris might have empty factions list initially but should exist
             pass # Warning?
             
        # Check Missions
        missions = config.get("missions", [])
        mission_ids = set()
        for m in missions:
            if "id" in m:
                if m["id"] in mission_ids:
                    errors.append(f"Duplicate mission ID: {m['id']}")
                mission_ids.add(m["id"])
            
        # Check Prerequisites
        for m in missions:
             for p in m.get("prerequisites", []):
                 if p not in mission_ids:
                     errors.append(f"Mission {m.get('id')} requires missing mission {p}")
                     
        return len(errors) == 0, errors

def validate_campaign_file(filepath: str) -> bool:
    """Helper to validate a file path directly."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
        
    try:
        with open(filepath, 'r') as f:
             data = json.load(f)
             
        validator = CampaignValidator()
        valid, errors = validator.validate_campaign_config(data)
        
        if valid:
            print("Campaign Configuration is VALID.")
            return True
        else:
            print("Campaign Configuration is INVALID:")
            for e in errors:
                print(f" - {e}")
            return False
            
    except Exception as e:
        print(f"Error validating {filepath}: {e}")
        return False
