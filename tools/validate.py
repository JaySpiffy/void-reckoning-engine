
import sys
import os
import subprocess
import argparse

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_script = os.path.join(root_dir, "run.py")
    
    parser = argparse.ArgumentParser(description="Wrapper for validation")
    parser.add_argument("--quick", action="store_true", help="Skip registry rebuild")
    parser.add_argument("--check-conversion", action="store_true", help="Validate SOASE conversion pipeline")
    parser.add_argument("--game-dir", type=str, help="Game directory for readiness checks")
    args = parser.parse_args()
    
    cmd = [sys.executable, run_script, "validate"]
    if not args.quick:
        cmd.append("--rebuild-registries")
    if args.check_conversion:
        cmd.append("--check-conversion")
    if args.game_dir:
        cmd.append("--game-dir")
        cmd.append(args.game_dir)
        
    print("Running Validation Wrapper...")
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
