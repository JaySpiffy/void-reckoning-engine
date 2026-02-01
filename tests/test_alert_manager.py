import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import yaml

from src.reporting.alert_manager import AlertManager, AlertRuleEngine, ThresholdMonitor
from src.reporting.alert_models import AlertSeverity, ThresholdRule

# Helper to reset Singleton
@pytest.fixture(autouse=True)
def reset_alert_manager():
    AlertManager._instance = None
    yield
    AlertManager._instance = None

@pytest.fixture
def mock_config():
    return {
        'notifications': {'console': True},
        'thresholds': {
            'low_fps': {
                'enabled': True,
                'severity': 'warning',
                'message': 'FPS is low: {value}',
                'metric': 'fps',
                'operator': 'less_than',
                'value': 30,
                'duration_turns': 1
            }
        },
        'patterns': {
            'error_spam': {
                'enabled': True,
                'severity': 'critical',
                'message': 'Repeated error: {error_message}',
                'event_type': 'error',
                'pattern': 'same_error_message',
                'threshold_count': 2,
                'window_turns': 5
            }
        }
    }

@pytest.fixture
def alert_manager(mock_config):
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        with patch("yaml.safe_load", return_value=mock_config):
            with patch("src.reporting.notification_channels.NotificationManager") as MockNM:
                am = AlertManager("dummy_path")
                am.notification_manager = MockNM.return_value
                return am

def test_threshold_monitor_trigger(alert_manager):
    """Test that a threshold violation triggers an alert."""
    event = {
        "category": "performance",
        "turn": 10,
        "faction": "Imperium",
        "data": {"fps": 25} # Less than 30
    }
    
    alert_manager.process_telemetry_event(event)
    
    # Check history
    active = alert_manager.get_active_alerts()
    assert len(active) == 1
    assert active[0].rule_name == "low_fps"
    assert "FPS is low: 25" in active[0].message
    
    # Check notification sent
    alert_manager.notification_manager.send.assert_called_once()

def test_threshold_consecutive_duration():
    """Test that duration_turns logic works in monitor."""
    monitor = ThresholdMonitor()
    rule = ThresholdRule(
        name="test_rule", enabled=True, severity=AlertSeverity.WARNING,
        message_template="", config={}, metric="val", operator="greater_than",
        value=100, duration_turns=3 # Needs 3 consecutive triggers
    )
    
    # Turn 1: Trigger (Count 1) -> No Alert
    assert not monitor.evaluate(rule, 101, {}) 
    
    # Turn 2: Miss (Count 0) -> Reset
    assert not monitor.evaluate(rule, 90, {})
    
    # Turn 3: Trigger (Count 1)
    assert not monitor.evaluate(rule, 101, {})
    
    # Turn 4: Trigger (Count 2)
    assert not monitor.evaluate(rule, 101, {})
    
    # Turn 5: Trigger (Count 3) -> ALERT
    assert monitor.evaluate(rule, 101, {})

def test_pattern_detection_error_spam(alert_manager):
    """Test repeated error pattern detection."""
    
    # Inject 1st error
    alert_manager.process_log_event(40, "Connection timeout", {"turn": 1})
    assert len(alert_manager.get_active_alerts()) == 0
    
    # Inject 2nd error (Threshold is 2)
    alert_manager.process_log_event(40, "Connection timeout", {"turn": 2})
    
    active = alert_manager.get_active_alerts()
    assert len(active) == 1
    assert active[0].rule_name == "error_spam"
    assert "Connection timeout" in active[0].message

def test_alert_deduplication(alert_manager):
    """Test that identical alerts are deduplicated within 60 seconds."""
    # Trigger first alert
    alert_manager.trigger_alert(AlertSeverity.WARNING, "rule1", "Same Message", {})
    assert len(alert_manager.history.alerts) == 1
    
    # Trigger second alert immediately
    alert_manager.trigger_alert(AlertSeverity.WARNING, "rule1", "Same Message", {})
    assert len(alert_manager.history.alerts) == 1 # Should stay 1
    
    # Trigger different message
    alert_manager.trigger_alert(AlertSeverity.WARNING, "rule1", "Different Message", {})
    assert len(alert_manager.history.alerts) == 2
