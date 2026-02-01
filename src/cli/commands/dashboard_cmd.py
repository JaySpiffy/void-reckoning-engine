import argparse
import sys
import subprocess
import webbrowser
import time
from src.cli.base_command import BaseCommand

class DashboardCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "dashboard"

    @property
    @property
    def help(self) -> str:
        return "Launch Terminal Dashboard (Demo Batch)"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--universe", type=str, help="Universe context (default: void_reckoning)")
        parser.add_argument("--runs", type=int, help="Number of runs for demo")

    def execute(self, args: argparse.Namespace) -> None:
        from src.engine import simulation_runner
        
        universe = args.universe or "void_reckoning"
        runs = args.runs
        
        # Interactive prompt if not specified via CLI arg
        if runs is None:
            try:
                user_input = input(f"Enter number of runs for {universe} (default 5): ").strip()
                if user_input:
                    runs = int(user_input)
                else:
                    runs = 5
            except ValueError:
                print("Invalid input. Using default: 5")
                runs = 5
        
        print(f"\n[DEMO] Launching Terminal Dashboard for {universe} ({runs} runs)...")
        print("This runs a small batch simulation to demonstrate the terminal UI.")
        
        # Create a temporary config for the demo
        config = {
            "universe": universe,
            "simulation": {
                "num_runs": runs,
                "output_dir": "reports/dashboard_demo"
            },
            "campaign": {
                "turns": 50,  # Short runs for demo
                "num_systems": 20
            },
            "reporting": {
                "enable_dashboard": True
            }
        }
        
        try:
            simulation_runner.run_batch_simulation(config)
        except KeyboardInterrupt:
            print("\nDemo stopped.")
