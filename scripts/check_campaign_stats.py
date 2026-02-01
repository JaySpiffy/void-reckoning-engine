import json
import os

report_path = r'C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\eternal_crusade\batch_20260124_232546\run_1769297146\campaign.json'

with open(report_path, 'r') as f:
    data = json.load(f)

print("=== Campaign Statistics ===")
factions = data.get('factions', {})
total_wins = 0
total_losses = 0
total_draws = 0

for f_name, f_data in factions.items():
    stats = f_data.get('stats', {})
    wins = stats.get('battles_won', 0)
    losses = stats.get('battles_lost', 0)
    draws = stats.get('battles_drawn', 0)
    print(f"{f_name}: W:{wins} L:{losses} D:{draws}")
    total_wins += wins
    total_losses += losses
    total_draws += draws

print(f"\nTOTALS: W:{total_wins} L:{total_losses} D:{total_draws}")
