import csv
from src.reporting.generators.base import BaseReportGenerator
from typing import Dict, Any

class CSVReportGenerator(BaseReportGenerator):
    def generate(self, summary: Dict[str, Any], output_path: str):
        self._ensure_dir(output_path)
        
        # Flatten the dictionary
        flat_data = {
            "universe": summary.get("universe", "unknown"),
            "turn": summary["turn"],
            "faction": summary["faction"],
            "req_net": summary["deltas"]["requisition"],
            "req_income": summary["economy"]["income"],
            "req_expense": summary["economy"]["expense"],
            "efficiency": summary["economy"]["efficiency_pct"],
            "planets": summary["territory"]["total_controlled"],
            "planets_delta": summary["deltas"]["planets_count"],
            "fleets": summary["military"]["total_fleets"],
            "mil_power": summary["military"]["military_power_score"],
            "mil_power_delta": summary["deltas"]["military_power"],
            "battles_fought": summary["military"]["battles_fought"],
            "battles_won": summary["military"]["battles_won"],
            "units_recruited": summary["military"]["units_recruited"],
            "units_lost": summary["military"]["units_lost"]
        }
        
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=flat_data.keys())
            writer.writeheader()
            writer.writerow(flat_data)
