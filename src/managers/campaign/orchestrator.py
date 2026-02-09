from typing import Dict, Any, Optional
from src.managers.campaign.campaign_manager import CampaignManager
from src.managers.campaign.turn_manager import TurnManager
from src.managers.campaign.victory_manager import VictoryManager
from src.managers.campaign.milestone_manager import MilestoneManager
from src.managers.campaign.dashboard_manager import DashboardManager
from src.core.service_locator import ServiceLocator
from src.events.event_bus import EventBus
from src.events.subscribers.telemetry_subscriber import TelemetrySubscriber
from src.events.subscribers.dashboard_subscriber import DashboardSubscriber

class CampaignOrchestrator:
    """
    Lightweight orchestrator that coordinates domain managers.
    Replaces the monolithic CampaignEngine progressively.
    """
    def __init__(self, engine: Any):
        self.engine = engine
        self._config = engine.config.raw_config if hasattr(engine, 'config') else {}
        
        # Initialize Event System
        self.event_bus = EventBus.get_instance()
        
        # Initialize Command System (Phase 7)
        from src.commands.command_bus import CommandBus
        self.command_bus = CommandBus()
        
        # Initialize Managers
        self.campaign_manager = CampaignManager(self._config)
        self.turn_manager = TurnManager(self)
        self.victory_manager = VictoryManager(engine)
        self.milestone_manager = MilestoneManager(engine.telemetry)
        self.dashboard_manager = DashboardManager(engine.telemetry, engine.report_organizer, engine.logger)
        
        # Initialize Subscribers
        # We hook them up to the EventBus we just initialized
        self.telemetry_subscriber = TelemetrySubscriber(self.event_bus, engine.telemetry)
        self.dashboard_subscriber = DashboardSubscriber(self.event_bus, self.dashboard_manager)
        
        # Sync state references (Transition Phase)
        # self.campaign_manager.factions = engine.factions (Property copy/reference)
        
    def process_turn(self, fast_resolve: bool = False) -> None:
        """Delegates to TurnManager"""
        # [HOOK] Update Managers with latest engine state if needed
        return self.turn_manager.process_turn(fast_resolve)
    
    def check_victory(self) -> Optional[str]:
        """Delegates to VictoryManager"""
        return self.victory_manager.check_victory()
        
    def log_victory_progress(self):
        """Delegates to VictoryManager"""
        self.victory_manager.log_victory_progress()
        
    def log_milestone(self, key: str, turn: int, data: Dict[str, Any] = None):
        self.milestone_manager.record_milestone(key, turn, data)

    def attach_dashboard(self) -> bool:
        # Use Engine state for galaxy systems
        return self.dashboard_manager.attach_dashboard(self.engine.systems, self.engine.universe_config.name)

    def __getstate__(self):
        """Custom pickling to exclude event system components."""
        state = self.__dict__.copy()
        # Exclude unpicklable components
        if 'event_bus' in state: del state['event_bus']
        if 'command_bus' in state: del state['command_bus']
        if 'telemetry_subscriber' in state: del state['telemetry_subscriber']
        if 'dashboard_subscriber' in state: del state['dashboard_subscriber']
        return state

    def __setstate__(self, state):
        """Restore state and re-initialize components."""
        self.__dict__.update(state)
        
        # Re-init Event System
        self.event_bus = EventBus.get_instance()
        
        # Re-init Command System
        from src.commands.command_bus import CommandBus
        self.command_bus = CommandBus()
        
        # Re-init Subscribers
        from src.events.subscribers.telemetry_subscriber import TelemetrySubscriber
        from src.events.subscribers.dashboard_subscriber import DashboardSubscriber
        
        # Note: self.engine should be restored by pickle cycle handling
        if hasattr(self, 'engine') and self.engine:
            if hasattr(self.engine, 'telemetry') and self.engine.telemetry:
                self.telemetry_subscriber = TelemetrySubscriber(self.event_bus, self.engine.telemetry)
            if hasattr(self.engine, 'logger'): # DashboardManager uses logger/report_organizer
                self.dashboard_subscriber = DashboardSubscriber(self.event_bus, self.dashboard_manager)

    def reinit_dependencies(self):
        """Re-injects dependencies after engine services are restored."""
        if not self.engine: return
        
        # 1. Update DashboardManager
        if self.dashboard_manager:
            if hasattr(self.engine, 'telemetry'):
                self.dashboard_manager.telemetry = self.engine.telemetry
            if hasattr(self.engine, 'report_organizer'):
                self.dashboard_manager.report_organizer = self.engine.report_organizer
            if hasattr(self.engine, 'logger'):
                self.dashboard_manager.logger = self.engine.logger
        
        # 2. Update Subscribers with real telemetry
        from src.events.subscribers.telemetry_subscriber import TelemetrySubscriber
        from src.events.subscribers.dashboard_subscriber import DashboardSubscriber
        
        if hasattr(self.engine, 'telemetry') and self.engine.telemetry:
            self.telemetry_subscriber = TelemetrySubscriber(self.event_bus, self.engine.telemetry)
            
        # Re-attach DashboardSubscriber
        if hasattr(self.engine, 'logger'):
             self.dashboard_subscriber = DashboardSubscriber(self.event_bus, self.dashboard_manager)
