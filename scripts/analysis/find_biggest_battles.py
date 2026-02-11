import json
import os

log_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260208_100236\void_reckoning\runs\run_001\telemetry\events.json"

def find_biggest():
    if not os.path.exists(log_path):
        print(f"File not found: {log_path}")
        return

    battles = []

    print(f"Scanning {log_path}...")
    with open(log_path, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                if event.get('event_type') == 'battle_end':
                    data = event.get('data', {})
                    casualties = data.get('casualties', {})
                    total_lost = sum(casualties.values())
                    
                    battles.append({
                        'id': data.get('battle_id'),
                        'location': data.get('location'),
                        'rounds': data.get('rounds'),
                        'casualties': casualties,
                        'total_lost': total_lost,
                        'mutual': len([c for c in casualties.values() if c > 0]) > 1
                    })
            except:
                continue
    
    # Sort by total units lost descending
    battles.sort(key=lambda x: x['total_lost'], reverse=True)

    print(f"\n--- Top 5 Biggest Battles (by Unit Count) ---")
    for b in battles[:5]:
        mutual_str = "[MUTUAL]" if b['mutual'] else "[ONE-SIDED]"
        print(f"\n{mutual_str} Battle at {b['location']} (Rounds: {b['rounds']})")
        print(f"Total Casualties: {b['total_lost']}")
        print(f"Breakdown: {b['casualties']}")

if __name__ == "__main__":
    find_biggest()
