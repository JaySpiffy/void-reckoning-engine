import json
import os

log_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260208_100236\void_reckoning\runs\run_001\telemetry\events.json"

def deep_dive():
    if not os.path.exists(log_path):
        print(f"File not found: {log_path}")
        return

    print(f"Scanning {log_path} for a mutual loss battle...")
    target_battle_id = None
    
    # First pass: Find a battle with mutual losses
    with open(log_path, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                if event.get('event_type') == 'battle_end':
                    data = event.get('data', {})
                    casualties = data.get('casualties', {})
                    losers = [f for f, count in casualties.items() if count > 0]
                    
                    if len(losers) >= 2:
                        target_battle_id = data.get('battle_id')
                        print(f"Found Target Battle: {target_battle_id}")
                        print(f"Casualties: {casualties}")
                        break
            except:
                continue
                
    if not target_battle_id:
        print("No mutual loss battle found.")
        return

    # Second pass: Collect all events for this battle
    print(f"\n--- Extracting Events for {target_battle_id} ---")
    with open(log_path, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                # Check if this event relates to our battle
                # battle_end has battle_id in data
                # combat_round has battle_id in data
                if event.get('data', {}).get('battle_id') == target_battle_id:
                    print(json.dumps(event, indent=2))
            except:
                continue

if __name__ == "__main__":
    deep_dive()
