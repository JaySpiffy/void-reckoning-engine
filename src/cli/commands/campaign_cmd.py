import argparse
import sys
from src.cli.base_command import BaseCommand

class CampaignCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "campaign"

    @property
    def help(self) -> str:
        return "Run single-universe campaign simulations"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--universe", type=str, default="void_reckoning",
                            help="Universe to simulate (default: void_reckoning)")
        parser.add_argument("--quick", action="store_true", help="Run a quick 30-turn campaign")
        parser.add_argument("--batch", action="store_true", help="Run batch simulation")
        parser.add_argument("--config", type=str, help="Path to config JSON")
        parser.add_argument("--turns", type=int, help="Override turn count")
        parser.add_argument("--systems", type=int, help="Override system count")
        parser.add_argument("--output-dir", type=str, help="Custom output directory")
        parser.add_argument("--dashboard", action="store_true", help="Launch live dashboard for this simulation")
        parser.add_argument("--delay", type=float, default=0.0, help="Delay in seconds between turns")
        parser.add_argument("--manual", action="store_true", help="Start simulation in PAUSED mode for manual stepping")
        parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically (Dashboard)")

    def execute(self, args: argparse.Namespace) -> None:
        from src.core.config import set_active_universe
        from src.engine import simulate_campaign
        from src.engine import simulation_runner as run_simulation
        import time
        import subprocess
        import webbrowser

        universe = args.universe
        set_active_universe(universe)
        
        # Dashboard Integration
        active_run_id = f"run_{int(time.time())}" # Default generation
        
        if args.dashboard:
            try:
                print(f"Launching Live Dashboard V2 for {universe}...")
                
                # Launch FastAPI Server via subprocess
                # NOTE: In CLI refactor we don't hold the process ref in a persistent variable
                # unless we block.
                dash_process = subprocess.Popen([
                    sys.executable, 
                    "-m", "src.reporting.dashboard_v2.run_server",
                    "--universe", universe,
                    "--run-id", active_run_id
                ])
                
                time.sleep(3.0)
                
                dashboard_url = "http://localhost:8000"
                if not getattr(args, 'no_browser', False):
                     try:
                        print(f"[DASHBOARD] Opening browser at {dashboard_url}")
                        webbrowser.open(dashboard_url)
                     except: pass
                     
            except Exception as e:
                print(f"Warning: Failed to launch dashboard: {e}")
        
        # Execution Mode
        if args.quick:
             simulate_campaign.run_campaign_simulation(
                 turns=30, 
                 planets=15, 
                 universe_name=universe, 
                 run_id=active_run_id, 
                 delay_seconds=args.delay, 
                 manual_mode=args.manual
             )
        elif args.batch:
             print("Batch mode dashboard not fully supported in this refactor.")
             output_dir = args.output_dir
             if args.config:
                 config_data = run_simulation.load_config_from_file(args.config)
             else:
                 config_data = run_simulation.load_config_from_file() # Load default
                 
             run_simulation.run_batch_simulation(config_data, output_dir=output_dir)
             
        elif args.config or args.turns or args.systems:
             # Custom
             t = args.turns or 30
             s = args.systems or 15
             config_data = None
             if args.config:
                  config_data = run_simulation.load_config_from_file(args.config)
                  t = args.turns or config_data.get("campaign", {}).get("turns", 50)
                  s = args.systems or config_data.get("campaign", {}).get("num_systems", 40)
                  
             simulate_campaign.run_campaign_simulation(
                 turns=t, 
                 planets=s, 
                 game_config=config_data, 
                 universe_name=universe, 
                 run_id=active_run_id, 
                 delay_seconds=args.delay, 
                 manual_mode=args.manual
             )
        else:
             # Default fallback
             simulate_campaign.run_campaign_simulation(
                 turns=30, 
                 planets=15, 
                 universe_name=universe, 
                 run_id=active_run_id, 
                 delay_seconds=args.delay, 
                 manual_mode=args.manual
             )
        
        # Dashboard Cleanup / Keep-Alive logic
        if args.dashboard:
            print("[CLI] Simulation complete.")
            print("[CLI] Dashboard is running in background. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[CLI] Shutting down...")
                if 'dash_process' in locals():
                    dash_process.terminate()
