
import sys
import os
import subprocess

def main():
    print("--- Warhammer 40k Simulator Setup ---")
    
    # 1. Check Python Version
    print(f"Python Version: {sys.version.split()[0]}")
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7+ is required.")
        sys.exit(1)
        
    # 2. Verify Directory Structure
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Project Root: {root_dir}")
    
    required_dirs = [
        os.path.join("wh40k_campaign_simulator", "data", "02_factions_and_units"),
        os.path.join("wh40k_campaign_simulator", "data", "03_Infrastructure"),
        os.path.join("wh40k_campaign_simulator", "data", "04_Technology"),
        os.path.join("wh40k_campaign_simulator", "campaign", "simulation")
    ]
    missing = []
    for d in required_dirs:
        if not os.path.exists(os.path.join(root_dir, d)):
            missing.append(d)
            
    if missing:
        print(f"ERROR: Missing directories: {missing}")
        sys.exit(1)
        
    print("Directory structure OK.")
    
    # 3. Build Registries & Validate (via run.py)
    run_script = os.path.join(root_dir, "run.py")
    if not os.path.exists(run_script):
        print("ERROR: run.py not found in root.")
        sys.exit(1)
        
    print("\n[Step 1/2] Building Registries and Validating Data...")
    res = subprocess.run([sys.executable, run_script, "validate", "--rebuild-registries"])
    
    if res.returncode != 0:
        print("\nWARNING: Validation found issues. Please review errors above.")
    else:
        print("\nSUCCESS: Validation passed.")
        
    print("\n[Step 2/2] Setup Complete.")
    print("Try running a quick simulation:")
    print("  python scripts/simulate.py --mode duel --units \"Space Marine\" \"Ork Boy\"")

if __name__ == "__main__":
    main()
