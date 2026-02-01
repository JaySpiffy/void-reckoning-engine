import sys
import os
import subprocess

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_script = os.path.join(root_dir, "run.py")
    
    # We pass through arguments to run.py simulate
    # But let's add some interactive default behavior if no args provided
    
    if len(sys.argv) == 1:
        print("--- Simulation Interactive Mode ---")
        print("1. Quick Campaign (30 turns, 15 systems)")
        print("2. Quick Duel (Space Marine vs Ork Boy)")
        print("3. Grand Royale (All Factions)")
        print("4. Fleet Battle (Imperium vs Chaos)")
        
        choice = input("Select mode (1-4): ")
        if choice == "1":
             subprocess.run([sys.executable, run_script, "campaign", "--quick"])
        elif choice == "2":
            subprocess.run([sys.executable, run_script, "simulate", "--mode", "duel", "--units", "Space Marine", "Ork Boy"])
        elif choice == "3":
            subprocess.run([sys.executable, run_script, "simulate", "--mode", "royale"])
        elif choice == "4":
            subprocess.run([sys.executable, run_script, "simulate", "--mode", "fleet", "--faction1", "Imperium", "--faction2", "Chaos Undivided", "--size", "50"])
        else:
            print("Invalid choice.")
        return

    # Pass through
    args = sys.argv[1:]
    cmd = [sys.executable, run_script, "simulate"] + args
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
