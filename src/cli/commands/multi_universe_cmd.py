import argparse
import sys
import json
import traceback
from src.cli.base_command import BaseCommand

class MultiUniverseCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "multi-universe"

    @property
    def help(self) -> str:
        return "Run multiple universes in parallel on different processors"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--config", type=str, required=True,
            help="Path to multi-universe configuration JSON")
        parser.add_argument("--universes", help="Comma-separated list of universe names to run (overrides config enabled status)")
        parser.add_argument("--output-dir", type=str,
            help="Custom output directory for all universe reports")

    def execute(self, args: argparse.Namespace) -> None:
        from src.core.game_config import MultiUniverseConfig
        from src.engine.multi_universe_runner import MultiUniverseRunner
        
        try:
            # Load and parse config
            with open(args.config, 'r') as f:
                config_data = json.load(f)
            
            multi_config = MultiUniverseConfig.from_dict(config_data)
            
            if multi_config.mode != "multi":
                print("Error: Configuration file must have mode='multi'")
                sys.exit(1)
            
            # Apply Filter if provided
            if args.universes:
                selected = [u.strip() for u in args.universes.split(',')]
                # Enable selected, disable others
                found_any = False
                for uni_conf in multi_config.universes:
                    if uni_conf.name in selected:
                        uni_conf.enabled = True
                        found_any = True
                    else:
                        uni_conf.enabled = False
                
                if not found_any:
                    print(f"Error: None of the requested universes {selected} found in config.")
                    sys.exit(1)
            
            # Convert to runner format
            runner_configs = multi_config.to_runner_configs()
            
            if not runner_configs:
                print("Error: No enabled universes found in configuration")
                sys.exit(1)
            
            print(f"Starting multi-universe simulation with {len(runner_configs)} universes:")
            for cfg in runner_configs:
                affinity = cfg.get('processor_affinity', 'Auto')
                print(f"  - {cfg['universe_name']}: {cfg['num_runs']} runs on cores {affinity}")
            
            # Prepare Multi Settings
            multi_settings = {
                "sync_turns": multi_config.sync_turns,
                "cross_universe_events": multi_config.cross_universe_events,
                "aggregate_reports": multi_config.aggregate_reports
            }

            # Create and run
            runner = MultiUniverseRunner(runner_configs, multi_settings=multi_settings)
            runner.run_parallel(output_dir=args.output_dir)
            runner.aggregate_results()
            
            print("\nMulti-universe simulation complete!")
            
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {args.config}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration file: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: Configuration validation failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error running multi-universe simulation: {e}")
            traceback.print_exc()
            sys.exit(1)
