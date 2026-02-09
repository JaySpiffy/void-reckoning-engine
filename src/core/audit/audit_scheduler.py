
import logging
from typing import List, Dict, Any, Optional, Set
from src.utils.rust_auditor import RustAuditorWrapper

class AuditScheduler:
    """
    Manages the periodic validation of game entities against Rust-based consistency rules.
    Runs in small batches per tick to minimize performance impact.
    """
    def __init__(self, auditor: RustAuditorWrapper):
        self.auditor = auditor
        self.logger = logging.getLogger("AuditScheduler")
        
        # Scheduling
        self.entities_to_audit: List[Any] = []
        self._entity_set: Set[int] = set() # For O(1) existence checks
        self.current_index = 0
        self.batch_size = 50
        
        # Stats
        self.audits_performed = 0
        self.violations_found = 0
        
    def register_entity(self, entity: Any) -> None:
        """
        Registers an entity for periodic auditing.
        Entity must have 'id' and 'to_dict()' or similar serialization method.
        """
        eid = id(entity)
        if eid not in self._entity_set:
            self.entities_to_audit.append(entity)
            self._entity_set.add(eid)
            
    def unregister_entity(self, entity: Any) -> None:
        """Removes an entity from the audit cycle (e.g. on death)."""
        eid = id(entity)
        if eid in self._entity_set:
            self._entity_set.remove(eid)
            # Lazy removal: We'll filter it out during iteration or rebuild list occasionally
            # For now, simplistic remove is O(N), so we might just skip it during run_audit_cycle
            # if we can detect it's dead/invalid.
            if entity in self.entities_to_audit:
                 self.entities_to_audit.remove(entity)

    def run_audit_cycle(self, universe_id: str, turn: int) -> List[Dict[str, Any]]:
        """
        Audits the next batch of entities.
        Returns a list of violation reports.
        """
        if not self.entities_to_audit:
            return []
            
        violations = []
        count = 0
        
        # Circular buffer iteration
        while count < self.batch_size:
            if not self.entities_to_audit: break
            
            # Wrap around
            if self.current_index >= len(self.entities_to_audit):
                self.current_index = 0
                
            entity = self.entities_to_audit[self.current_index]
            self.current_index += 1
            count += 1
            
            if not entity: continue
            
            # Skip destroyed/dead entities (lazy cleanup)
            if hasattr(entity, 'is_alive') and not entity.is_alive():
                 # Cleanup O(1) if we were using a different structure, but here we just skip
                 continue
            if hasattr(entity, 'is_destroyed') and entity.is_destroyed:
                 continue
                 
            # Prepare Data
            try:
                # Duck typing for serialization
                data = {}
                e_type = "Entity"
                # Robust ID extraction
                e_id = str(getattr(entity, 'id', getattr(entity, 'name', 'unknown')))
                
                # --- TYPE DETECTION ---
                if hasattr(entity, 'units') and hasattr(entity, 'travel_progress'):
                     e_type = "Fleet"
                elif hasattr(entity, 'is_ship') and entity.is_ship():
                    e_type = "Ship"
                elif hasattr(entity, 'is_building'): # heuristic
                    e_type = "Building"
                elif hasattr(entity, 'planet_class') or (hasattr(entity, 'orbit_index') and hasattr(entity, 'system')):
                    e_type = "Planet"
                elif hasattr(entity, 'requisition') and hasattr(entity, 'technologies'):
                    e_type = "Faction"
                elif hasattr(entity, 'faction'): 
                    # Fallback for generic objects with faction (e.g. Unit, or misidentified Fleet)
                    # If we reached here, it's NOT a Fleet (checked above)
                    if hasattr(entity, 'unit_class'):
                        e_type = "Unit"
                    else:
                        e_type = "Entity"
                elif hasattr(entity, 'owner') and hasattr(entity, 'planet_class'):
                    e_type = "Planet"

                # Serialization Strategy
                if hasattr(entity, 'to_dict'):
                    try:
                        data = entity.to_dict()
                    except:
                        data = entity.__dict__.copy()
                elif hasattr(entity, '__dict__'):
                    data = entity.__dict__.copy()
                
                # Sanitize Data (Deep)
                safe_data = self._sanitize(data)

                reports = self.auditor.validate_entity(e_id, e_type, safe_data, universe_id, turn)
                     
                if reports:
                     self.violations_found += len(reports)
                     for r in reports:
                         r['entity_id'] = e_id
                         r['entity_type'] = e_type
                         violations.append(r)
                         
                     self.logger.warning(f"Audit Violations for {e_type} {e_id}: {reports}")
                         
            except Exception as e:
                self.logger.error(f"Error auditing entity {getattr(entity, 'id', 'unknown')}: {e}")
                
        self.audits_performed += count
        return violations

    def _sanitize(self, data: Any, depth: int = 0) -> Any:
        """
        Recursively sanitizes data to ensure JSON compatibility.
        Limits depth to prevent infinite recursion.
        """
        if depth > 2:
            return str(data)
            
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, dict):
            return {k: self._sanitize(v, depth + 1) for k, v in data.items() if isinstance(k, str)}
        elif isinstance(data, (list, tuple)):
            return [self._sanitize(v, depth + 1) for v in data]
        elif hasattr(data, 'to_dict'):
             return self._sanitize(data.to_dict(), depth + 1)
        else:
            return str(data)
                         

