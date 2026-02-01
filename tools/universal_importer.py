import sys
import os
import argparse
import json
import importlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.format_detector import FormatDetector
from src.utils.parser_registry import ParserRegistry
try:
    from src.utils.registry_builder import build_all_registries
except ImportError:
    # Fallback or local dev setup might vary
    pass

from src.utils.import_progress_tracker import ImportProgressTracker
from src.utils.import_validator import ImportValidator
from src.utils.import_reporter import ImportReporter
try:
    from src.core.physics_calibrator import PhysicsCalibrator
    from src.utils.unit_parser import load_all_units
except ImportError:
    PhysicsCalibrator = None
    load_units_from_universe = None

from src.utils.dna_injector import extract_parser_data

try:
    from src.core.balance import BalanceAnalyzer
except ImportError:
    BalanceAnalyzer = None


class UniversalImporter:
    def __init__(self, game_dir: str, universe_name: str, engine: str = None, dry_run: bool = False, skip_registries: bool = False, faction_filter: str = None, extract_ai: bool = False, skip_dna_generation: bool = False, skip_physics_calibration: bool = False, continue_on_error: bool = False, quiet: bool = False, force_convert: bool = False):
        self.game_dir = game_dir
        self.universe_name = universe_name
        self.engine = engine
        self.dry_run = dry_run
        self.skip_registries = skip_registries
        self.faction_filter = faction_filter.split(',') if faction_filter else None
        self.extract_ai = extract_ai
        self.skip_dna_generation = skip_dna_generation
        self.skip_physics_calibration = skip_physics_calibration
        self.continue_on_error = continue_on_error
        self.quiet = quiet
        self.force_convert = force_convert
        
        self.detector = FormatDetector()
        self.registry = ParserRegistry.get_instance()
        
        # New Components
        self.tracker = ImportProgressTracker(quiet=self.quiet) # Controlled by CLI later
        
        self.universe_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "universes") # Heuristic
        # Usually from config, but let's derive or use config
        from src.core.config import UNIVERSE_ROOT
        self.universe_root = UNIVERSE_ROOT
        
        self.validator = ImportValidator(universe_name, self.universe_root)
        self.reporter = ImportReporter(universe_name, os.path.join(self.universe_root, universe_name))
        
        self.dry_run_actions = []
        self.errors = []
        self.entity_counts = {"units": 0, "buildings": 0, "technology": 0, "factions": 0}


    def run(self):
        print("\n=== Universal Game Importer ===")
        print(f"Target Universe: {self.universe_name}")
        print(f"Game Directory: {self.game_dir}")
        
        self.tracker.start_stage("Engine Detection")
        
        # Stage 1: Detection
        detected_engine = self.engine
        if not detected_engine:
            detected_engine = self.detector.detect_game_engine(self.game_dir)
            
        if not detected_engine:
            self.tracker.complete_stage("Failed to detect engine")
            print("[!] Failed to detect game engine. Please specify --engine.")
            return

        self.reporter.set_engine(detected_engine)
        self.tracker.complete_stage(f"Detected {detected_engine}")
        self.tracker.update(1, f"Data Root Scan")

        metadata = self.registry.get_metadata(detected_engine)
        if not metadata:
             print(f"[!] No registry metadata found for engine: {detected_engine}")
             return

        # Determine Data Root
        paths = self.detector.get_engine_data_paths(self.game_dir, detected_engine)
        data_root = self.game_dir
        if detected_engine == "paradox" and "common" in paths:
            data_root = paths["common"]
        elif detected_engine == "petroglyph" and "xml_root" in paths:
            data_root = paths["xml_root"]
            
        # Stage 2.5: Binary Conversion (if needed)
        converted_data_root = None
        if detected_engine == "ironclad" or self.force_convert:
            self.tracker.start_stage("Binary Conversion")
            converted_data_root = self._run_binary_conversion(detected_engine, self.game_dir)
            if converted_data_root:
                data_root = converted_data_root  # Update data_root for parser
                self.tracker.complete_stage(f"Converted to {converted_data_root}")
            else:
                self.tracker.complete_stage("Conversion skipped or failed")
            
        # Stage 2: Parser Selection
        self.tracker.start_stage("Parser Selection")
        importer_instance = self._load_importer(metadata, data_root)
        self.tracker.complete_stage(f"Selected {type(importer_instance).__name__ if importer_instance else 'None'}")
        
        # Stage 3: Data Extraction
        if importer_instance:
             self.tracker.start_stage("Data Extraction")
             if hasattr(importer_instance, 'set_progress_tracker'):
                 importer_instance.set_progress_tracker(self.tracker)
             
             start_time = time.time()
             if hasattr(importer_instance, 'run'):
                 try:
                     importer_instance.run()
                 except Exception as e:
                     self.errors.append({"stage": "extraction", "error": str(e)})
                     if not self.continue_on_error: raise e
             
             self.reporter.record_stage_time("data_extraction", time.time() - start_time)
             self.tracker.complete_stage("Extraction complete")
        
        
        # Stage 4: DNA Generation (Decommissioned)
        pass
            
        # Stage 4.5: AI Extraction
        if self.extract_ai:
             self._extract_ai_personalities()

        # Stage 5: Physics Calibration
        if not self.skip_physics_calibration and PhysicsCalibrator:
            self._calibrate_physics()

        # Stage 6: Registries
        if not self.skip_registries:
            self._build_registries()
            
        # Stage 7: Validation
        self._run_validation()
        
        # Stage 8: Reporting
        self._generate_final_report()

    def _load_importer(self, metadata, data_root):
        importer_module_name = metadata.get("importer_module")
        importer_class_name = metadata.get("importer_class")
        
        if importer_module_name and importer_class_name:
            try:
                module = importlib.import_module(importer_module_name)
                importer_cls = getattr(module, importer_class_name)
                
                try:
                     importer_instance = importer_cls(data_root, universe_name=self.universe_name, dry_run=self.dry_run)
                except TypeError:
                     # Set Importer flags
                     if hasattr(importer_instance, 'set_continue_on_error'):
                         importer_instance.set_continue_on_error(self.continue_on_error)
                     
                     # Set Importer flags
                     if hasattr(importer_instance, 'set_continue_on_error'):
                         importer_instance.set_continue_on_error(self.continue_on_error)
                     
                     # Set Importer flags
                     if hasattr(importer_instance, 'set_continue_on_error'):
                         importer_instance.set_continue_on_error(self.continue_on_error)
                     
                     importer_instance = importer_cls(data_root, universe_name=self.universe_name)
                     if hasattr(importer_instance, 'dry_run'):
                         importer_instance.dry_run = self.dry_run
                return importer_instance
            except Exception as e:
                print(f"Failed to load importer: {e}")
        return None

    def _run_binary_conversion(self, engine: str, game_dir: str) -> Optional[str]:
        """Execute binary conversion for SOASE before parsing."""
        if engine != "ironclad":
             return None
             
        config = self.detector.get_soase_conversion_config(game_dir)
        if not config or not config.get("requires_conversion"):
            return None
            
        if not config.get("exe_path"):
            print("[!] ConvertData.exe not found. Manual conversion required.")
            
            # Create output directory for script
            output_dir = os.path.join(self.universe_root, self.universe_name, "raw_txt")
            if not self.dry_run:
                os.makedirs(output_dir, exist_ok=True)
                
                # Generate Batch/Shell Script
                import platform
                is_windows = platform.system() == "Windows"
                script_name = "convert_all.bat" if is_windows else "convert_all.sh"
                script_path = os.path.join(output_dir, script_name)
                
                with open(script_path, "w") as f:
                    if is_windows:
                        f.write("@echo off\n")
                        f.write("set CONVERT_EXE=C:\\Path\\To\\ConvertData_Rebellion.exe\n")
                        for in_dir in config.get("input_dirs", []):
                            f.write(f'for %%f in ("{in_dir}\\*.entity") do (\n')
                            f.write(f'    echo Converting %%f...\n')
                            f.write(f'    "%CONVERT_EXE%" entity "%%f" "{output_dir}\\%%~nxf.txt" txt\n')
                            f.write(')\n')
                        f.write("pause\n")
                    else:
                        f.write("#!/bin/bash\n")
                        f.write("CONVERT_EXE=\"/path/to/ConvertData_Rebellion\"\n")
                        for in_dir in config.get("input_dirs", []):
                            f.write(f'for f in "{in_dir}"/*.entity; do\n')
                            f.write(f'    echo \"Converting $f...\"\n')
                            f.write(f'    \"$CONVERT_EXE\" entity \"$f\" \"{output_dir}/$(basename \"$f\").txt\" txt\n')
                            f.write('done\n')
                
                print(f"[i] Manual conversion script generated at: {script_path}")
                print("[!] Please update CONVERT_EXE path in the script and run it, then re-import.")
                
            return None
            
        # Create output directory
        output_dir = os.path.join(self.universe_root, self.universe_name, "raw_txt")
        if not self.dry_run:
            os.makedirs(output_dir, exist_ok=True)
            
        try:
            from tools.soase_converter import SOASEConverter
            converter = SOASEConverter(
                exe_path=config["exe_path"],
                input_dir=game_dir,
                output_dir=output_dir,
                file_types=["entity", "mesh", "brush", "particle"],
                dry_run=self.dry_run,
                continue_on_error=self.continue_on_error,
                quiet=self.quiet
            )
            result = converter.run()
            if result.get("success"):
                return output_dir
        except Exception as e:
            print(f"[!] Binary conversion failed: {e}")
            if not self.continue_on_error: raise e
            
        return None

    def _generate_dna(self):
        """DNA logic removed (Phase 6 Alignment)."""
        pass

    def _extract_ai_personalities(self):
         self.tracker.start_stage("AI Extraction")
         try:
             from src.utils.ai_personality_orchestrator import AIPersonalityOrchestrator
             orchestrator = AIPersonalityOrchestrator()
             orchestrator.extract_and_generate(self.game_dir, self.universe_name, self.engine)
             self.tracker.complete_stage("AI extracted")
         except Exception as e:
             self.errors.append({"stage": "ai", "error": str(e)})
             self.tracker.complete_stage("AI extraction failed")
             
    def _calibrate_physics(self):
        self.tracker.start_stage("Physics Calibration")
        start = time.time()
        
        if PhysicsCalibrator:
            try:
                if self.dry_run:
                    self.tracker.update(1, "[DRY RUN] Calibrating Physics...")
                    profile_data = {"archetype": "DryRun", "mape": 0.0, "status": "SKIPPED"}
                else:
                    self.tracker.update(0, "Loading units for calibration...")
                    # 1. Load Units
                    faction_units = load_all_units(self.universe_name)
                    units = []
                    for f_list in faction_units.values():
                        units.extend(f_list)
                        
                    self.tracker.update(1, f"Calibrating with {len(units)} units...")
                    
                    if not units:
                        if not self.quiet: print("  [!] No units found for physics calibration. Skipping.")
                        self.tracker.complete_stage("Calibration skipped (no units)")
                        return

                    # 2. Calibrate
                    profile, metadata = PhysicsCalibrator.calibrate(units, self.universe_name)
                    
                    # 3. Validate
                    validation = PhysicsCalibrator.validate_calibration(profile, units[:100] if len(units) > 100 else units)
                    
                    # 4. Save Profile
                    profile_dict = profile.to_dict()
                    profile_path = os.path.join(self.universe_root, self.universe_name, "universe_physics.json")
                    with open(profile_path, 'w', encoding='utf-8') as f:
                        json.dump(profile_dict, f, indent=2)
                        
                    profile_data = {
                        "archetype": metadata.get("archetype", {}),
                        "mape": validation.mape,
                        "status": validation.status_msg,
                        "profile": profile_dict
                    }
                    
                    if not self.quiet:
                        print(f"\n[+] Physics Profile Generated: {profile_path}")
                        print(f"    Archetype: {profile.description}")
                        print(f"    MAPE: {validation.mape*100:.1f}% ({validation.status_msg})")

            except Exception as e:
                 if not self.continue_on_error: raise e
                 profile_data = {"error": str(e), "status": "FAILED"}
        else:
             profile_data = {"status": "MISSING_MODULE"}

        self.reporter.set_physics_profile(profile_data)
        
        self.reporter.record_stage_time("physics_calibration", time.time() - start)
        self.tracker.complete_stage("Physics Profile Generated")

    def _build_registries(self):
        self.tracker.start_stage("Registry Building")
        start = time.time()
        
        if self.dry_run:
            self.tracker.complete_stage("[DRY RUN] Skipped Registry Building")
            return

        try:
            build_all_registries(self.universe_name)
            self.tracker.complete_stage("Registries Built")
        except Exception as e:
            self.errors.append({"stage": "registry", "error": str(e)})
            if not self.continue_on_error: raise e
            self.tracker.complete_stage("Registry Build Failed")
        self.reporter.record_stage_time("registry_building", time.time() - start)

    def _run_validation(self):
        self.tracker.start_stage("Validation")
        start = time.time()
        
        # File Structure
        file_issues = self.validator.validate_file_structure()
        self.reporter.add_validation_issues(file_issues)
        
        # Registries
        registries = {}
        if not self.skip_registries and not self.dry_run:
             for reg_type in ["factions", "technology", "buildings"]:
                issues = self.validator.validate_registry(reg_type, self.universe_name)
                self.reporter.add_validation_issues(issues)
                
                # Load registry for cross-ref
                reg_path = os.path.join(self.universe_root, self.universe_name, "factions" if reg_type != "campaigns" else "", f"{reg_type}_registry.json")
                if reg_type == "technology": reg_path = os.path.join(self.universe_root, self.universe_name, "technology", "technology_registry.json")
                if reg_type == "buildings": reg_path = os.path.join(self.universe_root, self.universe_name, "infrastructure", "building_registry.json")
                
                if os.path.exists(reg_path):
                    with open(reg_path, 'r', encoding='utf-8') as f:
                        registries[reg_type] = json.load(f)

        # Deep Entity Scan & Cross-Reference
        universe_path = os.path.join(self.universe_root, self.universe_name)
        # Scan Units
        meta_counts = {"dna_checked": 0, "cross_refs": 0}
        
        for root, dirs, files in os.walk(os.path.join(universe_path, "factions")):
            for f in files:
                if f.endswith(".md"):
                    fpath = os.path.join(root, f)
                    basename = os.path.basename(fpath)
                    
                    # DNA Validation
                    dna = extract_dna_from_markdown(fpath)
                    if dna:
                        violation = self.validator.validate_dna_budget(dna, basename)
                        if violation: self.reporter.add_validation_issues([violation])
                        meta_counts["dna_checked"] += 1
                        
                    # Cross-Ref Validation (Units typically have weapons/abilities)
                    parser_data = extract_parser_data(fpath)
                    if parser_data:
                        # Weapons
                        if "authentic_weapons" in parser_data: # StarWars format
                            for w in parser_data["authentic_weapons"]:
                                # TODO: Check against weapon registry if available (usually in factions/weapon_registry.json)
                                pass
        
        # Balance Analysis
        if BalanceAnalyzer and not self.dry_run:
            try:
                analyzer = BalanceAnalyzer(self.universe_name)
                # analyzer.check_factions() # Hypothetical method based on request
                # For now, just logging presence
                pass
            except Exception as e:
                pass # soft fail

        self.reporter.record_stage_time("validation", time.time() - start)
        self.tracker.complete_stage(f"Validation complete ({len(file_issues)} file issues)")

    def _generate_final_report(self):
        self.tracker.start_stage("Reporting")
        
        if self.dry_run:
             self.tracker.complete_stage("[DRY RUN] Reports Not Written")
             return

        paths = self.reporter.generate_reports()
        for p in paths:
            print(f"  [+] Report saved: {p}")
        self.tracker.complete_stage("Reports Generated")


