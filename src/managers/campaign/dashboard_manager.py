from typing import Optional, List, Any
import requests
from src.reporting.telemetry import EventCategory

class DashboardManager:
    """
    Manages communication with the live dashboard and telemetry attachment.
    """
    def __init__(self, telemetry_collector: Any, report_organizer: Any = None, logger: Any = None):
        self.telemetry = telemetry_collector
        self.report_organizer = report_organizer
        self.logger = logger

    def attach_dashboard(self, systems: List[Any], universe_name: str) -> bool:
        """Attempts to attach telemetry to the live dashboard if active."""
        try:
            from src.reporting.live_dashboard import state
            
            if hasattr(state, 'active') and state.active:
                batch_id = self.report_organizer.batch_id if self.report_organizer else "unknown"
                self.telemetry.set_batch_id(batch_id)
                state.attach_telemetry(self.telemetry)
                state.attach_galaxy(systems)
                if self.logger:
                    self.logger.info(f"Attached to Live Dashboard via Engine Hook (Batch: {batch_id})")
                
                # Send Test Event
                self.telemetry.log_event(EventCategory.SYSTEM, "dashboard_attached", {
                    "manager": "DashboardManager",
                    "universe": universe_name
                })
                return True
                
        except ImportError:
            pass

        # Fallback: Remote Attachment (Split Process)
        return self._attach_remote_dashboard(systems)

    def _attach_remote_dashboard(self, systems: List[Any]) -> bool:
        try:
            batch_id = self.report_organizer.batch_id if self.report_organizer else "unknown"
            self.telemetry.set_batch_id(batch_id)
            
            # Check availability
            resp = requests.get("http://localhost:5000/api/status", timeout=0.5)
            if resp.status_code == 200:
                 # 1. Enable Event Streaming
                 self.telemetry.enable_remote_streaming("http://localhost:5000/api/telemetry/ingest")
                 
                 # 2. Push Galaxy Topology
                 simple_systems = []
                 for s in systems:
                     conns = [n.name for n in s.connections] if hasattr(s, 'connections') else []
                     p_count = len(s.planets) if hasattr(s, 'planets') else 0
                     
                     simple_systems.append({
                         "name": s.name,
                         "x": s.x,
                         "y": s.y,
                         "owner": getattr(s, 'owner', 'Neutral'),
                         "connections": conns,
                         "total_planets": p_count,
                         "planets": [] 
                     })

                 requests.post("http://localhost:5000/api/galaxy/update", json={
                     "systems": simple_systems,
                     "batch_id": batch_id
                 }, timeout=2)
                 
                 if self.logger:
                     self.logger.info(f"Attached to Remote Dashboard via HTTP (Batch: {batch_id})")
                 return True
        except Exception:
            pass
            
        return False

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'telemetry' in state: del state['telemetry']
        if 'report_organizer' in state: del state['report_organizer']
        if 'logger' in state: del state['logger']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Dependencies must be re-injected by Orchestrator
        self.telemetry = None
        self.report_organizer = None
        self.logger = None
