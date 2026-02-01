import argparse
import sys
import json
import time
from src.core.config import set_active_universe
from src.combat.combat_simulator import run_duel
from src.utils.unit_parser import load_all_units

def main():
    parser = argparse.ArgumentParser(description="Single Universe Simulation Runner")
    parser.add_argument("--universe", required=True, help="Universe to simulate")
    parser.add_argument("--output", required=True, help="Output file for JSON result")
    args = parser.parse_args()

    # Configure universe
    try:
        set_active_universe(args.universe)
        
        # Load units
        units = load_all_units()
        
        # Determine representative units for a duel
        factions = list(units.keys())
        if len(factions) < 2:
            result = {"status": "error", "message": f"Not enough factions in {args.universe} (found {len(factions)})"}
        else:
            # Pick first unit from first two factions
            u1 = units[factions[0]][0] if units[factions[0]] else None
            u2 = units[factions[1]][0] if units[factions[1]] else None
            
            if u1 and u2:
                # Run Duel
                start_time = time.time()
                # run_duel prints to stdout, we might want to capture it or just let it run
                # For this test, valid execution is enough.
                # run_duel doesn't return structured data easily, so we just run it.
                # To capture result, we'd need to modify run_duel or capture stdout.
                # Assuming success if no exception.
                winner = run_duel(u1.name, u2.name)
                duration = time.time() - start_time
                
                result = {
                    "status": "success",
                    "universe": args.universe,
                    "combat": f"{u1.name} vs {u2.name}",
                    # "winner": str(winner), # run_duel return might vary, check implementation if needed
                    "duration": duration
                }
            else:
                result = {"status": "error", "message": "Could not find valid units to duel"}

    except Exception as e:
        result = {"status": "error", "message": str(e), "traceback": str(sys.exc_info())}

    # Write result
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
