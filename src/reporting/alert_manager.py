import yaml
import threading
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.reporting.alert_models import Alert, AlertSeverity, AlertHistory, ThresholdRule, PatternRule

class AlertRuleEngine:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.threshold_rules: List[ThresholdRule] = []
        self.pattern_rules: List[PatternRule] = []
        self.notifications_config = {}
        self.load_rules()

    def load_rules(self):
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.notifications_config = config.get('notifications', {})
            
            self.threshold_rules = []
            for name, r in config.get('thresholds', {}).items():
                if not r.get('enabled', True): continue
                self.threshold_rules.append(ThresholdRule(
                    name=name,
                    enabled=True,
                    severity=AlertSeverity.from_str(r.get('severity', 'warning')),
                    message_template=r.get('message', ''),
                    config=r,
                    metric=r.get('metric', ''),
                    operator=r.get('operator', 'greater_than'),
                    value=r.get('value'),
                    duration_turns=r.get('duration_turns', 1)
                ))

            self.pattern_rules = []
            for name, r in config.get('patterns', {}).items():
                if not r.get('enabled', True): continue
                self.pattern_rules.append(PatternRule(
                    name=name,
                    enabled=True,
                    severity=AlertSeverity.from_str(r.get('severity', 'info')),
                    message_template=r.get('message', ''),
                    config=r,
                    event_type=r.get('event_type', ''),
                    pattern_type=r.get('pattern', ''),
                    window_turns=r.get('window_turns', 10),
                    threshold_count=r.get('threshold_count', 3),
                    metric=r.get('metric'),
                    threshold=r.get('threshold'),
                    growth_rate_mb_per_turn=r.get('growth_rate_mb_per_turn')
                ))
            print(f"[ALERT] Loaded {len(self.threshold_rules)} thresholds and {len(self.pattern_rules)} patterns.")
        except Exception as e:
            print(f"[ALERT] Failed to load rules: {e}")

class ThresholdMonitor:
    def __init__(self):
        self.consecutive_matches: Dict[str, int] = {} # rule_name -> count

    def evaluate(self, rule: ThresholdRule, current_value: Any, context: Dict[str, Any]) -> bool:
        op = rule.operator
        val = rule.value
        
        match = False
        try:
            if op == "less_than": match = float(current_value) < float(val)
            elif op == "greater_than": match = float(current_value) > float(val)
            elif op == "equals": match = str(current_value) == str(val)
        except (ValueError, TypeError):
            match = False
        
        if match:
            count = self.consecutive_matches.get(rule.name, 0) + 1
            self.consecutive_matches[rule.name] = count
            if count >= rule.duration_turns:
                return True
        else:
            self.consecutive_matches[rule.name] = 0
        return False

