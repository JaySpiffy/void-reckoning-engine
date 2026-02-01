#!/usr/bin/env python3
"""
Dashboard Validation Script
---------------------------
Runs the same startup checks as the live dashboard to diagnose issues.
Usage: python scripts/validate_dashboard.py
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

try:
    from src.reporting.dashboard.startup_validator import validate_startup
    from src.reporting.dashboard.config import DashboardConfig
except ImportError as e:
    print(f"Error importing dashboard modules: {e}")
    print("Ensure you are running from the project root or have set PYTHONPATH.")
    sys.exit(1)

def main():
    print("Initializing Dashboard Config to clean state...")
    # Mock config or load real one
    # Note: Flask app config usually not needed unless we depend on specific Flask vars
    # We can try to load via DashboardConfig if it exposes a 'as_dict' or similar, 
    # OR create a dummy config dict
    
    config = {
        'HOST': '0.0.0.0',
        'PORT': 5000,
        # Try to resolve paths dynamically
        'STATIC_FOLDER': os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/reporting/static')),
        'DB_PATH': os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/campaign_data.db')) # Example default
    }
    
    print("Running Validation Checks...")
    success, errors = validate_startup(config)
    
    if success:
        print("\n[OK] DASHBOARD STARTUP CHECKS PASSED")
        sys.exit(0)
    else:
        print("\n[FAIL] DASHBOARD STARTUP CHECKS FAILED")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
