from typing import Dict, Any, List, Optional, TYPE_CHECKING
from queue import Empty
from src.managers.fleet_queue_manager import FleetQueueManager
from src.utils.game_logging import GameLogger, LogCategory
from src.config import logging_config

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.models.planet import Planet

class PortalManager:
    """
    Manages inter-universe fleet transfers via portal queues.
    Handles fleet injection, removal, and validation of cross-universe transfers.
    Delegated from CampaignEngine.
    """
    
    def __init__(self, engine: 'CampaignEngine'):
        self.engine = engine
        self.logger = getattr(engine, 'logger', None)

    def process_queue_commands(self, run_id: int, turn: int) -> None:
        """
        Polls incoming/outgoing fleet queues via FleetQueueManager.
        Handles both outgoing instructions (REMOVE_FLEET) and incoming arrivals (INJECT_FLEET).
        """
        queue_mgr = FleetQueueManager.get_instance()
        
        # 1. Outgoing (Removal Instructions)
        while True:
            try:
                if not queue_mgr.outgoing_q:
                    break
                    
                cmd = queue_mgr.outgoing_q.get_nowait()
                if cmd.get("action") == "REMOVE_FLEET":
                    fid = cmd.get("fleet_id")
                    target = next((f for f in self.engine.fleets if f.id == fid), None)
                    if target:
                        self.engine.unregister_fleet(target)
                        target.is_destroyed = True
                        
                        # Confirm Removal via Progress Queue
                        queue_mgr.push_progress((run_id, turn, "FLEET_REMOVED", fid))
                        
                        if self.logger:
                            self.logger.debug(f"[PORTAL] Processed removal for fleet {fid}", category=LogCategory.CAMPAIGN)
            except Empty:
                break
            except Exception as e:
                if self.logger: 
                    self.logger.error(f"Error processing outgoing fleet queue: {e}", category=LogCategory.CAMPAIGN)
                break

        # 2. Incoming (Arrivals)
        while True:
            try:
                cmd = queue_mgr.pop_incoming()
                if not cmd:
                    break
                    
                # Validate Command
                from src.utils.validation_schemas import validate_portal_command
                valid_cmd = validate_portal_command(cmd)
                
                if valid_cmd and valid_cmd.action == "INJECT_FLEET":
                    self.handle_fleet_injection(valid_cmd.model_dump())
            except Exception as e:
                if self.logger: 
                    self.logger.error(f"Error processing incoming fleet queue: {e}", category=LogCategory.CAMPAIGN)
                break

    def handle_fleet_injection(self, cmd: Dict[str, Any]) -> None:
        """
        Inject a fleet from another universe into this campaign.
        Handles faction registration, location selection, and unit hydration.
        """
        from src.models.faction import Faction
        from src.models.unit import Unit
        
        pkg = cmd.get("package", {})
        fid = pkg.get("fleet_id")
        faction_name = pkg.get("faction", "Unknown")
        coords = pkg.get("portal_exit_coords")
        
        # Register Faction if New (Invader)
        if faction_name not in self.engine.factions:
            self.engine.factions[faction_name] = Faction(faction_name)
            # Initialize basic cache entry for visibility
            if hasattr(self.engine, '_visibility_cache'):
                 self.engine._visibility_cache[faction_name] = set()
            if self.logger: 
                self.logger.info(f"[PORTAL] Registered new invading faction: {faction_name}", category=LogCategory.CAMPAIGN)

        # Location Strategy: Closest Node or First Planet
        destination = self.engine.all_planets[0] if self.engine.all_planets else None
        if coords and destination:
            # Find closest system (Manhattan distance for speed)
            cx, cy = coords
            best_dist = float('inf')
            for p in self.engine.all_planets:
                if hasattr(p, 'system'):
                    dist = abs(p.system.x - cx) + abs(p.system.y - cy)
                    if dist < best_dist:
                        best_dist = dist
                        destination = p
        
        if destination:
            # Create Empty Fleet Shell
            new_fleet = self.engine.create_fleet(faction_name, destination, [], fid=fid)
            
            # Hydrate Units
            raw_units = pkg.get("units", [])
            for u_dna in raw_units:
                try:
                    # Validate Unit DNA
                    from src.utils.validation_schemas import validate_unit_dna
                    if not validate_unit_dna(u_dna):
                        if self.logger: 
                            self.logger.warning(f"[PORTAL] Skipping invalid unit DNA in fleet {fid}", category=LogCategory.CAMPAIGN)
                        continue
                        
                    unit = Unit.deserialize_dna(u_dna)
                    new_fleet.add_unit(unit)
                except Exception as ue:
                    if self.logger: 
                        self.logger.warning(f"Failed to deserialize unit in portal fleet: {ue}", category=LogCategory.CAMPAIGN)
            
            self.engine.register_fleet(new_fleet)
            
            # [PHASE 6] Portal Injection Trace
            if logging_config.LOGGING_FEATURES.get('portal_wormhole_usage_tracking', False):
                if hasattr(self.logger, 'movement'):
                    trace_msg = {
                        "event_type": "portal_injection_event",
                        "fleet_id": fid,
                        "faction": faction_name,
                        "destination": destination.name,
                        "unit_count": len(new_fleet.units),
                        "turn": self.engine.turn_counter
                    }
                    self.logger.movement(f"[PORTAL] Injected fleet {fid} at {destination.name}", extra=trace_msg)

            if self.logger: 
                self.logger.info(f"[PORTAL] Injected portal fleet {fid} at {destination.name} with {len(new_fleet.units)} units.", category=LogCategory.CAMPAIGN)