class PatternDetector:
    def __init__(self):
        self.event_windows: Dict[str, List[Dict[str, Any]]] = {} # rule_name -> events

    def process_event(self, rule: PatternRule, event: Dict[str, Any], manager: 'AlertManager') -> bool:
        if rule.name not in self.event_windows:
            self.event_windows[rule.name] = []
        
        window = self.event_windows[rule.name]
        window.append(event)
        
        # Prune old events (simplified turn-based window)
        current_turn = event.get('turn', 0)
        self.event_windows[rule.name] = [e for e in window if current_turn - e.get('turn', 0) <= rule.window_turns]
        window = self.event_windows[rule.name]

        if rule.pattern_type == "same_error_message":
            msg = event.get('message')
            count = sum(1 for e in window if e.get('message') == msg)
            if count >= rule.threshold_count:
                manager.trigger_alert(rule.severity, rule.name, rule.message_template.format(error_message=msg), event)
                return True
        elif rule.pattern_type == "operation_stuck":
            duration = event.get('data', {}).get(rule.metric, 0) if rule.metric else event.get('duration_ms', 0)
            if duration >= (rule.threshold or 30000):
                op = event.get('data', {}).get('operation', 'unknown')
                manager.trigger_alert(rule.severity, rule.name, rule.message_template.format(operation=op), event)
                return True
        elif rule.pattern_type == "memory_growth":
            # Identify growth per turn
            if len(window) < 2: return False
            metric = rule.metric or "memory_usage_mb"
            try:
                first = float(window[0].get('data', {}).get(metric, 0))
                last = float(window[-1].get('data', {}).get(metric, 0))
                turns = int(window[-1].get('turn', 0)) - int(window[0].get('turn', 0))
                if turns >= 1:
                    rate = (last - first) / turns
                    if rate >= (rule.growth_rate_mb_per_turn or 50):
                        manager.trigger_alert(rule.severity, rule.name, rule.message_template.format(growth_rate=round(rate, 2)), event)
                        return True
            except (ValueError, TypeError):
                pass
        elif rule.pattern_type == "consecutive_match":
            # Check if recent N events match criteria
            if len(window) < rule.threshold_count: return False
            
            # Check last N events
            subset = window[-rule.threshold_count:]
            metric = rule.metric
            if not metric: return False
            
            try:
                op = rule.config.get('operator', 'less_than')
                matches = 0
                for e in subset:
                    val = e.get('data', {}).get(metric)
                    if val is None: break
                    
                    is_match = False
                    if op == "less_than": is_match = float(val) < float(rule.threshold)
                    elif op == "greater_than": is_match = float(val) > float(rule.threshold)
                    elif op == "equals": is_match = str(val) == str(rule.threshold)
                    
                    if is_match: matches += 1
                    else: break
                
                if matches >= rule.threshold_count:
                    formatted_msg = rule.message_template.format(faction=event.get('faction', 'Unknown'), threshold_count=rule.threshold_count)
                    manager.trigger_alert(rule.severity, rule.name, formatted_msg, event)
                    return True
            except (ValueError, TypeError):
                pass
        return False

class AlertManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(AlertManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config/alert_rules.yaml"):
        if self._initialized: return
        self.rule_engine = AlertRuleEngine(config_path)
        self.threshold_monitor = ThresholdMonitor()
        self.pattern_detector = PatternDetector()
        self.history = AlertHistory()
        
        from src.reporting.notification_channels import NotificationManager
        self.notification_manager = NotificationManager(self.rule_engine.notifications_config)
        
        self.active = True
        self._initialized = True
        
    def trigger_alert(self, severity: AlertSeverity, rule_name: str, message: str, context: Dict[str, Any]):
        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            severity=severity,
            rule_name=rule_name,
            message=message,
            context=context
        )
        # Deduplication (very basic)
        recent = self.history.alerts[-5:] if self.history.alerts else []
        if any(a.message == alert.message and (alert.timestamp - a.timestamp).seconds < 60 for a in recent):
            return

        self.history.add_alert(alert)
        if self.notification_manager:
            self.notification_manager.send(alert)

    def process_telemetry_event(self, event: Dict[str, Any]):
        # Map telemetry data to thresholds
        data = event.get('data', {})
        for rule in self.rule_engine.threshold_rules:
            val = data.get(rule.metric)
            if val is not None:
                if self.threshold_monitor.evaluate(rule, val, event):
                    msg = rule.message_template.format(faction=event.get('faction', 'Unknown'), value=val)
                    self.trigger_alert(rule.severity, rule.name, msg, event)

        # Process pattern rules
        for rule in self.rule_engine.pattern_rules:
            if rule.event_type == event.get('category') or rule.event_type == event.get('event_type'):
                self.pattern_detector.process_event(rule, event, self)

    def process_log_event(self, level: int, message: str, context: Dict[str, Any]):
        event = {
            "category": "error",
            "event_type": "log_error",
            "message": message,
            "level": level,
            "turn": context.get("turn", 0),
            "faction": context.get("faction")
        }
        for rule in self.rule_engine.pattern_rules:
            if rule.event_type == "error":
                self.pattern_detector.process_event(rule, event, self)
            
    def get_active_alerts(self) -> List[Alert]:
        return self.history.get_active()
