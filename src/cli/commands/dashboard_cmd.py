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
    def help(self) -> str:
        return "Launch live dashboard"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--port", type=int, default=5000, help="Port to bind to (default: 5000)")
        parser.add_argument("--host", default="localhost", help="Host interface (default: localhost)")
        parser.add_argument("--universe", type=str, help="Universe context (optional)")
        parser.add_argument("--run-id", type=str, help="Run ID to attach to (optional)")
        parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    def execute(self, args: argparse.Namespace) -> None:
        universe = args.universe or "void_reckoning"
        run_id = args.run_id # Optional
        
        print(f"Starting Live Dashboard V2 on http://{args.host}:{args.port}")
        
        cmd = [
            sys.executable, 
            "-m", "src.reporting.dashboard_v2.run_server",
            "--universe", universe,
            "--host", args.host,
            "--port", str(args.port)
        ]
        
        if run_id:
            cmd.extend(["--run-id", run_id])
            
        dash_process = subprocess.Popen(cmd)
        
        if not args.no_browser:
            time.sleep(2.0)
            webbrowser.open(f"http://{args.host}:{args.port}")
            
        try:
            dash_process.wait()
        except KeyboardInterrupt:
            print("Stopping dashboard...")
            dash_process.terminate()
