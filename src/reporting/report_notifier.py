from typing import Dict, Any, List
from src.reporting.notification_channels import NotificationManager, ReportWebhookChannel

class ReportNotifier:
    """
    Handles notifications for completed reports via configured channels.
    """
    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager

    def notify_completion(self, universe: str, run_id: str, paths: Dict[str, str], webhook_url: str = None):
        """
        Sends completion notification.
        """
        if not paths: return
        
        # 1. Ad-hoc Webhook (from API request)
        if webhook_url:
            channel = ReportWebhookChannel(webhook_url)
            channel.send_completion(universe, run_id, paths)
            
        # 2. Configured Channels (Future extension)
        # Currently we only promised ad-hoc webhook support in the plan for API usage
        # But we could reuse notification manager logic if we had a dedicated "Report Ready" alert type.
        # For now, we stick to the plan: "Notify completion after all formats are generated" via webhook.
