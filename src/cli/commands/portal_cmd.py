import argparse
from pathlib import Path
from src.cli.base_command import BaseCommand

class ValidatePortalsCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "validate-portals"

    @property
    def help(self) -> str:
        return "Validate portal configurations"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--universe", type=str, help="Universe to validate (optional)")

    def execute(self, args: argparse.Namespace) -> None:
        from src.utils.portal_validator import PortalValidator
        from src.core.config import UNIVERSE_ROOT, get_active_universe
        
        target_uni = args.universe if args.universe else get_active_universe()
        if not target_uni:
            print("Error: No universe specified or active.")
            return

        print(f"Validating portal configuration for {target_uni}...")
        config_path = Path(UNIVERSE_ROOT) / target_uni / "portal_config.json"
        
        try:
             res = PortalValidator.validate_portal_config(config_path)
             if res["valid"]:
                 print(f"SUCCESS: Portal configuration for {target_uni} is valid.")
                 p_count = len(res["data"]["portals"])
                 print(f"Found {p_count} portal(s).")
             else:
                 print(f"FAILURE: {res['error']}")
        except Exception as e:
             print(f"Error: {e}")


class ListPortalsCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "list-portals"

    @property
    def help(self) -> str:
        return "List all configured portals across universes"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        pass

    def execute(self, args: argparse.Namespace) -> None:
        from src.utils.portal_validator import PortalValidator
        from src.core.config import UNIVERSE_ROOT
        
        try:
            report = PortalValidator.generate_portal_report(Path(UNIVERSE_ROOT))
            print("\n" + report)
        except Exception as e:
            print(f"Error listing portals: {e}")


class TestPortalCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "test-portal"

    @property
    def help(self) -> str:
        return "Test portal connectivity between universes"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--from-universe", required=True, help="Origin universe")
        parser.add_argument("--to-universe", required=True, help="Destination universe")

    def execute(self, args: argparse.Namespace) -> None:
        from src.utils.portal_validator import PortalValidator
        from src.core.config import UNIVERSE_ROOT
        
        print(f"Testing portal connectivity: {args.from_universe} <-> {args.to_universe}")
        try:
            errors = PortalValidator.validate_bidirectional_portals(
                args.from_universe, args.to_universe, Path(UNIVERSE_ROOT)
            )
            
            if not errors:
                print(f"SUCCESS: Bidirectional connectivity verified between {args.from_universe} and {args.to_universe}.")
            else:
                print("FAILURE: Connectivity issues found:")
                for err in errors:
                    print(f"  - {err}")
        except Exception as e:
            print(f"Error testing portals: {e}")
