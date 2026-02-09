import json
import os

log_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260208_100236\void_reckoning\runs\run_001\telemetry\events.json"

def analyze_battle():
    if not os.path.exists(log_path):
        print(f"File not found: {log_path}")
        return

    print(f"Scanning {log_path} for the Axikora IV battle...")
    target_battle_id = None
    
    # 1. Find the specific battle ID
    with open(log_path, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                if event.get('event_type') == 'battle_end':
                    data = event.get('data', {})
                    if data.get('location') == 'Axikora IV':
                        cas = data.get('casualties', {})
                        # Match the specific casualty profile
                        if cas.get('SteelBound_Syndicate') == 176 and cas.get('BioTide_Collective') == 19:
                            target_battle_id = data.get('battle_id')
                            print(f"Found Battle ID: {target_battle_id}")
                            break
            except:
                continue
    
    if not target_battle_id:
        print("Battle not found.")
        return

    # 2. Extract relevant details
    print(f"\n--- Battle Details for {target_battle_id} ---")
    events_of_interest = ['battle_composition', 'battle_end', 'combat_engagement_analysis', 'battle_decisiveness']
    
    with open(log_path, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                if event.get('data', {}).get('battle_id') == target_battle_id:
                    if event.get('event_type') in events_of_interest:
                        print(f"\n>>> Event: {event.get('event_type')}")
                        print(json.dumps(event.get('data'), indent=2))
            except:
                continue

if __name__ == "__main__":
    analyze_battle()
