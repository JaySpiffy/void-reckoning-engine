import json
from src.reporting.generators.base import BaseReportGenerator
from typing import Dict, Any

class JSONReportGenerator(BaseReportGenerator):
    def generate(self, summary: Dict[str, Any], output_path: str):
        self._ensure_dir(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
