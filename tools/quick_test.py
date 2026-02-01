
import sys
import os
import subprocess

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_script = os.path.join(root_dir, "run.py")
    
    print("=== Quick Health Check ===")
    
    # 1. Validation
    print("\n[1/2] Running Validation...")
    cmd_val = [sys.executable, run_script, "validate", "--rebuild-registries"]
    res_val = subprocess.run(cmd_val)
    if res_val.returncode != 0:
        print("Validation FAILED.")
        sys.exit(1)
        
    # 2. Sample Duel
    print("\n[2/2] Running Sample Duel...")
    # Using two basic units that should exist
    cmd_duel = [sys.executable, run_script, "simulate", "--mode", "duel", "--units", "Space Marine Intercessor", "Ork Boy"]
    res_duel = subprocess.run(cmd_duel)
    if res_duel.returncode != 0:
        print("Duel FAILED.")
        sys.exit(1)
        
    print("\n=== Quick Test PASSED ===")

if __name__ == "__main__":
    main()
