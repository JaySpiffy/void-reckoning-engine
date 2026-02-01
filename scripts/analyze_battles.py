import json
import glob
import os

# Dynamically find latest run
base_report_dir = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\runs"
# Get all subdirs
runs = [os.path.join(base_report_dir, d) for d in os.listdir(base_report_dir) if os.path.isdir(os.path.join(base_report_dir, d))]
if not runs:
    print("No runs found!")
    exit(1)
    
# Sort by modified time (or name if timestamped)
latest_run = max(runs, key=os.path.getmtime)
print(f"Analyzing latest run: {latest_run}")

battle_dir = os.path.join(latest_run, "battles")
files = glob.glob(os.path.join(battle_dir, "*.json"))

battles = []
faction_losses = {}

print(f"Scanning {len(files)} battle files...")

for f in files:
    try:
        with open(f, 'r') as fp:
            data = json.load(fp)
            
        meta = data.get('par', {}).get('meta', {})
        factions = data.get('par', {}).get('factions', {})
        
        total_lost = 0
        total_damage = 0
        
        battle_losses = {}
        
        for fname, stats in factions.items():
            # Handle cases where stats might be missing
            if not stats:
                continue
                
            init = stats.get('initial_strength', 0)
            surv = stats.get('survivors', 0)
            lost = init - surv
            damage = stats.get('damage_dealt', 0)
            
            # Sanity check for negative losses
            if lost < 0:
                lost = 0
            
            total_lost += lost
            total_damage += damage
            
            battle_losses[fname] = lost
            
            faction_losses[fname] = faction_losses.get(fname, 0) + lost
            
        battles.append({
            'name': os.path.basename(f),
            'total_lost': total_lost,
            'total_damage': total_damage,
            'details': battle_losses
        })
            
    except Exception as e:
        print(f"Error parsing {f}: {e}")

# Top 5 Ships Lost
top_lost = sorted(battles, key=lambda x: x['total_lost'], reverse=True)[:5]
print("\n--- TOP 5 BATTLES BY SHIPS LOST ---")
for b in top_lost:
    print(f"{b['name']}: {b['total_lost']} lost (Dmg: {b['total_damage']})")
    print(f"  Breakdown: {b['details']}")

# Top 5 Damage
top_dmg = sorted(battles, key=lambda x: x['total_damage'], reverse=True)[:5]
print("\n--- TOP 5 BATTLES BY DAMAGE DEALT ---")
for b in top_dmg:
    print(f"{b['name']}: {b['total_damage']} dmg (Lost: {b['total_lost']})")

# Total Faction Losses
print("\n--- TOTAL FACTION SHIP LOSSES ---")
sorted_losses = sorted(faction_losses.items(), key=lambda x: x[1], reverse=True)
for faction, lost in sorted_losses:
    print(f"{faction}: {lost}")
