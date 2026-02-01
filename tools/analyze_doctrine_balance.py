
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

def analyze_doctrines(log_dir="telemetry_logs"):
    print(f"--- Faction Combat Doctrine Analysis ---")
    log_path = Path(log_dir)
    if not log_path.exists():
        print(f"Directory {log_dir} not found.")
        return

    # Load all json files
    events = []
    for f in log_path.glob("*.json"):
        try:
            with open(f, 'r') as json_file:
                data = json.load(json_file)
                if isinstance(data, list):
                    events.extend(data)
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if not events:
        print("No telemetry events found.")
        return

    # Filter for doctrine events
    doctrine_events = [e for e in events if e.get('category') == 'doctrine']
    print(f"Found {len(doctrine_events)} doctrine events.")

    # Aggregate by Faction & Doctrine
    stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'played': 0, 'casualties': 0})
    
    for e in doctrine_events:
        data = e.get('data', {})
        faction = data.get('faction')
        doctrine = data.get('doctrine') or "STANDARD"
        outcome = data.get('outcome')
        
        if not faction: continue
        
        key = (faction, doctrine)
        stats[key]['played'] += 1
        if outcome == 'WIN':
            stats[key]['wins'] += 1
        elif outcome == 'LOSS':
            stats[key]['losses'] += 1
            
        stats[key]['casualties'] += data.get('casualties', 0)

    # Print Report
    print(f"\n{'FACTION':<20} | {'DOCTRINE':<15} | {'WIN RATE':<10} | {'BATTLES':<8}")
    print("-" * 65)
    
    for (faction, doctrine), stat in sorted(stats.items(), key=lambda x: x[0][0]):
        total = stat['played']
        win_rate = (stat['wins'] / total * 100) if total > 0 else 0
        print(f"{faction:<20} | {doctrine:<15} | {win_rate:>9.1f}% | {total:>8}")

if __name__ == "__main__":
    analyze_doctrines()
