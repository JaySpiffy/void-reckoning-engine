import json
import glob
import os

log_dir = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260202_182425\void_reckoning\runs\run_001"

def scan_all_116():
    files = glob.glob(os.path.join(log_dir, "campaign.json*"))
    target_turn = 116
    target_faction = "Algorithmic_Hierarchy"
    interest = ["unit_losses_report", "battle_end"]
    
    print(f"Scanning {len(files)} files for Turn {target_turn} / {target_faction}...")
    
    for f_path in files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("turn") == target_turn:
                            ctx = record.get("context", {})
                            et = ctx.get("event_type")
                            
                            if et in interest:
                                rec_str = json.dumps(record)
                                if target_faction in rec_str:
                                    print(f"[{os.path.basename(f_path)}] {json.dumps(record, indent=2)}")
                    except: pass
        except Exception as e:
            print(f"Error reading {os.path.basename(f_path)}: {e}")

if __name__ == "__main__":
    scan_all_116()