def scan_library(steam_lib):
    if not steam_lib or not os.path.exists(steam_lib):
        print(f"Error: Steam library path not found: {steam_lib}")
        return

    print(f"Scanning Steam Library at {steam_lib}...")
    results = FormatDetector.scan_steam_library(steam_lib)
    if not results:
        print("  No supported games found.")
        return
        
    print(f"  Found {len(results)} supported games:")
    for game, info in results.items():
        print(f"  - {game} (Engine: {info['engine']})")
        print(f"    Path: {info['path']}")

def main():
    parser = argparse.ArgumentParser(description="Universal Game Importer")
    parser.add_argument("--game-dir", help="Path to game installation")
    parser.add_argument("--steam-library", help="Path to Steam library root (to scan)")
    parser.add_argument("--universe-name", help="Target universe name")
    parser.add_argument("--engine", choices=["unity", "taleworlds", "paradox", "petroglyph", "ironclad"])
    parser.add_argument("--force-convert", action="store_true", help="Force binary conversion for games like SOASE")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--faction-filter", help="Comma-separated faction list")
    parser.add_argument("--extract-campaigns", action="store_true", help="Extract structure/missions")
    parser.add_argument("--extract-ai", action="store_true", help="Extract AI personalities and diplomacy")
    parser.add_argument("--skip-registries", action="store_true")
    
    # New Arguments
    parser.add_argument("--skip-dna-generation", action="store_true")
    parser.add_argument("--skip-physics-calibration", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue import even if errors occur")
    parser.add_argument("--resume-from", help="Resume from checkpoint file")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    
    parser.add_argument("--list-importable", action="store_true", help="List importable games from detected/default steam libs")
    
    args = parser.parse_args()
    
    if args.list_importable:
        if args.steam_library:
             scan_library(args.steam_library)
        else:
             print("Please provide --steam-library to scan.")
        return
        
    if not args.game_dir:
        parser.print_help()
        print("\nError: --game-dir is required for import.")
        return
        
    if not args.universe_name:
        print("Error: --universe-name is required for import.")
        return

    importer = UniversalImporter(
        args.game_dir, 
        args.universe_name, 
        engine=args.engine,
        dry_run=args.dry_run,
        skip_registries=args.skip_registries,
        faction_filter=args.faction_filter,
        extract_ai=args.extract_ai,
        skip_dna_generation=args.skip_dna_generation,
        skip_physics_calibration=args.skip_physics_calibration,
        continue_on_error=args.continue_on_error,
        quiet=args.quiet,
        force_convert=args.force_convert
    )
    importer.run()
    
    # Stage 7: Campaign Extraction (Phase 60)
    if args.extract_campaigns and not args.dry_run:
        print("\n[7/7] :: Extracting Campaign Structure...")
        try:
            from src.utils.campaign_extractor import CampaignExtractor
            # Re-detect or reuse engine
            extractor = CampaignExtractor(args.game_dir, args.engine)
            campaign_data = extractor.extract_campaign_structure()
            
            if campaign_data:
                from src.core.config import UNIVERSE_ROOT
                camp_dir = os.path.join(UNIVERSE_ROOT, args.universe_name, "campaigns")
                if not os.path.exists(camp_dir): os.makedirs(camp_dir)
                
                out_path = os.path.join(camp_dir, "campaign_config.json")
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(campaign_data, f, indent=2)
                print(f"  [+] Campaign configuration saved to {out_path}")
            else:
                print("  [i] No campaign structure extracted (or not supported for this engine).")
                
        except Exception as e:
            print(f"  [!] Campaign extraction failed: {e}")

if __name__ == "__main__":
    main()
