import argparse
from typing import Dict, Type
from src.cli.base_command import BaseCommand

class CommandRegistry:
    """
    Registry for CLI commands. Handles registration and parser setup.
    """
    _commands: Dict[str, BaseCommand] = {}

    @classmethod
    def register(cls, command_class: Type[BaseCommand]) -> None:
        """Register a command class."""
        cmd_instance = command_class()
        cls._commands[cmd_instance.name] = cmd_instance

    @classmethod
    def register_commands(cls, subparsers: argparse._SubParsersAction) -> None:
        """Register all commands with argparse subparsers."""
        for name, cmd in cls._commands.items():
            parser = subparsers.add_parser(name, help=cmd.help)
            cmd.register_arguments(parser)

    @classmethod
    def execute(cls, args: argparse.Namespace) -> None:
        """Execute the requested command."""
        if not hasattr(args, 'command') or not args.command:
            print("Error: No command specified. Use --help for usage.")
            return

        cmd = cls._commands.get(args.command)
        if cmd:
            cmd.execute(args)
        else:
            print(f"Error: Unknown command '{args.command}'")
