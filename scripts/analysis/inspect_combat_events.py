import json
import os

log_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260208_100236\void_reckoning\runs\run_001\telemetry\events.json"

def inspect_events():
    if not os.path.exists(log_path):
        print(f"File not found: {log_path}")
        return

    print(f"Reading {log_path}...")
    with open(log_path, 'r') as f:
        count = 0
        battle_events = []
        for line in f:
            try:
                event = json.loads(line)
                if event.get('event_type') in ['battle_end', 'combat_round', 'unit_destroyed', 'fleet_engagement']:
                    battle_events.append(event)
                    if len(battle_events) >= 5:
                        break
            except json.JSONDecodeError:
                continue
    
    for i, event in enumerate(battle_events):
        print(f"\n--- Event {i+1} ---")
        print(json.dumps(event, indent=2))

if __name__ == "__main__":
    inspect_events()
