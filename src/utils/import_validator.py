import os
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class ValidationResult:
    category: str  # "units", "buildings", "tech", "factions", "file_structure"
    severity: str  # "critical", "warning", "info"
    entity_id: str
    message: str
    file_path: Optional[str] = None

class ImportValidator:
    """
    Unified validation system for imported game data.
    Validates file structure, registry consistency, and game balance.
    Note: Atomic budget validation has been decommissioned.
    """
    
    def __init__(self, universe_name: str, universe_root: str):
        self.universe_name = universe_name
        self.universe_root = universe_root
        self.results: List[ValidationResult] = []
        
    def validate_file_structure(self) -> List[ValidationResult]:
        """Checks if all required directories exist."""
        required_dirs = [
            "factions", "technology", "infrastructure", 
            "campaigns", "maps", "events"
        ]
        
        violations = []
        for d in required_dirs:
            path = os.path.join(self.universe_root, self.universe_name, d)
            if not os.path.exists(path):
                violations.append(ValidationResult(
                    category="file_structure",
                    severity="critical",
                    entity_id=d,
                    message=f"Missing required directory: {d}",
                    file_path=path
                ))
        return violations

    def validate_dna_budget(self, dna_signature: Dict, entity_id: str, budget_type: str = "unit") -> Optional[ValidationResult]:
        """[DEPRECATED] Placeholder for legacy DNA budget validation."""
        return None

    def validate_registry(self, registry_name: str, universe_name: str) -> List[ValidationResult]:
        """Validates a built registry for consistency."""
        reg_path = os.path.join(self.universe_root, universe_name, "factions" if registry_name != "campaigns" else "campaigns", f"{registry_name}_registry.json")
        if registry_name == "tech":
            reg_path = os.path.join(self.universe_root, universe_name, "technology", "technology_registry.json")
        elif registry_name == "buildings":
            reg_path = os.path.join(self.universe_root, universe_name, "infrastructure", "building_registry.json")
            
        if not os.path.exists(reg_path):
             return [ValidationResult(
                category=registry_name,
                severity="critical",
                entity_id=registry_name,
                message=f"Registry not found: {reg_path}",
                file_path=reg_path
             )]
             
        violations = []
        try:
            with open(reg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for item_id, item_data in data.items():
                if "name" not in item_data:
                    violations.append(ValidationResult(registry_name, "warning", item_id, "Missing 'name' field"))
                if "source_file" not in item_data:
                    violations.append(ValidationResult(registry_name, "info", item_id, "Missing 'source_file' attribution"))
                    
                if registry_name == "factions":
                    if not item_data.get("subfactions"):
                        violations.append(ValidationResult(registry_name, "warning", item_id, "No subfactions defined"))
                        
        except Exception as e:
            violations.append(ValidationResult(registry_name, "critical", "parsing", str(e), reg_path))
            
        return violations

    def get_summary(self) -> Dict[str, int]:
        """Returns counts of issues by severity."""
        summary = {"critical": 0, "warning": 0, "info": 0}
        for r in self.results:
            summary[r.severity] += 1
        return summary
