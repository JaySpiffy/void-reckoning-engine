
import os
import sys
import json
import glob
from datetime import datetime

# Add src to path
sys.path.append(os.getcwd())

from src.reporting.dashboard_v2.api.utils.discovery import discover_all_runs

def debug_discovery():
    print("REPORTS_DIR:", os.path.abspath("reports"))
    
    runs = discover_all_runs("void_reckoning")
    print(f"Discovered {len(runs)} runs for void_reckoning.")
    
    for r in runs[:5]:
        print(f"Run: {r['run_id']} | Turns: {r['turns_taken']} | Started: {r['started_at']}")
        
        # Check subdirs manually
        rp = r['path']
        t_dirs = glob.glob(os.path.join(rp, "turn_*"))
        t_dirs_nested = glob.glob(os.path.join(rp, "turns", "turn_*"))
        print(f"  - Manual Turn Count: root={len(t_dirs)}, nested={len(t_dirs_nested)}")
        
        # Check factions dir
        f_dir = os.path.join(rp, "factions")
        if os.path.exists(f_dir):
            f_files = glob.glob(os.path.join(f_dir, "*.json"))
            print(f"  - Faction files: {len(f_files)}")
            # Try to extract max turn from faction files
            import re
            turns = set()
            for f in f_files:
                match = re.search(r"_turn_(\d+)\.json", f)
                if match:
                    turns.add(int(match.group(1)))
            if turns:
                print(f"  - Max turn from factions: {max(turns)}")

if __name__ == "__main__":
    debug_discovery()
