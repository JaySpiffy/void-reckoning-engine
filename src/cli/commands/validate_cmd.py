import argparse
from src.cli.base_command import BaseCommand

class ValidateCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "validate"

    @property
    def help(self) -> str:
        return "Validate data and registries"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--universe", type=str, default="void_reckoning",
                            help="Universe to validate")
        parser.add_argument("--game-dir", type=str, help="Game directory for readiness checks")
        parser.add_argument("--rebuild-registries", action="store_true", help="Force rebuild of registries")
        parser.add_argument("--check-atomic-budget", action="store_true", help="Audit all units for atomic budget violations")
        parser.add_argument("-v", "--verbose", action="store_true", help="Detailed output")

    def execute(self, args: argparse.Namespace) -> None:
        from src.core.config import set_active_universe
        from src.utils import validator as validate_data_layer
        from src.utils import registry_builder as build_registries
        
        universe = args.universe
        set_active_universe(universe)
        
        if args.rebuild_registries:
            print(f"Rebuilding registries for {universe}...")
            build_registries.build_all_registries(universe_name=universe)
        
        print("Validating data layer...")
        results = validate_data_layer.validate_all(output_report=True)
        errors = results["errors"]
        
        print("\n=== Validation Report ===")
        if not errors:
            print("SUCCESS: Data Layer Integrity Verified.")
        else:
            print(f"FAILED: Found {len(errors)} errors.")
        
        # Format Detection Stats
        try:
            from universes.base.universe_loader import UniverseLoader
            from src.core.config import UNIVERSE_ROOT
            loader = UniverseLoader(UNIVERSE_ROOT)
            config = loader.load_universe(universe)
            formats = loader.detect_unit_formats(config)
            
            print("\n=== Format Detection ===")
            for faction, f_list in formats.items():
                fmt_str = ", ".join(f_list)
                print(f"{faction}: {fmt_str}")
            
            if any("xml" in f for f in formats.values()):
                print(f"{universe.title()} universe uses hybrid XML/Markdown sources.")
            else:
                print(f"{universe.title()} universe uses standard Markdown sources.")
        except Exception as e:
            if args.verbose: print(f"DEBUG: Format detection failed: {e}")

        if errors:
            if args.verbose:
                for err in errors:
                    print(err)
            else:
                for err in errors[:25]:
                    print(err)
                if len(errors) > 25:
                    print(f"... and {len(errors)-25} more.")

        # Cross-Universe Validation
        if args.universe == "all" or args.verbose:
            from src.utils.cross_universe_validator import CrossUniverseValidator
            validator = CrossUniverseValidator()
            is_valid, messages = validator.validate_translation_table()
            
            print("\n=== Cross-Universe Translation Validation ===")
            if is_valid:
                print("SUCCESS: Translation table is valid.")
            else:
                print("WARNINGS found:")
                
            for msg in messages[:20]:
                print(f"  - {msg}")
            if len(messages) > 20:
                print(f"  ... and {len(messages)-20} more.")

        if args.check_atomic_budget:
            from src.utils.atomic_budget_auditor import audit_all_units
            print("\n=== Atomic Budget Audit ===")
            results = audit_all_units(universe=universe, verbose=args.verbose)
            
            if results["success"]:
                print(f"SUCCESS: All {results['total_units']} units have valid atomic budgets.")
            else:
                print(f"VIOLATIONS: {results['violation_count']} units have budget issues.")
                print(f"Report saved to: {results['report_path']}")
