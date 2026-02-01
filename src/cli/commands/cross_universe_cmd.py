import argparse
from src.cli.base_command import BaseCommand

class CrossUniverseDuelCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "cross-universe-duel"

    @property
    def help(self) -> str:
        return "Pit units from different universes against each other"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--unit1", required=True, help="Unit 1 (format: universe:faction:unit_name)")
        parser.add_argument("--unit2", required=True, help="Unit 2 (format: universe:faction:unit_name)")
        parser.add_argument("--battle-universe", help="Combat resolution universe (default: unit1's universe)")

    def execute(self, args: argparse.Namespace) -> None:
        from src.combat import combat_simulator
        combat_simulator.run_cross_universe_duel(
            args.unit1, args.unit2, 
            battle_universe=getattr(args, 'battle_universe', None)
        )


class CrossUniverseBattleCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "cross-universe-battle"

    @property
    def help(self) -> str:
        return "Run configured cross-universe battle"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--config", required=True, help="Path to battle config JSON")
        parser.add_argument("--profile-memory", action="store_true")

    def execute(self, args: argparse.Namespace) -> None:
        from src.combat import combat_simulator
        combat_simulator.run_cross_universe_battle(
            args.config,
            profile_memory=getattr(args, 'profile_memory', False)
        )
