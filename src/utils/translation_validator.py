import json
import os
import sys
from typing import Dict, List, Any

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Static Stat Metrics
VALID_METRICS = ["hp", "ma", "md", "damage", "armor", "speed", "bs", "ws", "w", "a", "ld", "sv"]

class TranslationValidator:
    def __init__(self, table_path: str):
        self.table_path = table_path
        self.errors = []
        self.warnings = []

    def validate(self) -> bool:
        if not os.path.exists(self.table_path):
            self.errors.append(f"Translation table not found at {self.table_path}")
            return False

        try:
            with open(self.table_path, 'r', encoding='utf-8') as f:
                table = json.load(f)
        except Exception as e:
            self.errors.append(f"Failed to parse JSON: {e}")
            return False

        universes = [u for u in table.keys() if u != "default"]
        
        for source_uni in universes:
            targets = table[source_uni]
            for target_uni, mappings in targets.items():
                if target_uni not in universes and target_uni != "default":
                    self.warnings.append(f"Universe '{target_uni}' is a target from '{source_uni}' but not defined as a source.")
                
                # Validate Metrics
                for metric, multiplier in mappings.items():
                    if metric not in VALID_METRICS:
                        self.errors.append(f"Invalid metric '{metric}' in mapping {source_uni} -> {target_uni}")
                    if not isinstance(multiplier, (int, float)):
                        self.errors.append(f"Multiplier for '{metric}' in {source_uni} -> {target_uni} must be a number.")

        return len(self.errors) == 0

    def print_report(self):
        print(f"\n--- Translation Validation Report: {os.path.basename(self.table_path)} ---")
        if not self.errors and not self.warnings:
            print("All clear! No issues found.")
            return

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for err in self.errors:
                print(f" [!] {err}")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f" [?] {warn}")
        print("\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate cross-universe translation table.")
    parser.add_argument("--table", type=str, help="Path to translation_table.json")
    args = parser.parse_args()

    table_path = args.table
    if not table_path:
        # Default to universes/base/translation_table.json relative to project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        table_path = os.path.join(project_root, "universes", "base", "translation_table.json")

    validator = TranslationValidator(table_path)
    success = validator.validate()
    validator.print_report()
    
    if not success:
        sys.exit(1)
