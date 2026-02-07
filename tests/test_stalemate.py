
import os
import sys
from unittest.mock import MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.combat.combat_state import CombatState
from src.models.unit import Regiment

def test_stalemate_breaker():
    print("Testing Stalemate Breaker...")
    
    # 1. Setup mock units
    u1 = Regiment("Test1", "Faction1")
    u2 = Regiment("Test2", "Faction2")
    
    # Initialize HP since Regiment defaults might not match test expectations
    u1.base_hp = 100
    u1.current_hp = 100
    u2.base_hp = 100
    u2.current_hp = 100
    
    armies = {"Faction1": [u1], "Faction2": [u2]}
    state = CombatState(armies, {"Faction1": "STANDARD", "Faction2": "STANDARD"}, {})
    
    # Faction1 is Defender.
    state.defender_factions = {"Faction1"}
    state.initialize_battle()
    
    print(f"Initial state: is_finished={state.check_victory_conditions()[2]}, rounds_since_last_damage={state.rounds_since_last_damage}")
    
    # Force rounds since last damage high
    state.rounds_since_last_damage = 500
        
    winner, survivors, is_finished = state.check_victory_conditions()
    print(f"After timeout: is_finished={is_finished}, winner={winner}")
    
    assert is_finished == True
    # Faction1 should win as it is the defender and survived
    assert winner == "Faction1"
    print("SUCCESS: Stalemate breaker triggered correctly.")

if __name__ == "__main__":
    test_stalemate_breaker()
