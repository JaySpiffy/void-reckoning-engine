import argparse
from src.cli.base_command import BaseCommand

class SimulateCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "simulate"

    @property
    def help(self) -> str:
        return "Run tactical combat simulations in any universe"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--universe", type=str, default="void_reckoning",
                            help="Universe context (default: void_reckoning)")
        parser.add_argument("--mode", choices=["duel", "royale", "fleet", "campaign"], required=True, help="Combat mode")
        parser.add_argument("--units", nargs="+", help="Units for duel mode")
        parser.add_argument("--faction1", help="Faction 1 for fleet battle")
        parser.add_argument("--faction2", help="Faction 2 for fleet battle")
        parser.add_argument("--size", type=int, help="Fleet size")
        parser.add_argument("--cross-universe", action="store_true", 
            help="Enable cross-universe combat (translate units to common context)")
        parser.add_argument("--multi-universe", action="store_true",
            help="Alias for --cross-universe")
        parser.add_argument("--battle-universe", type=str,
            help="Universe context for cross-universe battles (default: first faction's universe)")
        parser.add_argument("--profile-memory", action="store_true",
            help="Enable memory profiling for cross-universe operations")
        parser.add_argument("--dashboard", action="store_true", help="Launch live dashboard for this simulation")

    def execute(self, args: argparse.Namespace) -> None:
        from src.core.config import set_active_universe
        from src.combat import combat_simulator
        from src.engine import simulate_campaign
        
        universe = args.universe
        set_active_universe(universe)
        
        if args.mode == "duel":
            if not args.units or len(args.units) < 2:
                print("Error: --units requires at least 2 units for duel mode")
                return
            combat_simulator.run_duel(args.units[0], args.units[1])
            
        elif args.mode == "royale":
            combat_simulator.run_grand_royale()
            
        elif args.mode == "fleet":
            if not args.faction1 or not args.faction2:
                print("Error: --faction1 and --faction2 required for fleet mode")
                return
            combat_simulator.run_fleet_battle(
                args.faction1, args.faction2, args.size,
                cross_universe=args.cross_universe or args.multi_universe,
                profile_memory=getattr(args, 'profile_memory', False)
            )
            
        elif args.mode == "campaign":
             simulate_campaign.run_campaign_simulation(turns=30, planets=15, universe_name=universe)
