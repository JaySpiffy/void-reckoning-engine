
import logging
from typing import List, Dict, Any, Optional, Tuple
from src.reporting.indexing.orchestrator import ReportIndexer

logger = logging.getLogger(__name__)

class ReplayAnalyzer:
    """
    Analyzes and compares two simulation runs to identify divergence points
    and quantify the 'Butterfly Effect'.
    """
    def __init__(self, indexer: ReportIndexer):
        self.indexer = indexer

    def compare_runs(self, universe: str, run_id_a: str, run_id_b: str) -> Dict[str, Any]:
        """
        Compares two runs and returns a divergence report.
        """
        events_a = self._get_sorted_events(universe, run_id_a)
        events_b = self._get_sorted_events(universe, run_id_b)
        
        divergence = self._find_first_divergence(events_a, events_b)
        drift = self._calculate_drift(universe, run_id_a, run_id_b)
        
        return {
            "run_a": run_id_a,
            "run_b": run_id_b,
            "divergence": divergence,
            "drift_metrics": drift
        }

    def _get_sorted_events(self, universe: str, run_id: str) -> List[Dict[str, Any]]:
        """
        Fetches events sorted by turn and logical order, excluding non-deterministic fields.
        """
        cursor = self.indexer.conn.cursor()
        # We order by turn, then by event_type/category/faction to try and get a stable comparison order
        # implicit reliance on ID or timestamp is risky if they drift slightly
        query = """
            SELECT turn, category, event_type, faction, data_json
            FROM events
            WHERE universe = ? AND run_id = ?
            ORDER BY turn ASC, id ASC
        """
        cursor.execute(query, (universe, run_id))
        
        sanitized = []
        import json
        for row in cursor.fetchall():
            try:
                data = json.loads(row[4]) if row[4] else {}
                # Remove timestamps or UUIDs from data if they are expected to differ
                # identifying *what* to remove is tricky without strict schema
                sanitized.append({
                    "turn": row[0],
                    "category": row[1],
                    "event_type": row[2],
                    "faction": row[3],
                    "data": self._sanitize_data(data)
                })
            except: continue
        return sanitized

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Removes fields known to be non-deterministic or irrelevant for functional equality."""
        clean = data.copy()
        keys_to_ignore = ["timestamp", "duration_ms", "cpu_time", "trace_id", "parent_trace_id", "id"]
        for k in keys_to_ignore:
            clean.pop(k, None)
        return clean

    def _find_first_divergence(self, events_a: List[Dict], events_b: List[Dict]) -> Optional[Dict[str, Any]]:
        """Finds the first event that differs between the two streams."""
        limit = min(len(events_a), len(events_b))
        
        for i in range(limit):
            ev_a = events_a[i]
            ev_b = events_b[i]
            
            if ev_a != ev_b:
                return {
                    "index": i,
                    "turn": ev_a.get("turn"),
                    "event_a": ev_a,
                    "event_b": ev_b,
                    "reason": "Content Mismatch"
                }
        
        if len(events_a) != len(events_b):
            return {
                "index": limit,
                "turn": events_a[limit].get("turn") if len(events_a) > limit else events_b[limit].get("turn"),
                "event_a": events_a[limit] if len(events_a) > limit else None,
                "event_b": events_b[limit] if len(events_b) > limit else None,
                "reason": "Length Mismatch"
            }
            
        return None

    def _calculate_drift(self, universe: str, run_id_a: str, run_id_b: str) -> Dict[str, Any]:
        """Calculates the delta in final state metrics."""
        # Simple implementation: compare final faction stats
        stats_a = self._get_final_stats(universe, run_id_a)
        stats_b = self._get_final_stats(universe, run_id_b)
        
        drift = {}
        all_factions = set(stats_a.keys()) | set(stats_b.keys())
        
        for f in all_factions:
            sa = stats_a.get(f, {})
            sb = stats_b.get(f, {})
            
            drift[f] = {
                "planets": sb.get("planets_controlled", 0) - sa.get("planets_controlled", 0),
                "fleets": sb.get("fleets_count", 0) - sa.get("fleets_count", 0),
                "income": sb.get("gross_income", 0) - sa.get("gross_income", 0)
            }
            
        return drift

    def _get_final_stats(self, universe: str, run_id: str) -> Dict[str, Dict[str, Any]]:
        """Get the last known stats for each faction."""
        cursor = self.indexer.conn.cursor()
        query = """
            SELECT faction, planets_controlled, fleets_count, gross_income
            FROM factions
            WHERE universe = ? AND run_id = ?
            GROUP BY faction
            HAVING turn = MAX(turn)
        """
        cursor.execute(query, (universe, run_id))
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                "planets_controlled": row[1],
                "fleets_count": row[2],
                "gross_income": row[3]
            }
        return stats
