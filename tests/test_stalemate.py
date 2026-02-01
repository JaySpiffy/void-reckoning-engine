
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
    u1 = Regiment("Test1", 30, 30, 100, 0, 10, {}, "Faction1", [])
    u2 = Regiment("Test2", 30, 30, 100, 0, 10, {}, "Faction2", [])
    
    armies = {"Faction1": [u1], "Faction2": [u2]}
    state = CombatState(armies, {"Faction1": "STANDARD", "Faction2": "STANDARD"}, {})
    state.initialize_battle()
    
    # 2. Simulate 0 damage rounds
    print(f"Initial state: is_finished={state.check_victory_conditions()[2]}, rounds_since_last_damage={state.rounds_since_last_damage}")
    
    for i in range(100):
        # Mock what execute_battle_round would do
        state.rounds_since_last_damage += 1
        
    winner, survivors, is_finished = state.check_victory_conditions()
    print(f"After 100 rounds of 0 damage: is_finished={is_finished}, winner={winner}")
    
    assert is_finished == True
    assert winner == "Draw"
    print("SUCCESS: Stalemate breaker triggered correctly.")

if __name__ == "__main__":
    test_stalemate_breaker()
