import argparse
import os
import sys

# Core Infrastructure
from src.cli.registry import CommandRegistry
from src.reporting.alert_manager import AlertManager

# Commands
from src.cli.commands.campaign_cmd import CampaignCommand
from src.cli.commands.simulate_cmd import SimulateCommand
from src.cli.commands.validate_cmd import ValidateCommand
from src.cli.commands.config_cmd import ConfigCommand
from src.cli.commands.multi_universe_cmd import MultiUniverseCommand
from src.cli.commands.dashboard_cmd import DashboardCommand
from src.cli.commands.portal_cmd import ValidatePortalsCommand, ListPortalsCommand, TestPortalCommand
from src.cli.commands.analyze_cmd import AnalyzeCommand
from src.cli.commands.query_cmd import QueryCommand
from src.cli.commands.cross_universe_cmd import CrossUniverseDuelCommand, CrossUniverseBattleCommand
from src.cli.commands.generate_cmd import GenerateCommand
from src.cli.commands.export_cmd import ExportCommand

def register_all_commands():
    """Register all available commands with the registry."""
    CommandRegistry.register(CampaignCommand)
    CommandRegistry.register(SimulateCommand)
    CommandRegistry.register(ValidateCommand)
    CommandRegistry.register(ConfigCommand)
    CommandRegistry.register(MultiUniverseCommand)
    CommandRegistry.register(DashboardCommand)
    CommandRegistry.register(ValidatePortalsCommand)
    CommandRegistry.register(ListPortalsCommand)
    CommandRegistry.register(TestPortalCommand)
    CommandRegistry.register(AnalyzeCommand)
    CommandRegistry.register(QueryCommand)
    CommandRegistry.register(CrossUniverseDuelCommand)
    CommandRegistry.register(CrossUniverseBattleCommand)
    CommandRegistry.register(GenerateCommand)
    CommandRegistry.register(ExportCommand)

def main():
    # Initialize Alert System
    try:
        AlertManager(config_path=os.environ.get("ALERTS_CONFIG", "config/alert_rules.yaml"))
    except Exception as e:
        # Non-fatal warning
        print(f"Warning: Alert System initialization failed: {e}")

    parser = argparse.ArgumentParser(description="Multi-Universe Campaign Simulator CLI")
    
    # Global Epilog
    parser.epilog = """
Examples:
  # Single universe campaign
  python run.py campaign --universe void_reckoning --quick
  
  # Multi-universe parallel execution
  python run.py multi-universe --config simulation_config_multi_universe.json
  
  # Validate specific universe
  python run.py validate --universe void_reckoning --rebuild-registries
"""
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Register and Setup Subparsers
    register_all_commands()
    CommandRegistry.register_commands(subparsers)

    args = parser.parse_args()
    
    # Execute
    CommandRegistry.execute(args)

if __name__ == "__main__":
    main()
