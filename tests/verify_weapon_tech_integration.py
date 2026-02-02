import sys
import os
import json
import logging

# Setup Paths
sys.path.append(os.getcwd())

from src.managers.tech_manager import TechManager
from src.models.faction import Faction

# Mock Config
class MockConfig:
    TECH_DIR = os.path.join(os.getcwd(), "universes", "void_reckoning", "technology")
    ACTIVE_UNIVERSE = "void_reckoning"
    
if not os.path.exists(MockConfig.TECH_DIR):
    print(f"[ERROR] Tech Dir not found at: {MockConfig.TECH_DIR}")
else:
    print(f"[INFO] Tech Dir found at: {MockConfig.TECH_DIR}")

# Setup Logger
logging.basicConfig(level=logging.INFO)

def run_verification():
    print("--- Starting Weapon & Tech System Overhaul Verification ---")
    
    # 1. Initialize TechManager
    print("\n[Step 1] Initializing Managers...")
    tm = TechManager(tech_dir=MockConfig.TECH_DIR, game_config=MockConfig())
    
    # 2. Check if Universal Techs were generated
    print("\n[Step 2] Verifying Tech Generation...")
    
    # We expect "Tech_Unlock_turbolaser" or similar keys in the procedural output
    # Let's inspect a faction tree (Default)
    tree = tm.faction_tech_trees.get("default", tm.faction_tech_trees.get("imperium_of_man"))
    if not tree:
        # Fallback to any loaded tree
        tree = list(tm.faction_tech_trees.values())[0]

    found_weapon_tech = False
    sample_weapon_tech = None
    
    for t_id in tree["techs"]:
        if "Tech_Unlock_" in t_id:
            found_weapon_tech = True
            sample_weapon_tech = t_id
            print(f"  > Found Dynamic Tech: {t_id}")
            if "turbolaser" in t_id:
                print("    > CONFIRMED: Turbolaser tech exists!")
            if "phaser" in t_id:
                print("    > CONFIRMED: Phaser tech exists!")
                
    if not found_weapon_tech:
        print("[FAIL] No 'Tech_Unlock_' keys found in tech tree! Universal Weaponry integration failed.")
        return
    else:
        print(f"[PASS] Tech Generator is successfully creating nodes from universal_weaponry.json")

    # 3. Test Card Drawing
    print("\n[Step 3] Testing Card System...")
    # Use Underscore to match keys!
    faction_name = "Aurelian_Hegemony"
    faction = Faction(faction_name)
    
    # Get the ACTUAL tree for this faction
    tree = tm.faction_tech_trees.get(faction_name.lower())
    if not tree:
        print(f"[FAIL] Could not find tree for {faction_name.lower()}") 
        return

    # Grant some root techs to ensure prerequisites are met
    # We need to know what roots exist.
    start_techs = [t for t, c in tree["techs"].items() if c <= 1200]
    print(f"  > Granting starter techs: {start_techs[:3]}")
    faction.unlocked_techs.extend(start_techs[:3])
    
    # Draw!
    cards = tm.draw_research_cards(faction, num_cards=5)
    print(f"  > Drawn Cards: {cards}")

    if len(cards) > 0:
        print("[PASS] Card drawing system works.")
        
        # 4. Test Selection
        print("\n[Step 4] Testing Selection...")
        choice = cards[0]
        tm.select_research_project(faction, choice)
        
        if tm.research_state[faction.name]["current_project"] == choice:
            print(f"[PASS] Selected project '{choice}' matches state.")
        else:
            print(f"[FAIL] State mismatch! Expected {choice}, got {tm.research_state[faction.name]['current_project']}")
            
        # 5. Simulate Completion
        print("\n[Step 5] Simulating Unlock...")
        faction.unlock_tech(choice, turn=1, tech_manager=tm)
        if choice in faction.unlocked_techs:
            print("[PASS] Tech unlocked successfully.")
            
            # Check Passive Effects
            effects = tm.get_tech_effects(choice)
            print(f"  > Effects for {choice}: {effects}")
            
    else:
        print("[FAIL] Still no cards drawn after unlocking starters.")


    # 6. Verify Ship Designer Logic
    print("\n[Step 6] Verifying Ship Designer Restriction...")
    from src.core.ship_design_system import ShipDesigner, ShipComponent, ShipHull, ShipDesign
    
    # Setup Mock Components
    # 1 Basic (Tier 1) - Should be available by default if Tech Level matches
    basic_laser = ShipComponent("basic_laser", "Basic Laser", "S", {"damage": 10}, 100, -10, tech_level=1)
    # 2 Advanced (Tier 3) - Requires Tech Unlock
    photon_torp = ShipComponent("photon_torpedo", "Photon Torpedo", "S", {"damage": 50}, 500, -50, tech_level=3)
    
    registry = {"basic_laser": basic_laser, "photon_torpedo": photon_torp}
    designer = ShipDesigner(registry)
    
    hull = ShipHull("corvette_hull", "Corvette", 1, {"hp": 500}, {"S": 1})
    
    # Case A: Before Unlock (but high tech level)
    print("  > Designing ship with Tech Level 3 (Locked Techs)...")
    # Reset Faction Unlocks for testing
    faction.unlocked_techs = ["Headquarters"] 
    
    design_a = designer.create_design(hull, "Test Ship A", faction=faction, tech_level=3)
    comp_a = design_a.components["S"][0]
    print(f"    > Component Chosen: {comp_a.name}")
    
    if comp_a.id == "photon_torpedo":
        print("[FAIL] ShipDesigner picked Photon Torpedo despite it being LOCKED!")
    else:
        print("[PASS] ShipDesigner correctly restricted Photon Torpedo.")
        
    # Case B: After Unlock
    print("  > Unlocking Photon Torpedo...")
    faction.unlock_tech("Tech_Unlock_photon_torpedo", turn=5, tech_manager=tm)
    
    design_b = designer.create_design(hull, "Test Ship B", faction=faction, tech_level=3)
    comp_b = design_b.components["S"][0]
    print(f"    > Component Chosen: {comp_b.name}")
    
    if comp_b.id == "photon_torpedo":
         print("[PASS] ShipDesigner correctly picked Photon Torpedo after unlock.")
    else:
         print(f"[FAIL] ShipDesigner failed to pick Photon Torpedo (Picked {comp_b.name}).")

if __name__ == "__main__":
    run_verification()
