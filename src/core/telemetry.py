from typing import Dict, Any, List, Optional, Union
import json
import time
from pathlib import Path
from src.reporting.telemetry import EventCategory, VerbosityLevel

class TelemetryLogger:
    def __init__(self, output_dir="telemetry_logs", verbosity="summary"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events = []
        self.verbosity = verbosity 
        self.doctrine_stats = {} 
    
    def log_event(self, category: Union[EventCategory, str], event_type: str, data: Dict[str, Any], 
                  turn: int = 0, faction: Optional[str] = None, 
                  level: Any = None):
        
        cat_str = category.value if hasattr(category, 'value') else str(category)
        
        event = {
            "turn": turn,
            "category": cat_str,
            "type": event_type,
            "data": data,
            "faction": faction,
            "timestamp": time.time()
        }
        self.events.append(event)
        
        # Live Stats Update
        if cat_str == "doctrine":
             self._update_doctrine_stats(data)

    def _update_doctrine_stats(self, data):
        f = data.get('faction')
        d = data.get('doctrine')
        outcome = data.get('outcome')
        if f and d:
             key = (f, d)
             if key not in self.doctrine_stats:
                 self.doctrine_stats[key] = {'wins': 0, 'total': 0, 'casualties': 0}
             
             self.doctrine_stats[key]['total'] += 1
             if outcome == 'WIN': self.doctrine_stats[key]['wins'] += 1
             self.doctrine_stats[key]['casualties'] += data.get('casualties', 0)

    def flush(self):
        # Compat: No-op for now as we keep history in memory until export_to_json
        pass

    def export_to_json(self, filename="telemetry.json"):
        filepath = self.output_dir / filename
        try:
            with open(filepath, 'w') as f:
                json.dump(self.events, f, indent=2)
            # print(f"Telemetry exported to {filepath}")
        except Exception as e:
            print(f"Failed to export telemetry: {e}")

    def get_doctrine_performance(self, faction: str, doctrine: str):
         key = (faction, doctrine)
         stats = self.doctrine_stats.get(key, {'wins': 0, 'total': 0, 'casualties': 0})
         total = stats['total']
         win_rate = stats['wins'] / total if total > 0 else 0.5
         return {
             'win_rate': win_rate,
             'total_battles': total,
             'avg_casualties': stats['casualties'] / max(1, total)
         }
