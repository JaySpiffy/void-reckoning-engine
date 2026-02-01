import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.simulate_campaign import CampaignEngine
from src.core.config import set_active_universe

def verify_colonization():
    print("--- Starting Colonization Verification ---")
    
    # Setup
    set_active_universe("eternal_crusade")
    engine = CampaignEngine(universe_name="eternal_crusade")
    engine.generate_galaxy(num_systems=10, min_planets=2, max_planets=4)
    engine.spawn_start_fleets()
    
    # Run Simulation
    colonization_events = 0
    savings_trigger = False
    
    print("Running 15 Turns...")
    for i in range(15):
        engine.process_turn()
        
        # Check Faction Status
        for f_name, f_mgr in engine.factions.items():
            if f_name == "Neutral": continue
            
            # Check for savings behavior (High Req, Low Spending)
            if f_mgr.requisition > 2000:
                savings_trigger = True
                
            # Check for colonization commands (Fleet disappeared or planet owner changed)
            # Easier: Check planet owner changes
            pass
            
        print(f"Turn {i+1}: " + " | ".join([f"{f}: {engine.factions[f].requisition}R" for f in engine.factions if f != "Neutral"]))
    
    # Post-Run Analysis
    initial_planets = len([p for p in engine.all_planets if p.owner != "Neutral"])
    
    # Count current owned planets
    total_colonized = 0
    for f_name in engine.factions:
        if f_name == "Neutral": continue
        owned = len(engine.planets_by_faction.get(f_name, []))
        print(f"[{f_name}] Owned Planets: {owned}")
        # Assuming they start with 1, anything > 1 is colonization
        if owned > 1:
            total_colonized += (owned - 1)
    
    if total_colonized > 0:
        print(f"\n[PASS] Colonization Active! Total New Colonies: {total_colonized}")
    elif savings_trigger:
         print(f"\n[WARN] Savings logic active (Req > 2000), but no colonization yet. Might need more turns.")
    else:
        print(f"\n[FAIL] No Colonization and No Savings detected.")

if __name__ == "__main__":
    verify_colonization()
