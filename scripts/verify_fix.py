
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.combat.combat_simulator import run_cross_universe_duel

print("Running verification duel...")
result = run_cross_universe_duel(
    "eternal_crusade:Rift_Daemons:Hellfire Class",
    "eternal_crusade:Iron_Vanguard:Iron Strider"
)

print("\n=== VERIFICATION RESULT ===")
print(f"Winner: {result['winner']}")
print(f"Rounds: {result['rounds']}")
print(f"Survivors: {result['survivors']}")
print(f"Is Finished: {result.get('winner') != 'Draw'}")
