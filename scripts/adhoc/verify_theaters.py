
import sys
import os

# Fix path
sys.path.append(os.getcwd())

from src.engine.simulate_campaign import run_campaign_simulation

# Run short campaign
if __name__ == "__main__":
    print("Running Verification Simulation...")
    # Increase turns to ensure multiple factions get processed
    run_campaign_simulation(turns=15, planets=20)
