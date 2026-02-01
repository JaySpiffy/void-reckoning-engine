import argparse
from src.cli.base_command import BaseCommand

class GenerateCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "generate"

    @property
    def help(self) -> str:
        return "Generate content"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--type", choices=["roster", "cards"], required=True, help="Generation type")

    def execute(self, args: argparse.Namespace) -> None:
         print(f"Generating {args.type} not yet implemented.")
