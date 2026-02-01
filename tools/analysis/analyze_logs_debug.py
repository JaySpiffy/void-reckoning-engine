
import os
import re

LOG_FILE = r'C:\Users\whitt\Desktop\New folder (4)\reports\batch_20251229_093226\run_001\full_campaign_log.txt'

def analyze_logs():
    if not os.path.exists(LOG_FILE):
        print(f"File not found: {LOG_FILE}")
        return

    battle_events = []
    recruit_events = []
    
    print(f"Reading {LOG_FILE}...")
    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if '[COMBAT]' in line:
                    battle_events.append(line.strip())
                elif '[RECRUIT]' in line:
                    recruit_events.append(line.strip())
                elif '[CLEANUP]' in line:
                    print(line.strip())
                elif '[INVASION]' in line:
                    print(line.strip())
                elif '[EMBARK]' in line:
                    recruit_events.append(line.strip()) # Using same list for convenience
    except Exception as e:
        print(f"Error reading file: {e}")

    print(f"\n--- Last 10 Battles ---")
    for b in battle_events[-10:]:
        print(b)
        
    print(f"\n--- Last 10 Recruitments ---")
    for r in recruit_events[-10:]:
        print(r)

    print(f"\nTotal Battles: {len(battle_events)}")
    print(f"Total Recruitments: {len(recruit_events)}")

if __name__ == "__main__":
    analyze_logs()
