import argparse
import sys
import json
from src.cli.base_command import BaseCommand

class ConfigCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "validate-config"

    @property
    def help(self) -> str:
        return "Validate simulation configuration"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--config", type=str, required=True, help="Path to config file")

    def execute(self, args: argparse.Namespace) -> None:
        from src.core.game_config import MultiUniverseConfig, validate_multi_universe_config
        
        try:
            with open(args.config, 'r') as f:
                data = json.load(f)
            
            # Autodetect mode
            config = MultiUniverseConfig.from_dict(data)
            
            # Run Validation
            is_valid, errors = validate_multi_universe_config(config)
            
            print(f"Validating configuration from {args.config}...")
            print(f"Mode: {config.mode}")
            
            if config.mode == "multi":
                enabled_unis = [u for u in config.universes if u.enabled]
                print(f"Enabled Universes: {len(enabled_unis)}")
                for u in enabled_unis:
                    affinity_str = str(u.processor_affinity) if u.processor_affinity else "Auto"
                    print(f"  - {u.name}: {affinity_str} (Runs: {u.num_runs})")
            
            if is_valid:
                print("\nSUCCESS: Configuration is valid.")
            else:
                print("\nFAILURE: Configuration Errors:")
                for err in errors:
                    print(f"  - {err}")
                sys.exit(1)
                
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON syntax in {args.config}")
            sys.exit(1)
        except Exception as e:
            print(f"Error validating config: {e}")
            sys.exit(1)
