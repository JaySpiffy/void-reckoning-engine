import yaml
import os
import sys
from typing import Dict, List, Any

def validate_alert_config(config_path: str) -> bool:
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return False
        
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        is_valid = True
        
        # Check thresholds
        thresholds = config.get('thresholds', {})
        for name, r in thresholds.items():
            required = ['metric', 'operator', 'value', 'severity']
            for field in required:
                if field not in r:
                    print(f"Error in threshold '{name}': Missing required field '{field}'")
                    is_valid = False
                    
        # Check notification channels
        notifications = config.get('notifications', {})
        if not notifications:
            print("Warning: No notification channels defined.")
            
        if is_valid:
            print(f"Success: Configuration at {config_path} is valid.")
        return is_valid
        
    except Exception as e:
        print(f"Error parsing YAML: {e}")
        return False

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "config/alert_rules.yaml"
    validate_alert_config(path)
