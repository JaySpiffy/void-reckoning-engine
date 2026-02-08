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
