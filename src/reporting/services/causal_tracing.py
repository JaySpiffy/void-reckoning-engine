import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class CausalTracingService:
    """
    Service for reconstructing causal chains from the ReportIndexer database.
    This enables "Why did this happen?" queries in the TUI without keeping
    the entire graph in memory.
    """
    def __init__(self, indexer):
        self.indexer = indexer

    def get_causal_chain(self, universe: str, run_id: str, span_id: str) -> List[Dict[str, Any]]:
        """
        Reconstructs the lineage of an event from Target -> Root.
        Returns a list of event dictionaries in chronological order [Root ... Target].
        """
        chain = []
        current_id = span_id
        
        # Guard against infinite loops or extremely deep traces
        max_depth = 50 
        depth = 0
        
        while current_id and depth < max_depth:
            event = self._fetch_event_by_span(universe, run_id, current_id)
            if not event:
                break
                
            chain.append(event)
            
            # Extract parent_id from correlation context
            context = event.get('context', {})
            current_id = context.get('parent_id')
            depth += 1
            
        # Reverse to be chronological [Root -> ... -> Target]
        chain.reverse()
        return chain

    def _fetch_event_by_span(self, universe: str, run_id: str, span_id: str) -> Optional[Dict[str, Any]]:
        """Queries the SQL index for a specific span_id."""
        try:
            cursor = self.indexer.conn.cursor()
            # We search in data_json where span_id matches
            # The schema usually has data_json as a string field
            query = """
                SELECT turn, category, event_type, message, data_json 
                FROM events 
                WHERE universe = ? AND run_id = ? 
                AND json_extract(data_json, '$.context.span_id') = ?
                LIMIT 1
            """
            cursor.execute(query, (universe, run_id, span_id))
            row = cursor.fetchone()
            
            if row:
                turn, category, event_type, message, data_json = row
                event_data = json.loads(data_json)
                return event_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to fetch event {span_id}: {e}")
            return None

    def get_impact_analysis(self, universe: str, run_id: str, span_id: str) -> List[Dict[str, Any]]:
        """
        Reconstructs the downstream consequences (BFS).
        """
        consequences = []
        queue = [span_id]
        visited = {span_id}
        
        while queue:
            current_id = queue.pop(0)
            children = self._fetch_children(universe, run_id, current_id)
            for child in children:
                child_span = child.get('context', {}).get('span_id')
                if child_span and child_span not in visited:
                    visited.add(child_span)
                    consequences.append(child)
                    queue.append(child_span)
                    
        return consequences

    def _fetch_children(self, universe: str, run_id: str, parent_span_id: str) -> List[Dict[str, Any]]:
        """Finds all events that claim this span_id as their parent."""
        try:
            cursor = self.indexer.conn.cursor()
            query = """
                SELECT data_json 
                FROM events 
                WHERE universe = ? AND run_id = ? 
                AND json_extract(data_json, '$.context.parent_id') = ?
            """
            cursor.execute(query, (universe, run_id, parent_span_id))
            rows = cursor.fetchall()
            
            return [json.loads(r[0]) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch children for {parent_span_id}: {e}")
            return []
