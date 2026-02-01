import os
import sys

# Ensure we can import from src
sys.path.append(os.getcwd())

import src.core.config as config
from src.managers.tech_manager import TechManager
from src.models.faction import Faction

def test_syncretic_tech_loading():
    print("--- Verification: Intra-Universe Hybrid Tech ---")
    
    # Force Eternal Crusade context
    config.ACTIVE_UNIVERSE = "eternal_crusade"
    
    # Initialize TechManager
    tm = TechManager()
    
    # Check if syncretic techs are loaded
    syncretic_ids = ["syncretic_iv_zl_hallowed_bulwark", "syncretic_cs_hs_neural_lattice"]
    for sid in syncretic_ids:
        if sid in tm.hybrid_tech_trees:
            print(f"[SUCCESS] Loaded syncretic tech: {sid}")
        else:
            print(f"[FAILURE] Syncretic tech not found: {sid}")

    # Mock Factions and Test Prerequisites
    # 1. Iron Vanguard + Zealot
    iv_faction = Faction("Iron_Vanguard")
    
    # Prerequisites: 
    # Tech_Iron_Vanguard_Heavy Armor
    # Tech_Zealot_Legions_Basic Doctrine
    
    tech_vanguard = "Tech_Iron_Vanguard_Heavy Armor"
    tech_zealot = "Tech_Zealot_Legions_Basic Doctrine"
    syncretic_tech = "syncretic_iv_zl_hallowed_bulwark"
    
    print(f"\nTesting {syncretic_tech}:")
    print(f"- Available initially: {tm.is_hybrid_tech_available(iv_faction, syncretic_tech)}")
    
    # Add native tech
    iv_faction.unlock_tech(tech_vanguard)
    print(f"- Available after native tech: {tm.is_hybrid_tech_available(iv_faction, syncretic_tech)}")
    
    # Add stolen tech (The Intra-Universe Syncrecy!)
    iv_faction.unlock_tech(tech_zealot)
    print(f"- Available after stolen tech: {tm.is_hybrid_tech_available(iv_faction, syncretic_tech)}")

    if tm.is_hybrid_tech_available(iv_faction, syncretic_tech):
        print(f"[SUCCESS] {syncretic_tech} prerequisites correctly resolved across factions.")
    else:
        print(f"[FAILURE] {syncretic_tech} prerequisites failed to resolve.")

if __name__ == "__main__":
    test_syncretic_tech_loading()
