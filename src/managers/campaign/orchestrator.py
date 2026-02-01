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
