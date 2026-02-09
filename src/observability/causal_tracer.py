
import json
import os
import glob
from typing import List, Dict, Any, Optional
from src.observability.graph_store import CausalGraph

class CausalTracer:
    """
    Ingests telemetry logs (NDJSON) and builds a Causal Graph.
    Enables 'Why did this happen?' analysis.
    """
    def __init__(self):
        self.graph = CausalGraph()

    def load_events(self, log_dir: str):
        """
        Parses all event logs in the directory and populates the graph.
        """
        # Find all event.json files (recursively or pattern)
        pattern = os.path.join(log_dir, "**", "events.json*")
        # Support both new daily logs and monolithic
        files = glob.glob(pattern, recursive=True)
        
        # Also check standard report structure
        if not files:
            files = glob.glob(os.path.join(log_dir, "*.json"))

        print(f"Loading events from {len(files)} files found in {log_dir}...")

        for file_path in files:
            self._parse_file(file_path)

    def _parse_file(self, file_path: str):
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        event = json.loads(line)
                        self._process_event(event)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def _process_event(self, event: Dict[str, Any]):
        """
        Extracts correlation IDs and links events in the graph.
        """
        # Identify Event ID
        # Telemetry events usually have 'trace_id' in 'context' or 'details'
        
        details = event.get("details", {})
        context = event.get("context", {}) # From Rust bridge usually
        
        # Flatten source of truth
        trace_id = details.get("trace_id") or context.get("trace_id")
        span_id = details.get("span_id") or context.get("span_id")
        
        # If no trace_id, we might rely on 'id' if added by logger
        if not trace_id: 
            return

        # Identify Parent
        parent_trace_id = details.get("parent_trace_id") or context.get("parent_id")
        
        # Construct unique node ID: trace_id + span_id if available, else just trace_id
        # But for decision chains, trace_id is usually the 'action' ID.
        node_id = trace_id
        
        payload = {
            "event_type": event.get("event_type", "unknown"),
            "timestamp": event.get("timestamp"),
            "trace_id": trace_id,
            "actor": event.get("faction")
        }
        
        parents = []
        if parent_trace_id:
            parents.append(parent_trace_id)
            
        self.graph.add_event(node_id, payload, parents)

    def get_root_cause(self, event_id: str) -> List[Dict[str, Any]]:
        """
        Traces back to the earliest event in the chain.
        """
        chain = self.graph.trace_backward(event_id, depth_limit=100)
        return chain[::-1] # Chronological

    def explain_event(self, event_id: str) -> str:
        """
        Returns a human-readable explanation of the causality chain.
        """
        chain = self.get_root_cause(event_id)
        if not chain:
            return f"No causal history found for event {event_id}"
            
        story = ["Causal Trace:"]
        for node in chain:
            ts = node.get("timestamp", "?")
            etype = node.get("type", "Event")
            actor = node.get("actor", "System")
            story.append(f"[{ts}] {actor} performed {etype} (ID: {node['id'][:8]})")
            
        return "\n  |\n  v\n".join(story)
