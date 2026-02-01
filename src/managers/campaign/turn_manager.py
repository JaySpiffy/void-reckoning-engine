from typing import TYPE_CHECKING
from src.reporting.telemetry import EventCategory
from src.events.event import EventType

if TYPE_CHECKING:
    from src.managers.campaign.orchestrator import CampaignOrchestrator

class TurnManager:
    """
    Manages turn sequence and phase execution.
    Refactored from legacy TurnProcessor.
    """
    def __init__(self, orchestrator: 'CampaignOrchestrator'):
        # Circular dependency risk with Orchestrator? 
        # Orchestrator creates TurnManager.
        self.orchestrator = orchestrator
        self.current_phase: str = "PLANNING"
        
    def process_turn(self, fast_resolve: bool = False) -> None:
        """Execute a complete turn."""
        engine = self.orchestrator.engine # Access legacy engine state for now
        
        # 1. Global Cleanup
        engine.prune_empty_armies()
        if engine.logger:
            engine.logger.system(f"=== TURN {engine.turn_counter} GLOBAL PHASE ===")
            
        # 2. Cache Clearing
        engine.clear_turn_caches()
        if hasattr(engine, 'economy_manager'):
            engine.economy_manager.clear_caches()
            
        # 3. Reset Turn Flags
        self._reset_flags(engine)
        
        # 4. Preparing Turn Reporting
        if engine.report_organizer:
            self._prepare_reporting(engine)
            
        # 5. Start Turn Telemetry
        if getattr(engine, 'faction_reporter', None):
            engine.faction_reporter.start_turn(engine.turn_counter)
        
        # Event: Turn Started
        self.orchestrator.event_bus.publish(EventType.TURN_STARTED, {"turn": engine.turn_counter})
            
        # 6. Global Mechanics (Storms, Diplomacy, Combat Sanitization)
        if getattr(engine, 'storm_manager', None):
            engine.storm_manager.update_storms()

        if hasattr(engine.battle_manager, 'sanitize_state'):
            engine.battle_manager.sanitize_state(engine.fleets, engine.all_planets)

        if hasattr(engine, 'diplomacy') and engine.diplomacy:
            engine.diplomacy.process_turn()
            
        # 7. Execute Faction Phases
        # We rename process_turn in TurnProcessor to process_faction_turns to avoid name collision
        if hasattr(engine.turn_processor, 'process_faction_turns'):
             engine.turn_processor.process_faction_turns(fast_resolve)
        
        # 8. End Turn
        engine.turn_counter += 1
        
    def _reset_flags(self, engine):
        for f in engine.fleets:
            if hasattr(f, 'reset_turn_flags'): f.reset_turn_flags()
            
        for p in engine.all_planets:
            # Main Planet Armies
            for ag in p.armies:
                if hasattr(ag, 'reset_turn_flags'): ag.reset_turn_flags()
            
            # Province Armies (Total War Style)
            if hasattr(p, 'provinces'):
                for prov in p.provinces:
                    if hasattr(prov, 'armies'):
                        for ag in prov.armies:
                            if hasattr(ag, 'reset_turn_flags'): ag.reset_turn_flags()
                
        for faction in engine.get_all_factions():
            faction.reset_turn_stats()
            
        # Reset Battle Counter
        if hasattr(engine.battle_manager, 'battles_resolved_this_turn'):
            engine.battle_manager.battles_resolved_this_turn = 0
            engine.battle_manager.battles_resolved_this_turn_space = 0
            engine.battle_manager.battles_resolved_this_turn_ground = 0
            
    def _prepare_reporting(self, engine):
        f_names = [f.name for f in engine.get_all_factions()]
        turn_stats = {"factions": {}}
        for f_name in f_names:
            f_obj = engine.factions.get(f_name)
            if f_obj:
                req = getattr(f_obj, 'requisition', 0)
                fleets = [f for f in engine.fleets if f.faction == f_name and not f.is_destroyed]
                turn_stats["factions"][f_name] = {
                    "requisition": req,
                    "fleets": len(fleets),
                    "controlled_planets": len(engine.planets_by_faction.get(f_name, []))
                }
        engine.report_organizer.prepare_turn_folder(engine.turn_counter, factions=f_names, data=turn_stats)
        engine.battle_manager.log_dir = engine.report_organizer.get_turn_path(engine.turn_counter, "battles")
