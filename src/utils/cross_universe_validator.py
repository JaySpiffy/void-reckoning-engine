import json
from typing import Dict, List, Tuple
from pathlib import Path
from src.core.config import UNIVERSE_ROOT

class CrossUniverseValidator:
    """
    Validates translation tables and balance across universes.
    """
    
    def __init__(self):
        self.translation_table_path = Path(UNIVERSE_ROOT) / "base" / "translation_table.json"
        self.errors = []
        self.warnings = []
        
    def validate_translation_table(self) -> Tuple[bool, List[str]]:
        """
        Validates translation table for:
        - Symmetry (A->B and B->A should be reciprocal)
        - Completeness (all universe pairs defined)
        - Reasonable ranges (multipliers between 0.5 and 2.0)
        """
        if not self.translation_table_path.exists():
            return False, [f"Translation table not found: {self.translation_table_path}"]

        with open(self.translation_table_path, 'r') as f:
            table = json.load(f)
            
        universes = [k for k in table.keys() if k != "default"]
        
        # Check symmetry
        for uni_a in universes:
            for uni_b in universes:
                if uni_a == uni_b:
                    continue
                    
                if uni_b not in table.get(uni_a, {}):
                    self.warnings.append(f"Missing mapping: {uni_a} -> {uni_b}")
                    continue
                    
                if uni_a not in table.get(uni_b, {}):
                    self.warnings.append(f"Missing reverse mapping: {uni_b} -> {uni_a}")
                    continue
                    
                # Check reciprocal values
                forward = table[uni_a][uni_b]
                reverse = table[uni_b][uni_a]
                
                for metric in forward.keys():
                    if metric not in reverse:
                        continue
                        
                    fwd_val = forward[metric]
                    rev_val = reverse[metric]
                    if fwd_val == 0:
                        self.errors.append(f"Zero multiplier in {uni_a}->{uni_b} {metric}")
                        continue

                    expected_rev = 1.0 / fwd_val
                    
                    if abs(rev_val - expected_rev) > 0.05:
                        self.warnings.append(
                            f"Asymmetric mapping {uni_a}->{uni_b} {metric}: "
                            f"{fwd_val} vs {rev_val} (expected ~{expected_rev:.2f})"
                        )
                        
        # Check ranges
        for uni_a in universes:
            for uni_b_mappings in table.get(uni_a, {}).values():
                if not isinstance(uni_b_mappings, dict): continue
                for metric, value in uni_b_mappings.items():
                    if value < 0.1 or value > 10.0:
                        self.errors.append(
                            f"Extreme multiplier {uni_a}->{uni_b} {metric}: {value}"
                        )
                    elif value < 0.5 or value > 2.0:
                        self.warnings.append(
                            f"Significant multiplier {uni_a}->{uni_b} {metric}: {value}"
                        )
                        
        return len(self.errors) == 0, self.errors + self.warnings
        
    def generate_balance_report(self, output_path: str):
        """Generate HTML report of cross-universe balance."""
        # Implementation would create visual comparison charts
        pass
