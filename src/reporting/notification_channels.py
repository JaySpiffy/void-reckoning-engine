import os
import json
import logging
import smtplib
import requests
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from typing import Dict, List, Any, Optional
from src.reporting.alert_models import Alert, AlertSeverity

class NotificationChannel(ABC):
    def __init__(self, min_severity: str = "info"):
        self.min_severity = AlertSeverity.from_str(min_severity)

    def _should_send(self, alert: Alert) -> bool:
        levels = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.ERROR: 2,
            AlertSeverity.CRITICAL: 3
        }
        return levels.get(alert.severity, 0) >= levels.get(self.min_severity, 0)

    @abstractmethod
    def send(self, alert: Alert):
        pass

class ConsoleChannel(NotificationChannel):
    def send(self, alert: Alert):
        if not self._should_send(alert): return
        # ANSI colors
        colors = {
            AlertSeverity.INFO: "\033[94m", # Blue
            AlertSeverity.WARNING: "\033[93m", # Yellow
            AlertSeverity.ERROR: "\033[91m", # Red
            AlertSeverity.CRITICAL: "\033[41m\033[97m" # White on Red
        }
        reset = "\033[0m"
        color = colors.get(alert.severity, "")
        print(f"{color}[ALERT] [{alert.severity.value.upper()}] {alert.message}{reset}")

class FileChannel(NotificationChannel):
    def __init__(self, log_path: str, min_severity: str = "info"):
        super().__init__(min_severity)
        self.logger = logging.getLogger("AlertFileChannel")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def send(self, alert: Alert):
        if not self._should_send(alert): return
        self.logger.info(f"[{alert.rule_name}] {alert.message} - Context: {json.dumps(alert.context)}")

class EmailChannel(NotificationChannel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config.get('min_severity', 'error'))
        self.config = config

    def send(self, alert: Alert):
        if not self._should_send(alert): return
        try:
            msg = MIMEText(f"Alert Triggered:\n\nRule: {alert.rule_name}\nSeverity: {alert.severity.value}\nMessage: {alert.message}")
            msg['Subject'] = f"[{alert.severity.value.upper()}] Simulation Alert: {alert.rule_name}"
            msg['From'] = self.config.get('from_address')
            msg['To'] = ", ".join(self.config.get('to_addresses', []))

            with smtplib.SMTP(self.config.get('smtp_host'), self.config.get('smtp_port')) as server:
                if self.config.get('use_tls'):
                    server.starttls()
                # server.login(user, pass) - Credentials not in config for security
                server.send_message(msg)
        except Exception as e:
            print(f"[ALERT] Email failed: {e}")

class WebhookChannel(NotificationChannel):
    def __init__(self, endpoints: List[Dict[str, str]], min_severity: str = "warning"):
        super().__init__(min_severity)
        self.endpoints = endpoints

    def send(self, alert: Alert):
        if not self._should_send(alert): return
        for ep in self.endpoints:
            try:
                url = ep.get('url')
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "text": f"*[{alert.severity.value.upper()}]* {alert.rule_name}\n{alert.message}",
                    "severity": alert.severity.value
                }
                requests.post(url, json=payload, headers=headers, timeout=5)
            except Exception as e:
                print(f"[ALERT] Webhook failed: {e}")

class ReportWebhookChannel:
    """Dedicated channel for report completion notifications."""
    def __init__(self, url: str):
        self.url = url
        
    def send_completion(self, universe: str, run_id: str, paths: Dict[str, str]):
        from datetime import datetime
        payload = {
            "event": "report_generated",
            "universe": universe, 
            "run_id": run_id,
            "formats": list(paths.keys()),
            "download_urls": {k: f"/api/reports/download?path={v}" for k,v in paths.items()}, # Placeholder logic
            "timestamp": datetime.now().isoformat()
        }
        
        # Formatting for Discord/Slack detection
        if "discord.com" in self.url:
            discord_payload = {
                "embeds": [{
                    "title": "Report Generation Complete",
                    "description": f"Reports for {universe} (Run {run_id}) are ready.",
                    "fields": [{"name": fmt.upper(), "value": path} for fmt, path in paths.items()],
                    "color": 5763719
                }]
            }
            try:
                requests.post(self.url, json=discord_payload, timeout=5)
            except Exception as e:
                print(f"Discord webhook failed: {e}")
                
        elif "hooks.slack.com" in self.url:
             slack_payload = {
                 "text": f"Reports ready for {universe}",
                 "attachments": [{"fields": [{"title": k, "value": v} for k,v in paths.items()]}]
             }
             try:
                requests.post(self.url, json=slack_payload, timeout=5)
             except Exception as e:
                print(f"Slack webhook failed: {e}")
        else:
            # Generic
            try:
                requests.post(self.url, json=payload, timeout=5)
            except Exception as e:
                print(f"Webhook failed: {e}")

class NotificationManager:
    def __init__(self, config: Dict[str, Any]):
        self.channels: List[NotificationChannel] = []
        self.external_callback = None
        
        if config.get('console', {}).get('enabled', True):
            self.channels.append(ConsoleChannel(config.get('console', {}).get('min_severity', 'warning')))
            
        if config.get('file', {}).get('enabled', False):
            path = config['file'].get('path', 'logs/alerts.log')
            self.channels.append(FileChannel(path, config['file'].get('min_severity', 'info')))
            
        if config.get('webhook', {}).get('enabled', False):
            self.channels.append(WebhookChannel(config['webhook'].get('endpoints', []), config['webhook'].get('min_severity', 'warning')))

        if config.get('email', {}).get('enabled', False):
            self.channels.append(EmailChannel(config['email']))

    def set_external_callback(self, callback):
        self.external_callback = callback

    def send(self, alert: Alert):
        for channel in self.channels:
            channel.send(alert)
        if self.external_callback:
            try:
                self.external_callback(alert)
            except:
                pass
