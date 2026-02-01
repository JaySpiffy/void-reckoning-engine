import os
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseReportGenerator(ABC):
    """
    Standard interface for all report generators.
    """
    @abstractmethod
    def generate(self, summary: Dict[str, Any], output_path: str):
        """
        Processes turn summary data and writes it to the specified path.
        """
        pass

    def _ensure_dir(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def _inject_universe_metadata(self, summary: Dict[str, Any], universe_name: str) -> Dict[str, Any]:
        """Injects universe metadata into summary data."""
        from datetime import datetime, timezone
        summary["universe"] = universe_name
        summary["universe_metadata"] = {
            "name": universe_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return summary
