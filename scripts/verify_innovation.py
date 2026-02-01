import os
import sys
import json

# Ensure we can import from src
sys.path.append(os.getcwd())

import src.core.config as config
from src.managers.ai_manager import StrategicAI
from src.core.interfaces import IEngine

# Mock Engine for Verification
class MockEngine:
    def __init__(self):
        self.turn_counter = 200 # Set to a turn that might trigger innovation
        self.factions = {}
        self.unit_registry = {}
        self.planets_by_faction = {}
        self.fleets = []
        self.all_planets = []
        self.logger = None
        self.tech_manager = None

    def get_faction(self, name):
        return self.factions.get(name)

class MockFaction:
    def __init__(self, name):
        self.id = name
        self.requisition = 200000
        self.unlocked_techs = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", 
                               "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18", "T19", "T20", "T21"]
        self.weapon_registry = {}
        self.custom_hulls = {}
        self.learned_personality = None
        self.stats = {
            "turn_battles_won": 0,
            "turn_battles_lost": 0,
            "turn_losses": 1000,
            "turn_kills": 5000,
            "total_score": 100000
        }
        self.learning_history = {
            'performance_window': []
        }

def test_innovation_cycle():
    print("--- Verification: Hull & Weapon Innovation ---")
    
    # Setup
    engine = MockEngine()
    cyb_faction = MockFaction("Cyber_Synod")
    engine.factions["Cyber_Synod"] = cyb_faction
    
    config.ACTIVE_UNIVERSE = "eternal_crusade"
    config.UNIVERSE_ROOT = os.path.join(os.getcwd(), "universes")
    
    sai = StrategicAI(engine)
    
    # 1. Force Innovation Cycle
    print("Triggering Innovation Cycle for Cyber_Synod...")
    # We'll run it a few times to see both types (Hull vs Weapon)
    for i in range(5):
        print(f"\n[Run {i+1}]")
        sai.process_innovation_cycle("Cyber_Synod")
        
        # Check Results
        if cyb_faction.custom_hulls:
            print(f"  - Found {len(cyb_faction.custom_hulls)} custom hulls: {list(cyb_faction.custom_hulls.keys())}")
        
        if cyb_faction.weapon_registry:
            # Check for experimental weapons
            exp_weapons = [w for w in cyb_faction.weapon_registry.values() if w.get("category") == "Experimental"]
            if exp_weapons:
                print(f"  - Invented experimental weapons: {[w['name'] for w in exp_weapons]}")

    if cyb_faction.custom_hulls or any(w.get("category") == "Experimental" for w in cyb_faction.weapon_registry.values()):
        print("\n[SUCCESS] Innovation system successfully generated new tech/hulls!")
    else:
        print("\n[FAILURE] Innovation system failed to generate results.")

if __name__ == "__main__":
    test_innovation_cycle()
