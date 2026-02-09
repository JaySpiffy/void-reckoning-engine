from typing import Dict, List, Any, Optional, Set
import threading

class CausalGraph:
    """
    Directed Acyclic Graph (DAG) representing the lineage of simulation events.
    Optimized for in-memory storage and traversal.
    """
    def __init__(self):
        # Adjacency list: event_id -> list of child_event_ids
        self._adjacency: Dict[str, List[str]] = {}
        # Reverse adjacency: event_id -> list of parent_event_ids (for backward trace)
        self._parents: Dict[str, List[str]] = {}
        # Event storage: event_id -> event_payload (minimal)
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def add_event(self, event_id: str, payload: Dict[str, Any], parent_ids: List[str]):
        """
        Adds an event to the graph and links it to its parents.
        """
        with self._lock:
            if event_id in self._nodes:
                return # Idempotent

            # Store minimal payload to save memory
            self._nodes[event_id] = {
                "type": payload.get("event_type", "unknown"),
                "timestamp": payload.get("timestamp"),
                "trace_id": payload.get("trace_id"),
                "actor": payload.get("actor")
            }

            self._adjacency.setdefault(event_id, [])
            self._parents.setdefault(event_id, [])

            for pid in parent_ids:
                if pid:
                    self._parents[event_id].append(pid)
                    self._adjacency.setdefault(pid, []).append(event_id)

    def get_children(self, event_id: str) -> List[str]:
        """Returns direct consequences of an event."""
        with self._lock:
            return list(self._adjacency.get(event_id, []))

    def get_parents(self, event_id: str) -> List[str]:
        """Returns direct causes of an event."""
        with self._lock:
            return list(self._parents.get(event_id, []))

    def get_node(self, event_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._nodes.get(event_id)

    def trace_backward(self, event_id: str, depth_limit: int = 10) -> List[Dict[str, Any]]:
        """
        Returns the lineage chain leading to this event.
        BFS/DFS backward.
        """
        chain = []
        queue = [(event_id, 0)]
        visited = set()

        with self._lock:
            while queue:
                current_id, depth = queue.pop(0)
                if current_id in visited or depth > depth_limit:
                    continue
                visited.add(current_id)

                node = self.get_node(current_id)
                if node:
                    # Add current node info plus its ID
                    info = node.copy()
                    info['id'] = current_id
                    chain.append(info)

                for pid in self.get_parents(current_id):
                    queue.append((pid, depth + 1))
        
        return chain

    def trace_forward(self, event_id: str, depth_limit: int = 10) -> List[Dict[str, Any]]:
        """
        Returns the cascade of consequences from this event.
        """
        chain = []
        queue = [(event_id, 0)]
        visited = set()

        with self._lock:
            while queue:
                current_id, depth = queue.pop(0)
                if current_id in visited or depth > depth_limit:
                    continue
                visited.add(current_id)

                node = self.get_node(current_id)
                if node:
                    info = node.copy()
                    info['id'] = current_id
                    chain.append(info)

                for cid in self.get_children(current_id):
                    queue.append((cid, depth + 1))
        
        return chain
