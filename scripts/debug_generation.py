
from src.engine import simulate_campaign
import os
import shutil

def verify_generation():
    # Cleanup previous test if exists
    target_dir = "reports/eternal_crusade"
    # Don't delete valuable data, just check if new run appears
    
    print("Running 1-turn simulation...")
    simulate_campaign.run_campaign_simulation(turns=1, planets=10, universe_name="eternal_crusade")
    
    if os.path.exists(target_dir):
        print(f"\n[SUCCESS] Directory '{target_dir}' exists.")
        # Check for recent batches
        batches = os.listdir(target_dir)
        print(f"Batches found: {batches}")
    else:
        print(f"\n[FAILURE] Directory '{target_dir}' NOT found.")

if __name__ == "__main__":
    verify_generation()
