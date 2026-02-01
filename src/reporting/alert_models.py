from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @classmethod
    def from_str(cls, label: str):
        label = label.lower()
        if label == "info": return cls.INFO
        if label == "warning": return cls.WARNING
        if label == "error": return cls.ERROR
        if label == "critical": return cls.CRITICAL
        return cls.INFO

@dataclass
class Alert:
    id: str
    timestamp: datetime
    severity: AlertSeverity
    rule_name: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "rule_name": self.rule_name,
            "message": self.message,
            "context": self.context,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved
        }

@dataclass
class AlertHistory:
    alerts: List[Alert] = field(default_factory=list)
    
    def add_alert(self, alert: Alert):
        self.alerts.append(alert)
        
    def get_active(self) -> List[Alert]:
        return [a for a in self.alerts if not a.acknowledged and not a.resolved]

@dataclass
class AlertRule:
    name: str
    enabled: bool
    severity: AlertSeverity
    message_template: str
    config: Dict[str, Any]

@dataclass
class ThresholdRule(AlertRule):
    metric: str
    operator: str
    value: Any
    duration_turns: int = 1

@dataclass
class PatternRule(AlertRule):
    event_type: str
    pattern_type: str
    window_turns: int = 10
    threshold_count: int = 3
    metric: Optional[str] = None
    threshold: Optional[Any] = None
    growth_rate_mb_per_turn: Optional[float] = None
