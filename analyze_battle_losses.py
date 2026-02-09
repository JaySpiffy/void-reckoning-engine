import json
import os

log_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260208_100236\void_reckoning\runs\run_001\telemetry\events.json"

def analyze_losses():
    if not os.path.exists(log_path):
        print(f"File not found: {log_path}")
        return

    print(f"Scanning {log_path}...")
    total_battles = 0
    mutual_loss_battles = 0
    one_sided_battles = 0
    zero_loss_battles = 0
    
    examples = []

    with open(log_path, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                if event.get('event_type') == 'battle_end':
                    total_battles += 1
                    data = event.get('data', {})
                    casualties = data.get('casualties', {})
                    
                    losers = [f for f, count in casualties.items() if count > 0]
                    
                    if len(losers) >= 2:
                        mutual_loss_battles += 1
                        if len(examples) < 5:
                            examples.append(event)
                    elif len(losers) == 1:
                        one_sided_battles += 1
                    else:
                        zero_loss_battles += 1
                        
            except json.JSONDecodeError:
                continue
    
    print(f"\n--- Analysis Results ---")
    print(f"Total Battles: {total_battles}")
    print(f"Mutual Loss Battles: {mutual_loss_battles} ({mutual_loss_battles/total_battles*100:.1f}%)")
    print(f"One-Sided Battles: {one_sided_battles} ({one_sided_battles/total_battles*100:.1f}%)")
    print(f"Zero Loss Battles: {zero_loss_battles} ({zero_loss_battles/total_battles*100:.1f}%)")
    
    print(f"\n--- Examples of Mutual Loss ---")
    for i, event in enumerate(examples):
        print(f"\nExample {i+1}: Location: {event['data']['location']}, Rounds: {event['data']['rounds']}")
        print(f"Casualties: {event['data']['casualties']}")

if __name__ == "__main__":
    analyze_losses()
