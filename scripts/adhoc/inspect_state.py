
import json
import os
import sys
from collections import Counter

# Path to the campaign.json file (adjust as needed)
CAMPAIGN_FILE = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260119_163343\eternal_crusade\eternal_crusade\batch_20260119_163344\run_001\campaign.json.1"

def inspect_state():
    print(f"Reading {CAMPAIGN_FILE}...")
    
    ships_by_faction = {}
    armies_by_faction = {}
    
    count = 0
    try:
        with open(CAMPAIGN_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                count += 1
                try:
                    event = json.loads(line)
                    context = event.get("context", {})
                    data = context.get("data", {})
                    
                    # Check event type directly from context or message
                    event_type = context.get("event_type", "")
                    if not event_type and "Event: " in event.get("message", ""):
                        parts = event.get("message", "").split("Event: ")
                        if len(parts) > 1:
                            event_type = parts[1].strip()

                    faction = event.get("faction") or context.get("faction") or "Unknown"

                    if event_type == "unit_built":
                        unit = data.get("unit")
                        u_type = data.get("type")
                        if u_type == "army":
                            if faction not in armies_by_faction: armies_by_faction[faction] = []
                            armies_by_faction[faction].append(unit)
                        elif u_type == "ship": 
                            # If ships use unit_built (logs show 'navy_queued' but maybe 'unit_built' too?)
                            # Let's check 'type' for ships too.
                            if faction not in ships_by_faction: ships_by_faction[faction] = []
                            ships_by_faction[faction].append(unit)

                    elif event_type == "navy_queued":
                        # Navy usually queues then builds. 'unit_built' might cover completion.
                        # But looking at logs, we see 'army_queued' then 'unit_built' for armies.
                        # For ships, let's assume 'unit_built' covers it too if type matches?
                        # Log sample 20002: unit="Void_Corsairs Interceptor Interceptor", type="army" ??
                        # Wait, "Interceptor Interceptor" sounds like a ship? No, type="army".
                        # Let's capture navy_queued just in case
                        pass
                        
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        print(f"File not found: {CAMPAIGN_FILE}")
        return

    print(f"Processed {count} lines.")

    print("\n=== SHIP COMPOSITION (Produced) ===")
    for faction, ships in ships_by_faction.items():
        print(f"\n{faction}: {len(ships)} ships produced")
        c = Counter(ships)
        for unit, n in c.most_common():
            print(f"  - {unit}: {n}")

    print("\n=== ARMY COMPOSITION (Produced) ===")
    for faction, armies in armies_by_faction.items():
        print(f"\n{faction}: {len(armies)} armies produced")
        c = Counter(armies)
        for unit, n in c.most_common():
            print(f"  - {unit}: {n}")

if __name__ == "__main__":
    inspect_state()
