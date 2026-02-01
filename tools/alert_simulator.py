import time
import random
from src.reporting.alert_manager import AlertManager
from src.reporting.alert_models import AlertSeverity

def simulate_alerts():
    print("Starting Alert Simulator...")
    am = AlertManager()
    
    # Simulate simple events
    factions = ["Ultramarines", "Black Legion", "Eldar", "Necrons"]
    
    try:
        while True:
            f = random.choice(factions)
            r = random.random()
            
            if r > 0.9:
                am.trigger_alert(
                    AlertSeverity.CRITICAL,
                    "repeated_crashes",
                    f"CRITICAL: Repeated system failure detected in {f} AI controller.",
                    {"faction": f, "error_code": 500}
                )
            elif r > 0.7:
                am.trigger_alert(
                    AlertSeverity.WARNING,
                    "resource_depletion",
                    f"Warning: {f} resources are critically low.",
                    {"faction": f, "requisition": 450}
                )
                
            time.sleep(2)
    except KeyboardInterrupt:
        print("Simulator stopped.")

if __name__ == "__main__":
    simulate_alerts()
