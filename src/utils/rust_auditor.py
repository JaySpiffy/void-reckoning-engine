import json
import logging
from typing import Dict, Any, List, Optional
try:
    from void_reckoning_bridge import RustAuditor as _RustAuditor
except ImportError:
    _RustAuditor = None

class RustAuditorWrapper:
    def __init__(self):
        self.logger = logging.getLogger("RustAuditor")
        if _RustAuditor:
            try:
                self._auditor = _RustAuditor()
                self._initialized = False
                self.logger.info("RustAuditor bridge loaded successfully.")
            except Exception as e:
                self.logger.error(f"Failed to instantiate RustAuditor: {e}")
                self._auditor = None
        else:
            self.logger.warning("void_reckoning_bridge not found. RustAuditor disabled.")
            self._auditor = None

    def load_registry(self, registry_type: str, data: Dict[str, Any]) -> bool:
        if not self._auditor:
            return False
        try:
            json_data = json.dumps(data)
            self._auditor.load_registry(registry_type, json_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to load registry {registry_type}: {e}")
            return False

    def initialize(self) -> bool:
        if not self._auditor:
            return False
        try:
            self._auditor.initialize()
            self._event_log = self._auditor.enable_event_logging()
            self._initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize RustAuditor: {e}")
            return False

    def validate_entity(self, entity_id: str, entity_type: str, data: Dict[str, Any], universe_id: str, turn: int) -> List[Dict[str, Any]]:
        if not self._auditor or not self._initialized:
            return []
        try:
            json_data = json.dumps(data)
            result_json = self._auditor.validate_entity(entity_id, entity_type, json_data, universe_id, turn)
            return json.loads(result_json)
        except Exception as e:
            self.logger.error(f"Validation failed for {entity_id}: {e}")
            return []
    def flush_logs(self, telemetry_logger):
        """
        Retrieves events from Rust and flushes them to the Python telemetry logger.
        """
        if not self._auditor or not hasattr(self, '_event_log') or not self._event_log:
            return

        try:
            events = self._event_log.get_all()
            if not events: return
            
            from src.reporting.telemetry import EventCategory
            
            for evt in events:
                # Map Rust Severity to Telemetry Level
                cat = EventCategory.SYSTEM
                if evt.category == "Auditor": cat = EventCategory.SYSTEM
                
                telemetry_logger.log_event(
                    cat, 
                    "auditor_event", 
                    {
                        "severity": evt.severity,
                        "rule": getattr(evt, 'rule_name', 'unknown'),
                        "message": evt.message,
                        "context": evt.context.trace_id if evt.context else None
                    }
                )
                
            self._event_log.clear() 
            
        except Exception as e:
            self.logger.error(f"Failed to flush logs: {e}")

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'logger' in state: del state['logger']
        if '_auditor' in state: del state['_auditor']
        if '_event_log' in state: del state['_event_log']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Restore logger
        self.logger = logging.getLogger("RustAuditor")
        # Restore Auditor if available
        if _RustAuditor:
            try:
                self._auditor = _RustAuditor()
                # Attempt to restore state? 
                # Auditor state is complex. For now, we re-init as new.
                # If specialized state restoration is needed, we'd need serialization on Rust side.
                if state.get('_initialized', False):
                     self._auditor.initialize()
                     self._event_log = self._auditor.enable_event_logging()
            except Exception as e:
                self.logger.error(f"Failed to restore RustAuditor: {e}")
                self._auditor = None
                self._initialized = False
        else:
            self._auditor = None
