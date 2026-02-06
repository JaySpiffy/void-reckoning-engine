import time
import queue
import logging
import traceback
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PortalManager:
    """
    Handles cross-universe portal linking and fleet handoffs.
    """
    def __init__(self, runner: Any):
        self.runner = runner # MultiUniverseRunner instance

    def attempt_portal_linking(self):
        """
        Cross-references portal_registry to identify established links.
        """
        registry = self.runner.portal_registry
        universes = list(registry.keys())
        if len(universes) < 2:
            return

        established_links = []
        for i, u1_name in enumerate(universes):
            for u2_name in universes[i+1:]:
                u1_portals = registry[u1_name]
                u2_portals = registry[u2_name]
                
                for p1 in u1_portals:
                    meta = p1.get("metadata", {})
                    if meta.get("portal_dest_universe") == u2_name:
                        pid = meta.get("portal_id")
                        # Look for matching portal in U2
                        match = None
                        for p2 in u2_portals:
                            m2 = p2.get("metadata", {})
                            if m2.get("portal_id") == pid and m2.get("portal_dest_universe") == u1_name:
                                match = p2
                                break
                                
                        if match:
                            link_key = tuple(sorted([f"{u1_name}:{pid}", f"{u2_name}:{pid}"]))
                            if link_key not in established_links:
                                established_links.append(link_key)
                                print(f"  > [PORTAL_LINK] Established: {u1_name} <-> {u2_name} via {pid}")
                        else:
                             logger.warning(f"  > [PORTAL_LINK] Warning: Unmatched portal '{pid}' in {u1_name} pointing to {u2_name}. Check {u2_name} config.")

    def handle_portal_handoff(self, package: Dict[str, Any], src_universe: str, dest_universe: str, async_results: Dict) -> bool:
        """
        Orchestrates safe transfer of fleet between universe processes.
        """
        print(f"[PORTAL_HANDOFF] Processing transfer: {package.get('fleet_id')} | {src_universe} -> {dest_universe}")
        
        # 1. Validation
        known_universes = set(c['universe_name'] for c in self.runner.universe_configs)
        if dest_universe not in known_universes and dest_universe not in self.runner.progress_queues:
            logger.error(f"  > Error: Destination universe '{dest_universe}' not found.")
            return False
            
        if dest_universe in async_results and async_results[dest_universe].ready():
            logger.error(f"  > Error: Destination universe '{dest_universe}' has finished execution.")
            return False
            
        # 1.1 Validation (Schema)
        try:
            from src.utils.validation_schemas import FleetPackageSchema
            FleetPackageSchema(**package)
        except Exception as e:
            logger.error(f"  > [PORTAL] Outgoing Validation Failed: {e}")
            return False

        # 2. Source De-listing (Request Removal)
        if src_universe in self.runner.universe_queues:
            out_q = self.runner.universe_queues[src_universe]["outgoing"]
            cmd = {"action": "REMOVE_FLEET", "fleet_id": package["fleet_id"]}
            out_q.put(cmd)
            
            # Verify confirmation
            confirmed = False
            src_prog_q = self.runner.progress_queues.get(src_universe)
            msg_buffer = []

            max_retries = 3
            timeout_per_try = 2.0
            
            if src_prog_q:
                for attempt in range(max_retries):
                    start_wait = time.time()
                    while time.time() - start_wait < timeout_per_try:
                        try:
                            while not src_prog_q.empty():
                                msg = src_prog_q.get_nowait()
                                if len(msg) >= 3 and msg[2] == "FLEET_REMOVED" and len(msg) > 3 and msg[3] == package["fleet_id"]:
                                    confirmed = True
                                    break
                                else:
                                    msg_buffer.append(msg)
                            
                            if confirmed:
                                break
                            
                            time.sleep(0.1)
                        except queue.Empty:
                            time.sleep(0.1)

                    if confirmed:
                        break
                    
                    print(f"  > [PORTAL_HANDOFF] Retry {attempt+1}/{max_retries} waiting for source confirmation...")
                
                # Re-inject buffered messages
                for buffered_msg in msg_buffer:
                    src_prog_q.put(buffered_msg)
            
            if not confirmed:
                print(f"  > Error: Timed out waiting for FLEET_REMOVED confirmation from {src_universe} after {max_retries} attempts.")
                return False

            print(f"  > [PORTAL_HANDOFF] Source removal confirmed for fleet {package['fleet_id']}.")
            
            # Destination Validation (Re-check)
            if dest_universe not in self.runner.universe_queues or (dest_universe in async_results and async_results[dest_universe].ready()):
                 print(f"  > Error: Destination {dest_universe} became unavailable during handoff.")
                 # RECOVERY: Refund to Source
                 if src_universe in self.runner.universe_queues:
                     print(f"  > [RECOVERY] Refunding fleet {package['fleet_id']} to {src_universe} incoming queue.")
                     refund_q = self.runner.universe_queues[src_universe]["incoming"]
                     package["is_refund"] = True
                     refund_cmd = {
                        "action": "INJECT_FLEET",
                        "package": package,
                        "timestamp": time.time()
                     }
                     refund_q.put(refund_cmd)
                     return False
                 else:
                     print(f"  > CRITICAL ERROR: Could not refund fleet {package['fleet_id']} - Source queue lost.")
                     return False
            
        # 3. DNA Translation
        try:
             from src.core.universe_data import UniverseDataManager
             udm = UniverseDataManager.get_instance()
             udm.load_universe_data(dest_universe)
             
             translated_units = []
             raw_units = package.get("units", [])
             
             for u_dna in raw_units:
                 new_dna = udm.rehydrate_for_universe(u_dna, dest_universe)
                 translated_units.append(new_dna)
                 
             package["units"] = translated_units
             package["is_translated"] = True
             
        except Exception as e:
             print(f"  > Warning during translation: {e}")
             traceback.print_exc()

        # 4. Destination Injection
        if dest_universe in self.runner.universe_queues:
            in_q = self.runner.universe_queues[dest_universe]["incoming"]
            injection_cmd = {
                "action": "INJECT_FLEET",
                "package": package,
                "timestamp": time.time()
            }
            in_q.put(injection_cmd)
            print(f"  > [PORTAL_HANDOFF] Fleet injected into {dest_universe} queue.")
            return True
            
        print(f"  > Error: No queue found for {dest_universe}")
        return False
